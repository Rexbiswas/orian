import secrets
import hashlib
import hmac
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from .models import LaptopDevice, DeviceStatus
from .database import protection_db
from features.security.audit_logger import audit_logger
from features.security.models import RiskLevel, SecurityEventSeverity

logger = logging.getLogger("orian.protection.device_manager")

class LaptopDeviceManager:
    """Enterprise Laptop Device Identity, Pairing, and Lifecycle Manager enforcing Owner authorization and revocation."""

    def __init__(self):
        self.db = protection_db

    def initiate_pairing(
        self,
        device_id: str,
        device_name: str,
        agent_version: str = "1.0.0",
        owner_id: str = "orian_admin"
    ) -> Tuple[LaptopDevice, str]:
        """Step 1: Agent initiates pairing request. Returns (device, pairing_secret)."""
        clean_dev_id = device_id.strip().lower()
        pairing_code = f"PAIR-{secrets.randbelow(900000) + 100000}"
        shared_secret = secrets.token_hex(32)

        secret_hash = hashlib.sha256(shared_secret.encode("utf-8")).hexdigest()

        device = self.db.register_device(
            device_id=clean_dev_id,
            device_name=device_name,
            owner_id=owner_id,
            auth_token_hash=secret_hash,
            pairing_code=pairing_code,
            agent_version=agent_version
        )

        audit_logger.log_audit(
            action="DEVICE_PAIRING_REQUESTED",
            tool="LaptopDeviceManager",
            target=clean_dev_id,
            risk=RiskLevel.MEDIUM,
            result="PENDING",
            user_id=owner_id,
            details={"device_name": device_name, "pairing_code": pairing_code}
        )

        logger.info(f"Initiated pairing for device '{clean_dev_id}' with pairing code {pairing_code}")
        return device, shared_secret

    def approve_device(self, device_id: str, approved: bool, owner_id: str = "orian_admin") -> bool:
        """Step 2: Owner approves or rejects the pending laptop device."""
        device = self.db.get_device(device_id)
        if not device:
            raise ValueError(f"Device '{device_id}' not found.")

        if device.revoked:
            raise PermissionError(f"Cannot approve revoked device '{device_id}'.")

        new_status = DeviceStatus.ACTIVE if approved else DeviceStatus.UNREGISTERED
        success = self.db.update_device_status(device_id, new_status)

        audit_logger.log_audit(
            action="DEVICE_APPROVAL_DECISION",
            tool="LaptopDeviceManager",
            target=device_id,
            risk=RiskLevel.HIGH if approved else RiskLevel.MEDIUM,
            result="APPROVED" if approved else "REJECTED",
            user_id=owner_id,
            details={"status": new_status.value}
        )

        return success

    def revoke_device(self, device_id: str, reason: str = "Owner manual revocation", owner_id: str = "orian_admin") -> bool:
        """Revokes a laptop device. Once revoked, ALL privileged commands are permanently rejected."""
        device = self.db.get_device(device_id)
        if not device:
            return False

        success = self.db.update_device_status(device_id, DeviceStatus.REVOKED, revoked=True)

        audit_logger.log_security_event(
            event_type="DEVICE_REVOKED",
            severity=SecurityEventSeverity.HIGH,
            user_id=owner_id,
            message=f"Laptop device '{device_id}' has been REVOKED by owner. Reason: {reason}"
        )

        logger.warning(f"Device '{device_id}' revoked. Reason: {reason}")
        return success

    def validate_device_auth(self, device_id: str, token_or_signature: str, payload_str: str = "") -> bool:
        """Verifies device token or HMAC signature."""
        device = self.db.get_device(device_id)
        if not device:
            logger.warning(f"Auth validation failed: Unknown device '{device_id}'")
            return False

        if device.revoked or device.status != DeviceStatus.ACTIVE:
            logger.warning(f"Auth validation failed: Device '{device_id}' is revoked or not active ({device.status})")
            return False

        # Direct token match check
        hashed_input = hashlib.sha256(token_or_signature.encode("utf-8")).hexdigest()
        if hmac.compare_digest(hashed_input, device.auth_token_hash):
            return True

        # HMAC signature check
        if payload_str:
            # Reconstruct HMAC
            expected_sig = hmac.new(
                device.auth_token_hash.encode("utf-8"),
                payload_str.encode("utf-8"),
                hashlib.sha256
            ).hexdigest()
            if hmac.compare_digest(expected_sig, token_or_signature):
                return True

        return False

    def heartbeat(self, device_id: str, agent_version: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        device = self.db.get_device(device_id)
        if not device or device.revoked:
            return False
        return self.db.update_device_heartbeat(device_id, agent_version=agent_version, metadata=metadata)

    def is_device_active(self, device_id: str) -> bool:
        device = self.db.get_device(device_id)
        return bool(device and not device.revoked and device.status == DeviceStatus.ACTIVE)

laptop_device_manager = LaptopDeviceManager()
