import logging
from typing import Dict, Any, Optional, Tuple
from .models import (
    ProtectionRiskLevel, EnforcementAction, ProductivityCategory,
    SecurityCategory, ProductivityPolicy, SecurityPolicy
)
from .database import protection_db

logger = logging.getLogger("orian.protection.risk_engine")

class ProtectionRiskEngine:
    """Enterprise Risk Engine assessing productivity and security violation impact, duration damping, and escalation thresholds."""

    def __init__(self):
        self.db = protection_db

    def assess_productivity_risk(
        self,
        policy: ProductivityPolicy,
        duration_seconds: float,
        violation_count_today: int
    ) -> Tuple[ProtectionRiskLevel, EnforcementAction, str]:
        """Calculates risk level and escalated action based on duration damping and today's violation history."""
        # 1. Duration Damping for Terminal and Short Switches
        if policy.category == ProductivityCategory.TERMINAL:
            if duration_seconds < 30:
                return ProtectionRiskLevel.LOW, EnforcementAction.LOG, f"Terminal opened for brief duration ({int(duration_seconds)}s < 30s) - Ignored"
            elif duration_seconds < policy.min_duration_seconds:
                return ProtectionRiskLevel.LOW, EnforcementAction.LOG, f"Terminal active for ({int(duration_seconds)}s < {policy.min_duration_seconds}s threshold) - Logged"

        # 2. General short switch damping (< 5s for non-gaming apps)
        if duration_seconds < 5 and policy.category not in [ProductivityCategory.BLOCKED_APPS, ProductivityCategory.FOCUS_MODE_BYPASS]:
            return ProtectionRiskLevel.LOW, EnforcementAction.LOG, f"Brief application switch ({int(duration_seconds)}s) - Logged"

        # 3. Violation Escalation
        current_violation_index = violation_count_today + 1

        if current_violation_index == 1:
            action = policy.default_action
            risk = policy.risk_level
            reason = f"First violation for policy '{policy.name}'. Action: {action.value}"
        elif current_violation_index == 2:
            action = EnforcementAction.WARN
            risk = policy.risk_level
            reason = f"Second violation for policy '{policy.name}'. Escalating warning."
        elif current_violation_index == 3:
            action = EnforcementAction.BLOCK
            risk = ProtectionRiskLevel.HIGH
            reason = f"Third violation for policy '{policy.name}'. Escalating to BLOCK."
        else:
            # 4th violation or higher
            action = policy.escalation_action
            risk = ProtectionRiskLevel.HIGH if action != EnforcementAction.SLEEP else ProtectionRiskLevel.HIGH
            reason = f"Repeated violation ({current_violation_index}x) for policy '{policy.name}'. Escalating to {action.value}."

        return risk, action, reason

    def assess_security_risk(
        self,
        security_policy: SecurityPolicy,
        security_signal: Optional[Dict[str, Any]] = None
    ) -> Tuple[ProtectionRiskLevel, EnforcementAction, str]:
        """Assesses high-confidence security event risk and determines authoritative response."""
        sig = security_signal or {}
        cat = security_policy.category

        if cat == SecurityCategory.SECURITY_TAMPERING:
            return (
                ProtectionRiskLevel.CRITICAL,
                EnforcementAction.BLOCK,
                "CRITICAL SECURITY EVENT: Attempt to disable or tamper with Orian Security, Laptop Agent, or Gateway governance."
            )
        elif cat == SecurityCategory.PROTECTED_DATA_ACCESS:
            return (
                ProtectionRiskLevel.CRITICAL,
                EnforcementAction.BLOCK,
                "CRITICAL SECURITY EVENT: Unauthorized access attempt to protected user data, encryption keys, or credentials."
            )
        elif cat == SecurityCategory.MALWARE_ACTIVITY:
            return (
                ProtectionRiskLevel.CRITICAL,
                EnforcementAction.BLOCK,
                "HIGH-CONFIDENCE SECURITY EVENT: Malicious payload execution or persistence indicator detected."
            )
        elif cat == SecurityCategory.UNAUTHORIZED_HACKING:
            return (
                ProtectionRiskLevel.HIGH,
                EnforcementAction.BLOCK,
                "HIGH-CONFIDENCE SECURITY EVENT: Unauthorized attack attempt detected outside of whitelisted security laboratories."
            )
        else:
            return (
                security_policy.risk_level,
                security_policy.default_action,
                f"Security policy '{security_policy.name}' violation detected."
            )

protection_risk_engine = ProtectionRiskEngine()
