import time
import uuid
import logging
import threading
from typing import Dict, List, Any, Optional, Callable, Set
from .models import (
    MobileAlertCategory, NotificationPriority, NotificationDeliveryStatus,
    NotificationEvent, NotificationDelivery, MobileDevice, DeviceStatus,
    ProtectionRiskLevel, NotificationActionType
)
from .database import protection_db
from features.security.audit_logger import audit_logger
from features.security.models import User, Role, RiskLevel, SecurityEventSeverity
from features.security.auth_engine import auth_engine
from features.security.mfa_engine import mfa_engine

logger = logging.getLogger("orian.protection.notification_service")

class OrianNotificationService:
    """Enterprise Notification & Mobile Alert Service.
    
    Orchestrates alert generation, recipient authorization, priority assessment,
    idempotency/deduplication, real-time push delivery pipeline, and secure actions.
    """

    def __init__(self):
        self.db = protection_db
        self.delivery_listeners: List[Callable[[Dict[str, Any]], None]] = []
        self._lock = threading.Lock()
        self._recent_events_cache: Set[str] = set()
        self._last_alert_timestamps: Dict[str, float] = {}

    def register_delivery_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """Registers listener (e.g. WebSocket / SSE broadcaster) for live push events."""
        with self._lock:
            if listener not in self.delivery_listeners:
                self.delivery_listeners.append(listener)

    def unregister_delivery_listener(self, listener: Callable[[Dict[str, Any]], None]):
        with self._lock:
            if listener in self.delivery_listeners:
                self.delivery_listeners.remove(listener)

    def _broadcast(self, payload: Dict[str, Any]):
        """Dispatches notification payload to all active client channels."""
        with self._lock:
            listeners = list(self.delivery_listeners)
        for listener in listeners:
            try:
                listener(payload)
            except Exception as e:
                logger.warning(f"Failed to broadcast mobile alert to listener: {e}")

    def create_and_send_alert(
        self,
        alert_type: MobileAlertCategory,
        title: Optional[str] = None,
        device_id: str = "My Windows Laptop",
        risk: ProtectionRiskLevel = ProtectionRiskLevel.MEDIUM,
        policy_id: Optional[str] = None,
        policy_name: Optional[str] = None,
        activity: Optional[str] = None,
        reason: str = "",
        action: str = "Warning issued",
        details: Optional[Dict[str, Any]] = None,
        event_id: Optional[str] = None,
        force_send: bool = False
    ) -> Optional[NotificationEvent]:
        """Creates a structured mobile notification, validates recipients, performs
        idempotency checks, records delivery state, and broadcasts real-time push alert.
        """
        now = time.time()
        evt_id = event_id or f"evt_{uuid.uuid4().hex[:12]}"

        # 1. Duplicate Alert Protection (Idempotency Key & Damping Check)
        if not force_send:
            if self.db.is_duplicate_notification(evt_id) or evt_id in self._recent_events_cache:
                logger.info(f"Duplicate alert blocked by event_id idempotency: '{evt_id}'")
                return None

            # Rate-limiting deduplication: Prevent spamming exact same alert within 10 seconds
            dedup_key = f"{alert_type.value}:{activity or ''}:{device_id}:{reason}"
            last_sent = self._last_alert_timestamps.get(dedup_key, 0)
            if now - last_sent < 10.0 and risk not in [ProtectionRiskLevel.CRITICAL, ProtectionRiskLevel.HIGH]:
                logger.info(f"Duplicate alert dampened (sent {now - last_sent:.1f}s ago): '{dedup_key}'")
                return None
            self._last_alert_timestamps[dedup_key] = now

        # 2. Format Title & Priority
        if not title:
            if "SECURITY" in alert_type.value or "TAMPERING" in alert_type.value or "HACKING" in alert_type.value or "MALWARE" in alert_type.value:
                title = "ORIAN SECURITY ALERT"
            elif alert_type == MobileAlertCategory.AUTOMATIC_SLEEP:
                title = "ORIAN ALERT: SLEEP EXECUTED"
            else:
                title = "ORIAN ALERT"

        # 3. Construct NotificationEvent Entity
        event = NotificationEvent(
            event_id=evt_id,
            type=alert_type,
            title=title,
            device_id=device_id,
            risk=risk,
            policy_id=policy_id,
            policy_name=policy_name or policy_id or "Security Protection",
            activity=activity,
            reason=reason or f"Event triggered by {alert_type.value}",
            action=action,
            timestamp=now,
            status="UNREAD",
            details_json=details or {}
        )

        # 4. Persist to SQLite
        self.db.record_notification_event(event)
        with self._lock:
            self._recent_events_cache.add(evt_id)
            if len(self._recent_events_cache) > 500:
                self._recent_events_cache.clear()

        # 5. Query active/paired mobile devices to record delivery pipeline
        active_mobiles = self.db.list_mobile_devices(active_only=True)
        for mob in active_mobiles:
            delivery = NotificationDelivery(
                delivery_id=f"del_{uuid.uuid4().hex[:12]}",
                event_id=evt_id,
                mobile_device_id=mob.device_id,
                channel="WEBSOCKET",
                status=NotificationDeliveryStatus.SENT,
                attempt_count=1,
                created_at=now,
                last_attempt_at=now,
                delivered_at=now
            )
            self.db.record_notification_delivery(delivery)

        # 6. Audit Logging
        audit_logger.log_audit(
            action="MOBILE_ALERT_CREATED",
            tool="OrianNotificationService",
            target=activity or device_id,
            risk=RiskLevel(risk.value),
            result="SENT",
            details={
                "event_id": evt_id,
                "type": alert_type.value,
                "title": title,
                "device": device_id,
                "risk": risk.value,
                "action": action,
                "recipients_count": len(active_mobiles)
            }
        )

        # 7. Real-Time Push Dispatch
        broadcast_payload = {
            "type": "MOBILE_ALERT_PUSH",
            "event": event.model_dump(),
            "timestamp": now
        }
        self._broadcast(broadcast_payload)
        logger.info(f"Dispatched mobile alert '{alert_type.value}' (event_id: {evt_id}, risk: {risk.value})")
        return event

    def acknowledge_alert(self, event_id: str, user: User) -> bool:
        """Marks a mobile alert as ACKNOWLEDGED by the authorized user/owner."""
        event = self.db.get_notification_event(event_id)
        if not event:
            raise ValueError(f"Alert '{event_id}' not found.")

        success = self.db.acknowledge_notification(event_id, user_id=user.username)
        if success:
            audit_logger.log_audit(
                action="MOBILE_ALERT_ACKNOWLEDGED",
                tool="OrianNotificationService",
                target=event_id,
                risk=RiskLevel.LOW,
                result="ACKNOWLEDGED",
                user_id=user.id,
                details={"event_id": event_id, "user": user.username}
            )
            self._broadcast({
                "type": "ALERT_ACKNOWLEDGED",
                "event_id": event_id,
                "acknowledged_by": user.username,
                "timestamp": time.time()
            })
        return success

    def handle_secure_action(
        self,
        event_id: str,
        action_type: NotificationActionType,
        user: User,
        reason: Optional[str] = None,
        password: Optional[str] = None,
        step_up_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Executes secure actions initiated from mobile notification cards with step-up authentication."""
        event = self.db.get_notification_event(event_id)
        if not event:
            raise ValueError(f"Event '{event_id}' not found.")

        # Non-sensitive actions
        if action_type == NotificationActionType.ACKNOWLEDGE:
            self.acknowledge_alert(event_id, user)
            return {"success": True, "action": "ACKNOWLEDGE", "event_id": event_id}

        if action_type == NotificationActionType.VIEW_DETAILS:
            return {"success": True, "event": event.model_dump()}

        # Privileged actions require OWNER/ADMIN role and password/MFA verification
        if action_type in [NotificationActionType.OWNER_OVERRIDE, NotificationActionType.DISABLE_POLICY]:
            if user.role not in [Role.OWNER, Role.ADMIN]:
                raise PermissionError(f"Action '{action_type.value}' requires OWNER or ADMIN role.")

            # Authenticate: Push notification alone is NEVER treated as authentication
            if user.mfa_enabled:
                if not step_up_code or not mfa_engine.verify_user_totp(user.id, step_up_code):
                    raise PermissionError("Step-up MFA verification required to execute privileged command.")
            elif password:
                conn = auth_engine.db.get_connection()
                cur = conn.cursor()
                cur.execute("SELECT password_hash FROM sec_users WHERE id = ?", (user.id,))
                row = cur.fetchone()
                conn.close()
                if not row or not auth_engine.crypto.verify_password(password, row["password_hash"]):
                    raise PermissionError("Invalid password verification.")
            else:
                raise PermissionError("Password or MFA verification required for privileged action.")

            if action_type == NotificationActionType.OWNER_OVERRIDE:
                # If event has violation ID or policy ID, submit override
                violation_id = event.details_json.get("violation_id")
                from .laptop_service import laptop_protection_service
                if violation_id:
                    laptop_protection_service.submit_owner_override(
                        violation_id=violation_id,
                        user=user,
                        reason=reason or "Overridden from mobile notification",
                        password=password,
                        step_up_code=step_up_code
                    )
                self.create_and_send_alert(
                    alert_type=MobileAlertCategory.OWNER_OVERRIDE,
                    title="ORIAN ALERT: OWNER OVERRIDE",
                    device_id=event.device_id,
                    risk=ProtectionRiskLevel.LOW,
                    policy_id=event.policy_id,
                    policy_name=event.policy_name,
                    activity=event.activity,
                    reason=f"Override approved by {user.username}",
                    action="Policy overridden",
                    force_send=True
                )
                return {"success": True, "action": "OWNER_OVERRIDE", "event_id": event_id}

            elif action_type == NotificationActionType.DISABLE_POLICY:
                if event.policy_id:
                    pol = self.db.get_productivity_policy(event.policy_id)
                    if pol:
                        pol.enabled = False
                        self.db.save_productivity_policy(pol)
                        self.create_and_send_alert(
                            alert_type=MobileAlertCategory.POLICY_CHANGED,
                            title="ORIAN ALERT: POLICY DISABLED",
                            device_id=event.device_id,
                            risk=ProtectionRiskLevel.LOW,
                            policy_id=pol.policy_id,
                            policy_name=pol.name,
                            reason=f"Policy '{pol.name}' disabled by {user.username} from mobile alert",
                            action="Policy disabled",
                            force_send=True
                        )
                        return {"success": True, "action": "DISABLE_POLICY", "policy_id": pol.policy_id}

        return {"success": False, "error": f"Unhandled action type '{action_type.value}'"}

orian_notification_service = OrianNotificationService()
