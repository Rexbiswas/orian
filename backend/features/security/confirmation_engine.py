import time
import json
import uuid
import logging
from typing import Optional, Dict, Any
from .config import security_config
from .database import security_db
from .models import RiskLevel, ConfirmationTicket, SecurityEventSeverity

logger = logging.getLogger("orian.security.confirmation")

class ConfirmationEngine:
    """Enterprise Confirmation Engine managing cryptographic tickets for High and Critical risk operations with TTL validation."""

    def __init__(self):
        self.db = security_db
        self.config = security_config

    def create_ticket(
        self,
        user_id: str,
        action: str,
        target: str,
        risk_level: RiskLevel,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> ConfirmationTicket:
        """Generates an ephemeral confirmation ticket stored in SQLite."""
        ticket_id = f"tkt_{uuid.uuid4().hex[:16]}"
        now = time.time()
        expires_at = now + self.config.CONFIRMATION_TICKET_TTL_SECONDS
        params_json = json.dumps(parameters or {})

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO sec_confirmation_tickets (
            ticket_id, user_id, action, target, risk_level, command,
            parameters_json, expires_at, confirmed, confirmed_at, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, NULL, ?)
        """, (
            ticket_id, user_id, action, target,
            risk_level.value if isinstance(risk_level, RiskLevel) else str(risk_level),
            command, params_json, expires_at, now
        ))
        conn.commit()
        conn.close()

        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="CONFIRMATION_REQUESTED",
            severity=SecurityEventSeverity.WARNING if risk_level == RiskLevel.HIGH else SecurityEventSeverity.HIGH,
            user_id=user_id,
            message=f"Confirmation ticket generated: {ticket_id} for action '{action}' on target '{target}'"
        )

        return ConfirmationTicket(
            ticket_id=ticket_id,
            user_id=user_id,
            action=action,
            target=target,
            risk_level=risk_level,
            command=command,
            parameters=parameters or {},
            created_at=now,
            expires_at=expires_at,
            confirmed=False
        )

    def get_ticket(self, ticket_id: str) -> Optional[ConfirmationTicket]:
        """Fetches a confirmation ticket by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sec_confirmation_tickets WHERE ticket_id = ?", (ticket_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        d = dict(row)
        return ConfirmationTicket(
            ticket_id=d["ticket_id"],
            user_id=d["user_id"],
            action=d["action"],
            target=d.get("target") or "",
            risk_level=RiskLevel(d["risk_level"]),
            command=d["command"],
            parameters=json.loads(d.get("parameters_json") or "{}"),
            created_at=d["created_at"],
            expires_at=d["expires_at"],
            confirmed=bool(d["confirmed"]),
            confirmed_at=d.get("confirmed_at")
        )

    def submit_confirmation(
        self,
        ticket_id: str,
        user_id: str,
        approved: bool,
        step_up_code: Optional[str] = None
    ) -> bool:
        """Processes user approval or rejection of a confirmation ticket."""
        ticket = self.get_ticket(ticket_id)
        if not ticket:
            raise ValueError(f"Confirmation ticket '{ticket_id}' not found")

        now = time.time()
        if ticket.expires_at < now:
            raise ValueError(f"Confirmation ticket '{ticket_id}' has expired")

        if not approved:
            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="CONFIRMATION_REJECTED",
                severity=SecurityEventSeverity.INFO,
                user_id=user_id,
                message=f"User rejected confirmation ticket {ticket_id} for action '{ticket.action}'"
            )
            return False

        # If CRITICAL and MFA required, verify step-up code
        if ticket.risk_level == RiskLevel.CRITICAL and self.config.REQUIRE_MFA_FOR_CRITICAL_RISK:
            from .mfa_engine import mfa_engine
            if not step_up_code or not mfa_engine.verify_user_totp(user_id, step_up_code):
                from .audit_logger import audit_logger
                audit_logger.log_security_event(
                    event_type="CONFIRMATION_MFA_FAILED",
                    severity=SecurityEventSeverity.CRITICAL,
                    user_id=user_id,
                    message=f"MFA step-up verification failed for critical confirmation ticket {ticket_id}"
                )
                raise PermissionError("Valid TOTP step-up authentication code required to confirm critical action")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE sec_confirmation_tickets
        SET confirmed = 1, confirmed_at = ?
        WHERE ticket_id = ?
        """, (now, ticket_id))
        conn.commit()
        conn.close()

        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="CONFIRMATION_APPROVED",
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            message=f"Confirmation ticket {ticket_id} approved for action '{ticket.action}'"
        )
        return True

confirmation_engine = ConfirmationEngine()
