import time
import uuid
import threading
import logging
from typing import Dict, Any, Optional, List, Callable
from .models import (
    ActivityEvent, PolicyViolation, PolicyOverride, EnforcementAction,
    ProtectionRiskLevel, LaptopCommand
)
from .database import protection_db
from .policy_engine import orian_policy_engine, EvaluationResult
from .command_gateway import laptop_command_gateway
from features.security.models import User, Role, RiskLevel, SecurityEventSeverity
from features.security.audit_logger import audit_logger
from features.security.auth_engine import auth_engine
from features.security.mfa_engine import mfa_engine

logger = logging.getLogger("orian.protection.laptop_service")

class LaptopProtectionService:
    """Master Coordinator orchestrating Activity Ingestion, Policy Evaluation, Warning Notifications, Grace Period Timers, Owner Override, and Secure Command Dispatch."""

    def __init__(self):
        self.db = protection_db
        self.policy_engine = orian_policy_engine
        self.command_gateway = laptop_command_gateway
        self.active_grace_timers: Dict[str, threading.Timer] = {}
        self.event_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._lock = threading.Lock()

    def register_event_listener(self, listener: Callable[[Dict[str, Any]], None]):
        self.event_listeners.append(listener)

    def _broadcast_event(self, event_data: Dict[str, Any]):
        for listener in self.event_listeners:
            try:
                listener(event_data)
            except Exception as e:
                logger.warning(f"Error in protection event listener: {e}")

    def process_activity_report(
        self,
        device_id: str,
        application: str,
        process_name: str,
        duration_seconds: float = 0.0,
        window_title: Optional[str] = None,
        domain: Optional[str] = None,
        category_hint: Optional[str] = None,
        security_signal: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Ingests activity from Laptop Agent / Monitor, runs deterministic evaluation, and handles enforcement."""
        now = time.time()
        event_id = f"evt_{uuid.uuid4().hex}"

        # 1. Deterministic Policy Evaluation
        eval_res: EvaluationResult = self.policy_engine.evaluate_activity(
            device_id=device_id,
            application=application,
            process_name=process_name,
            duration_seconds=duration_seconds,
            domain=domain,
            category_hint=category_hint,
            security_signal=security_signal
        )

        # 2. Persist Activity Event
        event_obj = ActivityEvent(
            event_id=event_id,
            device_id=device_id,
            category=eval_res.category,
            application=application,
            process_name=process_name,
            window_title_sanitized=(window_title or "")[:120],
            duration_seconds=duration_seconds,
            timestamp=now,
            policy_id=eval_res.policy.policy_id if eval_res.policy else (eval_res.security_policy.policy_id if eval_res.security_policy else None),
            risk_level=eval_res.risk_level,
            action_taken=eval_res.action,
            matched_rule=eval_res.matched_rule
        )
        self.db.log_activity_event(event_obj)

        response_payload = {
            "event_id": event_id,
            "device_id": device_id,
            "allowed": eval_res.allowed,
            "action": eval_res.action.value,
            "risk_level": eval_res.risk_level.value,
            "category": eval_res.category,
            "reason": eval_res.reason,
            "policy_id": event_obj.policy_id,
            "grace_period_seconds": eval_res.grace_period_seconds,
            "violation_id": None
        }

        # 3. Handle Enforcement & Warning System
        if eval_res.action in [EnforcementAction.WARN, EnforcementAction.SLEEP, EnforcementAction.LOCK, EnforcementAction.BLOCK]:
            violation_id = f"viol_{uuid.uuid4().hex}"
            grace_seconds = eval_res.grace_period_seconds if eval_res.grace_period_seconds > 0 else 10
            expires_at = now + grace_seconds

            violation_obj = PolicyViolation(
                violation_id=violation_id,
                event_id=event_id,
                device_id=device_id,
                policy_id=event_obj.policy_id or "security-policy",
                violation_count=self.db.get_violation_count_today(device_id, event_obj.policy_id or "default") + 1,
                risk_level=eval_res.risk_level,
                action_enforced=eval_res.action,
                warning_issued_at=now,
                grace_period_expires_at=expires_at,
                status="WARNED" if eval_res.action in [EnforcementAction.WARN, EnforcementAction.SLEEP, EnforcementAction.LOCK] else "ENFORCED"
            )
            self.db.record_violation(violation_obj)
            response_payload["violation_id"] = violation_id

            # Emit Warning Notification Broadcast
            warning_msg = {
                "type": "ORIAN_PROTECTION_ALERT",
                "title": "ORIAN PROTECTION ALERT",
                "violation_id": violation_id,
                "device_id": device_id,
                "activity": process_name or application,
                "category": eval_res.category,
                "policy": eval_res.policy.name if eval_res.policy else "Security Policy",
                "risk": eval_res.risk_level.value,
                "reason": eval_res.reason,
                "action": eval_res.action.value,
                "countdown_seconds": grace_seconds,
                "expires_at": expires_at
            }
            self._broadcast_event(warning_msg)

            audit_logger.log_audit(
                action="POLICY_WARNING_ISSUED",
                tool="LaptopProtectionService",
                target=process_name or application,
                risk=RiskLevel(eval_res.risk_level.value),
                result="WARNING_SHOWN",
                details=warning_msg
            )

            # Schedule Grace Period Expiration Trigger if action is privileged (SLEEP/LOCK)
            if eval_res.action in [EnforcementAction.SLEEP, EnforcementAction.LOCK]:
                self._schedule_grace_period_enforcement(violation_id, device_id, eval_res.action, grace_seconds)

        return response_payload

    def _schedule_grace_period_enforcement(self, violation_id: str, device_id: str, action: EnforcementAction, grace_seconds: int):
        with self._lock:
            # Cancel any existing timer for this violation
            if violation_id in self.active_grace_timers:
                self.active_grace_timers[violation_id].cancel()

            timer = threading.Timer(grace_seconds, self._on_grace_period_expired, args=[violation_id, device_id, action])
            timer.daemon = True
            self.active_grace_timers[violation_id] = timer
            timer.start()

    def _on_grace_period_expired(self, violation_id: str, device_id: str, action: EnforcementAction):
        with self._lock:
            self.active_grace_timers.pop(violation_id, None)

        violation = self.db.get_active_violation(violation_id)
        if not violation or violation.overridden or violation.status in ["OVERRIDDEN", "CANCELLED"]:
            logger.info(f"Grace period expired for '{violation_id}', but violation was already resolved/overridden.")
            return

        # Execute Privileged Command Dispatch
        logger.warning(f"Grace period expired for '{violation_id}' without owner override. Enforcing action '{action.value}' on device '{device_id}'")
        self.db.update_violation_status(violation_id, "ENFORCED")

        try:
            cmd = self.command_gateway.generate_signed_command(
                device_id=device_id,
                command=action.value,
                policy_id=violation.policy_id,
                reason="GRACE_PERIOD_EXPIRED_ENFORCEMENT",
                ttl_seconds=15
            )

            # Broadcast command packet to device listeners/agent
            self._broadcast_event({
                "type": "EXECUTE_SIGNED_COMMAND",
                "command_packet": cmd.model_dump()
            })

        except Exception as e:
            logger.error(f"Failed to generate signed command upon grace expiry: {e}")

    def cancel_violation_if_activity_stopped(self, violation_id: str) -> bool:
        """Cancels enforcement if offending activity is stopped during grace period."""
        with self._lock:
            if violation_id in self.active_grace_timers:
                self.active_grace_timers[violation_id].cancel()
                self.active_grace_timers.pop(violation_id, None)

        success = self.db.update_violation_status(violation_id, "CANCELLED")
        if success:
            logger.info(f"Violation '{violation_id}' CANCELLED (Activity stopped by user).")
            self._broadcast_event({
                "type": "ENFORCEMENT_CANCELLED",
                "violation_id": violation_id,
                "reason": "ACTIVITY_STOPPED"
            })
        return success

    def submit_owner_override(
        self,
        violation_id: str,
        user: User,
        reason: str,
        password: Optional[str] = None,
        step_up_code: Optional[str] = None
    ) -> bool:
        """Processes Owner Override with role-based validation and optional MFA step-up for HIGH/CRITICAL risk."""
        violation = self.db.get_active_violation(violation_id)
        if not violation:
            raise ValueError(f"Violation '{violation_id}' not found.")

        # 1. Permission check: Only OWNER or ADMIN can override
        if user.role not in [Role.OWNER, Role.ADMIN]:
            audit_logger.log_security_event(
                event_type="UNAUTHORIZED_OVERRIDE_ATTEMPT",
                severity=SecurityEventSeverity.WARNING,
                user_id=user.id,
                message=f"User '{user.username}' ({user.role.value}) attempted unauthorized policy override."
            )
            raise PermissionError(f"Owner override requires OWNER or ADMIN privileges. Your role is '{user.role.value}'.")

        # 2. Stronger authentication verification for HIGH/CRITICAL risk
        if violation.risk_level in [ProtectionRiskLevel.HIGH, ProtectionRiskLevel.CRITICAL]:
            if user.mfa_enabled:
                if not step_up_code or not mfa_engine.verify_user_totp(user.id, step_up_code):
                    raise PermissionError("Step-up MFA verification code required for HIGH/CRITICAL policy override.")
            elif password:
                # Verify password
                conn = auth_engine.db.get_connection()
                cur = conn.cursor()
                cur.execute("SELECT password_hash FROM sec_users WHERE id = ?", (user.id,))
                row = cur.fetchone()
                conn.close()
                if not row or not auth_engine.crypto.verify_password(password, row["password_hash"]):
                    raise PermissionError("Invalid password for high-risk override verification.")

        # 3. Cancel active grace timer
        with self._lock:
            if violation_id in self.active_grace_timers:
                self.active_grace_timers[violation_id].cancel()
                self.active_grace_timers.pop(violation_id, None)

        # 4. Record Override in DB
        override_obj = PolicyOverride(
            override_id=f"ovr_{uuid.uuid4().hex}",
            violation_id=violation_id,
            user_id=user.id,
            policy_id=violation.policy_id,
            reason=reason,
            risk_level=violation.risk_level,
            timestamp=time.time()
        )
        self.db.record_override(override_obj)
        self.db.update_violation_status(violation_id, "OVERRIDDEN", overridden_by=user.username)

        # 5. Record tamper-resistant audit log
        audit_logger.log_audit(
            action="USER_OVERRIDE",
            tool="LaptopProtectionService",
            target=violation.policy_id,
            risk=RiskLevel(violation.risk_level.value),
            result="OVERRIDDEN",
            user_id=user.id,
            details={
                "violation_id": violation_id,
                "reason": reason,
                "overridden_by": user.username,
                "risk_level": violation.risk_level.value
            }
        )

        self._broadcast_event({
            "type": "ENFORCEMENT_CANCELLED",
            "violation_id": violation_id,
            "reason": f"OWNER_OVERRIDE by {user.username}"
        })

        logger.info(f"Policy override approved for '{violation_id}' by user '{user.username}' ({reason})")
        return True

laptop_protection_service = LaptopProtectionService()
