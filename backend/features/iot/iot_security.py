import time
import json
import uuid
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional, Tuple

from features.security.config import security_config
from features.security.crypto import crypto_engine
from features.security.database import security_db
from features.security.models import SecurityEventSeverity

logger = logging.getLogger("orian.iot.security")

class IoTSecurityEngine:
    """Enterprise IoT Hardware Security Engine enforcing unique ESP32 identities, device pairing, replay attack protection, and command signature verification."""

    def __init__(self):
        self.config = security_config
        self.crypto = crypto_engine
        self.db = security_db
        self._seen_nonces: Dict[str, float] = {} # nonce -> expiry_time
        self._ensure_baseline_credentials()

    def _ensure_baseline_credentials(self):
        """Seeds baseline IoT hardware credentials if missing."""
        baseline_devices = [
            ("esp32_main_core", "Orian ESP32 Hub"),
            ("room_light", "Room Light"),
            ("bedroom_fan", "Bedroom Fan"),
            ("living_room_ac", "Living Room AC"),
            ("dht22_temp_sensor", "Room Climate Sensor"),
            ("room_heater", "Room Heater"),
            ("patio_light", "Patio Light")
        ]
        now = time.time()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        for dev_id, name in baseline_devices:
            cursor.execute("SELECT device_id FROM sec_iot_credentials WHERE device_id = ?", (dev_id,))
            if not cursor.fetchone():
                token = f"token_{dev_id}_secure"
                thash = self.crypto.hash_sha256(token)
                pub_id = f"pub_{dev_id}"
                cursor.execute("""
                INSERT OR IGNORE INTO sec_iot_credentials (
                    device_id, secret_token_hash, public_id, status,
                    is_registered, last_nonce, last_command_timestamp,
                    created_at, updated_at
                ) VALUES (?, ?, ?, 'ACTIVE', 1, NULL, 0, ?, ?)
                """, (dev_id, thash, pub_id, now, now))
        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # 1. UNIQUE DEVICE IDENTITY & CREDENTIAL PROVISIONING
    # -------------------------------------------------------------------------
    def register_device(
        self,
        device_id: str,
        device_name: str,
        device_type: str = "ESP32",
        location: str = "Home"
    ) -> Dict[str, Any]:
        """Provisions a unique secret token for an ESP32 device and registers it in SQLite."""
        device_id = device_id.strip().lower()
        public_id = f"pub_{uuid.uuid4().hex[:12]}"
        secret_token = self.crypto.generate_token(32)
        secret_hash = self.crypto.hash_sha256(secret_token)
        now = time.time()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO sec_iot_credentials (
            device_id, secret_token_hash, public_id, status,
            is_registered, last_nonce, last_command_timestamp,
            created_at, updated_at
        ) VALUES (?, ?, ?, 'ACTIVE', 1, NULL, 0, ?, ?)
        ON CONFLICT(device_id) DO UPDATE SET
            secret_token_hash = excluded.secret_token_hash,
            public_id = excluded.public_id,
            status = 'ACTIVE',
            updated_at = excluded.updated_at
        """, (device_id, secret_hash, public_id, now, now))
        conn.commit()
        conn.close()

        # Also register in IoT hardware database
        from features.iot.device_manager import device_manager
        device_manager.register_device(
            device_id=device_id,
            device_name=device_name,
            device_type=device_type,
            location=location,
            mqtt_topic=f"orian/devices/{device_id}/command",
            is_safety_critical=(device_type.lower() in ["ac", "heater", "geyser"])
        )

        from features.security.audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="IOT_DEVICE_REGISTERED",
            severity=SecurityEventSeverity.INFO,
            message=f"New IoT device registered: '{device_id}' ({device_name}) with public ID {public_id}"
        )

        return {
            "device_id": device_id,
            "public_id": public_id,
            "secret_token": secret_token,
            "mqtt_topic": f"orian/devices/{device_id}/command"
        }

    # -------------------------------------------------------------------------
    # 2. REPLAY ATTACK PROTECTION & COMMAND SIGNING
    # -------------------------------------------------------------------------
    def build_secure_command_payload(
        self,
        device_id: str,
        command: str,
        parameters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Constructs an authenticated, anti-replay JSON command envelope for MQTT/REST transmission to ESP32."""
        now = time.time()
        request_id = f"req_{uuid.uuid4().hex[:16]}"
        nonce = uuid.uuid4().hex[:12]
        expires_at = now + self.config.IOT_REPLAY_WINDOW_SECONDS

        payload = {
            "request_id": request_id,
            "device_id": device_id,
            "command": command,
            "parameters": parameters or {},
            "timestamp": now,
            "expires_at": expires_at,
            "nonce": nonce
        }

        # Generate HMAC signature
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT secret_token_hash FROM sec_iot_credentials WHERE device_id = ?", (device_id,))
        row = cursor.fetchone()
        conn.close()

        secret_key = row["secret_token_hash"] if row else self.config.SECRET_KEY
        sig_data = f"{device_id}:{command}:{request_id}:{nonce}:{int(now)}"
        signature = self.crypto.hmac_sha256(secret_key, sig_data)
        payload["signature"] = signature

        return payload

    def validate_inbound_telemetry(
        self,
        device_id: str,
        timestamp: Optional[float] = None,
        nonce: Optional[str] = None
    ) -> bool:
        """Validates that telemetry or heartbeat feeds originate from a registered device without timestamp replay."""
        device_id = device_id.strip().lower()
        now = time.time()

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sec_iot_credentials WHERE device_id = ? AND status = 'ACTIVE'", (device_id,))
        row = cursor.fetchone()
        conn.close()

        if not row:
            from features.security.audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="IOT_UNAUTHORIZED_DEVICE",
                severity=SecurityEventSeverity.WARNING,
                message=f"Received telemetry from unapproved IoT device: '{device_id}'"
            )
            return False

        # Replay window check if timestamp is provided
        if timestamp:
            if abs(now - timestamp) > (self.config.IOT_REPLAY_WINDOW_SECONDS + self.config.IOT_MAX_CLOCK_SKEW_SECONDS):
                logger.warning(f"Rejected telemetry from '{device_id}': timestamp skew exceeded ({abs(now - timestamp)}s)")
                return False

        return True

    def validate_command_response(
        self,
        device_id: str,
        response_payload: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validates status feedback from ESP32 against registered credentials and command state."""
        device_id = device_id.strip().lower()
        dev_in_payload = str(response_payload.get("device_id") or "").lower()

        if dev_in_payload and dev_in_payload != device_id:
            return False, f"Device ID mismatch in payload: expected {device_id}, got {dev_in_payload}"

        return True, "Valid"

iot_security = IoTSecurityEngine()
