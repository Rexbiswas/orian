import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from .models import (
    ActivityEvent, ProductivityCategory, SecurityCategory,
    EnforcementAction, ProtectionRiskLevel, ProductivityPolicy,
    SecurityPolicy, RuleType
)
from .database import protection_db
from .whitelist import activity_whitelist
from .focus_manager import focus_manager
from .risk_engine import protection_risk_engine

logger = logging.getLogger("orian.protection.policy_engine")

class EvaluationResult:
    def __init__(
        self,
        allowed: bool,
        action: EnforcementAction,
        risk_level: ProtectionRiskLevel,
        policy: Optional[ProductivityPolicy] = None,
        security_policy: Optional[SecurityPolicy] = None,
        reason: str = "",
        category: str = "GENERAL",
        grace_period_seconds: int = 0,
        matched_rule: Optional[str] = None
    ):
        self.allowed = allowed
        self.action = action
        self.risk_level = risk_level
        self.policy = policy
        self.security_policy = security_policy
        self.reason = reason
        self.category = category
        self.grace_period_seconds = grace_period_seconds
        self.matched_rule = matched_rule

    def to_dict(self) -> Dict[str, Any]:
        return {
            "allowed": self.allowed,
            "action": self.action.value,
            "risk_level": self.risk_level.value,
            "policy_id": self.policy.policy_id if self.policy else (self.security_policy.policy_id if self.security_policy else None),
            "category": self.category,
            "reason": self.reason,
            "grace_period_seconds": self.grace_period_seconds,
            "matched_rule": self.matched_rule
        }

class OrianPolicyEngine:
    """Deterministic Enterprise Policy Engine assessing activities against Whitelist, Focus Mode, Blacklist, Duration Rules, and Security Policies."""

    def __init__(self):
        self.db = protection_db
        self.whitelist = activity_whitelist
        self.focus = focus_manager
        self.risk_engine = protection_risk_engine
        self.master_protection_enabled: bool = True
        self.automatic_sleep_enabled: bool = True

    def set_master_protection(self, enabled: bool):
        self.master_protection_enabled = enabled
        logger.info(f"Master Protection toggled: {enabled}")

    def set_automatic_sleep(self, enabled: bool):
        self.automatic_sleep_enabled = enabled
        logger.info(f"Automatic Sleep toggled: {enabled}")

    def evaluate_activity(
        self,
        device_id: str,
        application: str,
        process_name: str,
        duration_seconds: float = 0.0,
        domain: Optional[str] = None,
        category_hint: Optional[str] = None,
        security_signal: Optional[Dict[str, Any]] = None
    ) -> EvaluationResult:
        """Executes full deterministic evaluation pipeline."""
        p_name = (process_name or "").lower().strip()
        a_name = (application or "").lower().strip()
        d_name = (domain or "").lower().strip()

        # STEP 1: Master Protection Enabled Check
        if not self.master_protection_enabled:
            return EvaluationResult(
                allowed=True,
                action=EnforcementAction.LOG,
                risk_level=ProtectionRiskLevel.LOW,
                reason="Protection subsystem is currently disabled by owner."
            )

        # STEP 2: High-Confidence Security Signal Evaluation
        if security_signal:
            sec_res = self._evaluate_security_signal(device_id, p_name, d_name, security_signal)
            if sec_res:
                return sec_res

        # STEP 3: Whitelist Evaluation (Evaluated BEFORE broad productivity restrictions)
        is_focus = self.focus.is_focus_active_now()
        is_whitelisted, wl_cat, wl_desc = self.whitelist.evaluate_whitelist(
            process_name=p_name,
            application_name=a_name,
            domain=d_name,
            is_focus_active=is_focus
        )

        if is_whitelisted:
            return EvaluationResult(
                allowed=True,
                action=EnforcementAction.LOG,
                risk_level=ProtectionRiskLevel.LOW,
                reason=wl_desc or "Activity is whitelisted",
                category=wl_cat or "WHITELIST",
                matched_rule=wl_desc
            )

        # STEP 4: Explicit Blacklist Rules Check
        blacklist_rules = self.db.list_activity_rules(rule_type=RuleType.BLACKLIST)
        for br in blacklist_rules:
            target = br.target.lower().strip()
            if target == p_name or target == a_name or (d_name and target in d_name):
                return EvaluationResult(
                    allowed=False,
                    action=EnforcementAction.BLOCK,
                    risk_level=ProtectionRiskLevel.HIGH,
                    reason=f"Matched explicit owner blacklist: '{br.target}' ({br.description})",
                    category="BLACKLIST",
                    matched_rule=br.rule_id
                )

        # STEP 5: Productivity Policies Evaluation
        prod_policies = self.db.list_productivity_policies()
        for policy in prod_policies:
            if not policy.enabled:
                continue

            # If policy is focus_only, check if focus mode is active and in schedule
            if policy.focus_only and not is_focus:
                continue

            matched = False
            # Check Process / App matches
            if policy.match_apps:
                for app_pattern in policy.match_apps:
                    pat = app_pattern.lower().strip()
                    if pat == p_name or pat == a_name or pat in p_name:
                        matched = True
                        break

            # Check Domain matches
            if not matched and d_name and policy.match_domains:
                for dom_pattern in policy.match_domains:
                    d_pat = dom_pattern.lower().strip()
                    if d_pat in d_name:
                        matched = True
                        break

            # Check Category Hint matches
            if not matched and category_hint and category_hint.upper() == policy.category.value:
                matched = True

            if matched:
                violation_count = self.db.get_violation_count_today(device_id, policy.policy_id)
                risk, action, reason = self.risk_engine.assess_productivity_risk(
                    policy=policy,
                    duration_seconds=duration_seconds,
                    violation_count_today=violation_count
                )

                # If automatic sleep is disabled and action is SLEEP, fallback to BLOCK or WARN
                if action == EnforcementAction.SLEEP and not self.automatic_sleep_enabled:
                    action = EnforcementAction.BLOCK
                    reason += " (Automatic sleep disabled by owner, falling back to BLOCK)"

                allowed = (action in [EnforcementAction.LOG, EnforcementAction.NOTIFY])
                return EvaluationResult(
                    allowed=allowed,
                    action=action,
                    risk_level=risk,
                    policy=policy,
                    reason=reason,
                    category=policy.category.value,
                    grace_period_seconds=policy.grace_period_seconds if action in [EnforcementAction.WARN, EnforcementAction.SLEEP, EnforcementAction.LOCK] else 0,
                    matched_rule=policy.policy_id
                )

        # STEP 6: Default Allow for unclassified normal activities
        return EvaluationResult(
            allowed=True,
            action=EnforcementAction.LOG,
            risk_level=ProtectionRiskLevel.LOW,
            reason="Activity allowed under standard operating baseline."
        )

    def _evaluate_security_signal(
        self,
        device_id: str,
        process_name: str,
        domain: str,
        security_signal: Dict[str, Any]
    ) -> Optional[EvaluationResult]:
        """Evaluates high-confidence security events."""
        signal_type = str(security_signal.get("type", "")).upper()
        target_network = str(security_signal.get("target_network", "")).lower()

        # Check if authorized security lab whitelist applies
        if self.whitelist.is_authorized_security_lab(target_network or domain or process_name):
            return EvaluationResult(
                allowed=True,
                action=EnforcementAction.LOG,
                risk_level=ProtectionRiskLevel.LOW,
                reason=f"Security activity in AUTHORIZED_SECURITY_LAB: '{target_network or domain}' - Exempt from blocking",
                category=SecurityCategory.UNAUTHORIZED_HACKING.value
            )

        sec_policies = self.db.list_security_policies()
        for sp in sec_policies:
            if not sp.enabled:
                continue

            if sp.category.value in signal_type or signal_type in sp.category.value:
                risk, action, reason = self.risk_engine.assess_security_risk(sp, security_signal)
                return EvaluationResult(
                    allowed=False,
                    action=action,
                    risk_level=risk,
                    security_policy=sp,
                    reason=reason,
                    category=sp.category.value,
                    grace_period_seconds=0,
                    matched_rule=sp.policy_id
                )

        return None

orian_policy_engine = OrianPolicyEngine()
