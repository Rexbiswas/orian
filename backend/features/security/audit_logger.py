import time
import json
import uuid
import logging
from typing import Dict, List, Any, Optional
from .config import security_config
from .database import security_db
from .models import AuditLogEntry, SecurityEvent, SecurityEventSeverity, RiskLevel

logger = logging.getLogger("orian.security.audit")

SENSITIVE_KEYS = [
    "password", "secret", "token", "key", "api_key", "authorization",
    "access_token", "refresh_token", "totp", "mfa_secret", "jwt"
]

class AuditLogger:
    """Enterprise Audit Logging & Security Event Recording Engine writing structured logs to SQLite while sanitizing sensitive credentials."""

    def __init__(self):
        self.db = security_db
        self.config = security_config

    def _sanitize(self, data: Any) -> Any:
        """Recursively scrubs passwords, tokens, and cryptographic secrets from log payloads."""
        if isinstance(data, dict):
            clean = {}
            for k, v in data.items():
                if any(sk in k.lower() for sk in SENSITIVE_KEYS):
                    clean[k] = "[REDACTED]"
                else:
                    clean[k] = self._sanitize(v)
            return clean
        elif isinstance(data, list):
            return [self._sanitize(item) for item in data]
        elif isinstance(data, str):
            for sk in SENSITIVE_KEYS:
                if f"{sk}=" in data.lower() or f'"{sk}"' in data.lower():
                    return "[REDACTED_STRING]"
            return data
        return data

    def log_audit(
        self,
        action: str,
        tool: str,
        target: str = "",
        risk: RiskLevel = RiskLevel.LOW,
        result: str = "SUCCESS",
        user_id: str = "anonymous",
        session_id: Optional[str] = None,
        error_message: Optional[str] = None,
        ip_address: str = "127.0.0.1",
        device: str = "Desktop",
        request_id: str = "",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Writes an immutable structured audit log entry into SQLite."""
        if not self.config.AUDIT_LOGGING_ENABLED:
            return ""

        log_id = f"aud_{uuid.uuid4().hex[:16]}"
        now = time.time()
        clean_details = self._sanitize(details or {})
        details_json = json.dumps(clean_details)

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sec_audit_logs (
                id, timestamp, user_id, session_id, action, tool, target,
                risk, result, error_message, ip_address, device, request_id, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, now, user_id, session_id, action, tool, target,
                risk.value if isinstance(risk, RiskLevel) else str(risk),
                result, error_message, ip_address, device, request_id, details_json
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record audit log: {e}")

        logger.info(f"[AUDIT] {action} | Tool: {tool} | Target: {target} | Risk: {risk} | Result: {result} | User: {user_id}")
        return log_id

    def log_security_event(
        self,
        event_type: str,
        severity: SecurityEventSeverity = SecurityEventSeverity.INFO,
        user_id: Optional[str] = None,
        ip_address: str = "127.0.0.1",
        message: str = "",
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Records a security event (e.g. AUTH_LOGIN_SUCCESS, PERMISSION_DENIED) into SQLite."""
        event_id = f"evt_{uuid.uuid4().hex[:16]}"
        now = time.time()
        clean_details = self._sanitize(details or {})
        details_json = json.dumps(clean_details)

        try:
            conn = self.db.get_connection()
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sec_security_events (
                id, timestamp, event_type, severity, user_id, ip_address, message, details_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_id, now, event_type,
                severity.value if isinstance(severity, SecurityEventSeverity) else str(severity),
                user_id, ip_address, message, details_json
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to record security event: {e}")

        log_fn = logger.info if severity in [SecurityEventSeverity.INFO] else logger.warning if severity == SecurityEventSeverity.WARNING else logger.error
        log_fn(f"[SECURITY_EVENT] {event_type} [{severity}] | {message} | User: {user_id or 'anon'} | IP: {ip_address}")
        return event_id

    def query_audit_logs(self, limit: int = 50, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries recent audit logs for administration and compliance."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM sec_audit_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?", (user_id, limit))
        else:
            cursor.execute("SELECT * FROM sec_audit_logs ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def query_security_events(self, limit: int = 50, severity: Optional[str] = None) -> List[Dict[str, Any]]:
        """Queries recent security events for security dashboard."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        if severity:
            cursor.execute("SELECT * FROM sec_security_events WHERE severity = ? ORDER BY timestamp DESC LIMIT ?", (severity, limit))
        else:
            cursor.execute("SELECT * FROM sec_security_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

audit_logger = AuditLogger()
