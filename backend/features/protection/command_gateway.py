import uuid
import time
import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Optional, Tuple
from .models import LaptopCommand, LaptopCommandResult, DeviceStatus
from .database import protection_db
from .device_manager import laptop_device_manager
from features.security.gateway import security_gateway
from features.security.models import User, Role, RiskLevel, SecurityEventSeverity
from features.security.audit_logger import audit_logger

logger = logging.getLogger("orian.protection.command_gateway")

PERMITTED_COMMANDS = {"GET_STATUS", "NOTIFY", "LOCK", "SLEEP"}
PROHIBITED_COMMANDS = {
    "EXECUTE_COMMAND", "RUN_SHELL", "RUN_POWERSHELL",
    "EXECUTE_ARBITRARY_PROGRAM", "DELETE_FILE", "DOWNLOAD_FILE"
}
MAX_CLOCK_SKEW_SECONDS = 15.0
DEFAULT_COMMAND_TTL_SECONDS = 15.0

class LaptopCommandGateway:
    """Security-Hardened Laptop Command Gateway enforcing Authentication, Authorization, Nonce Uniqueness, Short TTL Expiration, and Replay Protection."""

    def __init__(self):
        self.db = protection_db
        self.device_manager = laptop_device_manager

    def generate_signed_command(
        self,
        device_id: str,
        command: str,
        policy_id: Optional[str] = None,
        reason: str = "PRODUCTIVITY_POLICY",
        ttl_seconds: float = DEFAULT_COMMAND_TTL_SECONDS
    ) -> LaptopCommand:
        """Constructs an authenticated, replay-protected command packet."""
        cmd_upper = command.strip().upper()
        if cmd_upper not in PERMITTED_COMMANDS:
            raise ValueError(f"Prohibited or unsupported command: '{command}'")

        device = self.db.get_device(device_id)
        if not device or device.revoked or device.status != DeviceStatus.ACTIVE:
            raise PermissionError(f"Target device '{device_id}' is not active or has been revoked.")

        now = time.time()
        req_id = f"cmd_{uuid.uuid4().hex}"
        expires_at = now + ttl_seconds

        # Payload string for HMAC signature
        payload_str = f"{req_id}:{device_id}:{cmd_upper}:{policy_id or ''}:{int(now)}:{int(expires_at)}"
        sig = hmac.new(
            device.auth_token_hash.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        cmd_obj = LaptopCommand(
            request_id=req_id,
            device_id=device_id,
            command=cmd_upper,
            policy_id=policy_id,
            reason=reason,
            timestamp=now,
            expires_at=expires_at,
            signature=sig,
            status="ISSUED"
        )

        self.db.record_command(cmd_obj)
        logger.info(f"Generated signed command '{cmd_upper}' (request_id: {req_id}) for device '{device_id}' (expires in {ttl_seconds}s)")
        return cmd_obj

    def validate_and_authorize_command(
        self,
        command_packet: Dict[str, Any],
        user: Optional[User] = None
    ) -> Tuple[bool, Optional[str]]:
        """Authorizes and validates command packet against replay, expiration, clock skew, and device status."""
        req_id = command_packet.get("request_id")
        dev_id = command_packet.get("device_id")
        cmd = str(command_packet.get("command", "")).upper().strip()
        ts = command_packet.get("timestamp", 0)
        exp = command_packet.get("expires_at", 0)
        sig = command_packet.get("signature")
        now = time.time()

        # 1. Prohibited command check
        if cmd in PROHIBITED_COMMANDS or cmd not in PERMITTED_COMMANDS:
            audit_logger.log_security_event(
                event_type="UNAUTHORIZED_COMMAND_ATTEMPT",
                severity=SecurityEventSeverity.CRITICAL,
                message=f"Attempted to execute prohibited command '{cmd}' on device '{dev_id}'"
            )
            return False, f"Prohibited command rejected: '{cmd}' is not an authorized laptop command."

        # 2. Check Device Registration and Revocation
        device = self.db.get_device(dev_id)
        if not device:
            audit_logger.log_security_event(
                event_type="UNKNOWN_DEVICE_REJECTED",
                severity=SecurityEventSeverity.HIGH,
                message=f"Command '{cmd}' rejected: Unknown device '{dev_id}'"
            )
            return False, f"Unknown device '{dev_id}' rejected."

        if device.revoked:
            audit_logger.log_security_event(
                event_type="REVOKED_DEVICE_COMMAND_REJECTED",
                severity=SecurityEventSeverity.CRITICAL,
                message=f"Command '{cmd}' rejected: Device '{dev_id}' is permanently revoked."
            )
            return False, f"Revoked device '{dev_id}' cannot execute privileged commands."

        if device.status != DeviceStatus.ACTIVE:
            return False, f"Device '{dev_id}' is not in ACTIVE state (current: {device.status.value})."

        # 3. Check Clock Skew
        if abs(now - ts) > MAX_CLOCK_SKEW_SECONDS:
            audit_logger.log_security_event(
                event_type="CLOCK_SKEW_EXCEEDED",
                severity=SecurityEventSeverity.WARNING,
                message=f"Command '{req_id}' rejected: Clock skew exceeded ({abs(now-ts):.1f}s > {MAX_CLOCK_SKEW_SECONDS}s)"
            )
            return False, f"Clock skew validation failed for request '{req_id}'."

        # 4. Check Expiration (Fail-safe guarantee)
        if now > exp:
            audit_logger.log_security_event(
                event_type="EXPIRED_COMMAND_REJECTED",
                severity=SecurityEventSeverity.WARNING,
                message=f"Command '{req_id}' rejected: Request expired ({now - exp:.1f}s ago)"
            )
            return False, f"Command '{req_id}' has expired and will not be executed."

        # 5. Check Replay & Nonce Uniqueness in Database
        existing_cmd = self.db.get_command(req_id)
        if existing_cmd and existing_cmd.status in ["EXECUTED", "ACKNOWLEDGED", "REJECTED"]:
            audit_logger.log_security_event(
                event_type="REPLAY_ATTACK_BLOCKED",
                severity=SecurityEventSeverity.CRITICAL,
                message=f"Replay attack detected: Request ID '{req_id}' has already been processed (status: {existing_cmd.status})"
            )
            return False, f"Replay rejected: Request ID '{req_id}' has already been executed."

        # 6. Verify HMAC Signature
        policy_id = command_packet.get("policy_id") or ""
        payload_str = f"{req_id}:{dev_id}:{cmd}:{policy_id}:{int(ts)}:{int(exp)}"
        expected_sig = hmac.new(
            device.auth_token_hash.encode("utf-8"),
            payload_str.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not sig or not hmac.compare_digest(expected_sig, sig):
            audit_logger.log_security_event(
                event_type="INVALID_COMMAND_SIGNATURE",
                severity=SecurityEventSeverity.CRITICAL,
                message=f"Command '{req_id}' rejected: Cryptographic signature mismatch on device '{dev_id}'"
            )
            return False, f"Invalid cryptographic signature for request '{req_id}'."

        return True, None

    def record_acknowledgment(self, request_id: str, success: bool, result_message: str, error: Optional[str] = None):
        """Records agent execution acknowledgment in SQLite audit and command history."""
        status = "EXECUTED" if success else "FAILED"
        result_dict = {
            "success": success,
            "message": result_message,
            "error": error,
            "ack_time": time.time()
        }
        self.db.update_command_result(request_id, status, result_dict)

        cmd = self.db.get_command(request_id)
        action_name = f"LAPTOP_{cmd.command if cmd else 'CMD'}_{status}"

        audit_logger.log_audit(
            action=action_name,
            tool="LaptopCommandGateway",
            target=cmd.device_id if cmd else "unknown_device",
            risk=RiskLevel.HIGH if cmd and cmd.command == "SLEEP" else RiskLevel.MEDIUM,
            result="SUCCESS" if success else "FAILED",
            error_message=error,
            details=result_dict
        )

laptop_command_gateway = LaptopCommandGateway()
