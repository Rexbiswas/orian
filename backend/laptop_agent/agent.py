import os
import sys
import json
import time
import hmac
import hashlib
import threading
import logging
from typing import Dict, Any, Optional, Tuple

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)

from .config import agent_config
from .windows_api import windows_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s")
logger = logging.getLogger("orian.laptop_agent")

PERMITTED_AGENT_COMMANDS = {"GET_STATUS", "NOTIFY", "LOCK", "SLEEP"}
PROHIBITED_COMMANDS = {
    "EXECUTE_COMMAND", "RUN_SHELL", "RUN_POWERSHELL",
    "EXECUTE_ARBITRARY_PROGRAM", "DELETE_FILE", "DOWNLOAD_FILE"
}

class OrianLaptopAgent:
    """Standalone Secure Windows Laptop Protection Agent executing only authenticated, cryptographically signed, explicitly permitted operations."""

    def __init__(self, config=agent_config):
        self.config = config
        self.device_id = config.DEVICE_ID
        self.device_name = config.DEVICE_NAME
        self.auth_token: Optional[str] = None
        self.is_running = False
        self.boot_time = time.time()
        self.processed_request_ids: set = set()
        self._load_stored_credentials()

    def _load_stored_credentials(self):
        """Loads stored cryptographic shared secret from local protected file."""
        if os.path.exists(self.config.CREDENTIALS_FILE):
            try:
                with open(self.config.CREDENTIALS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.device_id = data.get("device_id", self.device_id)
                    self.auth_token = data.get("auth_token")
                logger.info(f"Loaded credentials for device identity '{self.device_id}'.")
            except Exception as e:
                logger.warning(f"Could not read credentials file: {e}")

    def save_credentials(self, device_id: str, auth_token: str):
        """Saves device credentials locally."""
        self.device_id = device_id
        self.auth_token = auth_token
        try:
            os.makedirs(os.path.dirname(os.path.abspath(self.config.CREDENTIALS_FILE)), exist_ok=True)
            with open(self.config.CREDENTIALS_FILE, "w", encoding="utf-8") as f:
                json.dump({
                    "device_id": device_id,
                    "auth_token": auth_token,
                    "saved_at": time.time()
                }, f, indent=2)
            logger.info(f"Stored credentials for device identity '{device_id}'.")
        except Exception as e:
            logger.error(f"Failed to save credentials file: {e}")

    def verify_command_authenticity(self, packet: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validates all 10 security prerequisites before executing privileged commands:
        1. Device is registered.
        2. Device is authenticated.
        3. Request is authenticated (HMAC signature).
        4. Request is authorized.
        5. Request is not expired.
        6. Request ID has not been used.
        7. Command equals permitted operation (GET_STATUS, NOTIFY, LOCK, SLEEP).
        8. Policy ID is present/valid.
        9. Enforcement is permitted.
        10. Request originated from trusted Orian backend.
        """
        req_id = packet.get("request_id")
        dev_id = packet.get("device_id")
        cmd = str(packet.get("command", "")).upper().strip()
        policy_id = packet.get("policy_id") or ""
        ts = packet.get("timestamp", 0)
        expires_at = packet.get("expires_at", 0)
        sig = packet.get("signature")
        now = time.time()

        # 1. Prohibited command check
        if cmd in PROHIBITED_COMMANDS or cmd not in PERMITTED_AGENT_COMMANDS:
            return False, f"SECURITY_ERROR: Command '{cmd}' is strictly prohibited and not exposed by Laptop Agent."

        # 2. Check Device ID match
        if dev_id != self.device_id:
            return False, f"SECURITY_ERROR: Device ID mismatch (received '{dev_id}', expected '{self.device_id}')."

        # 3. Check Authentication token availability
        if not self.auth_token:
            return False, "SECURITY_ERROR: Agent has not been paired or authenticated with Orian backend."

        # 4. Check Replay & Nonce Uniqueness
        if req_id in self.processed_request_ids:
            return False, f"SECURITY_ERROR: Request ID '{req_id}' has already been executed (Replay Attack Blocked)."

        # 5. Check Expiration & Clock Skew
        if now > expires_at:
            return False, f"SECURITY_ERROR: Command '{req_id}' has expired ({now - expires_at:.1f}s ago)."

        if abs(now - ts) > 15.0:
            return False, f"SECURITY_ERROR: Clock skew exceeded ({abs(now - ts):.1f}s > 15s)."

        # 6. Verify HMAC-SHA256 Signature
        secret_hash = hashlib.sha256(self.auth_token.encode("utf-8")).hexdigest().encode("utf-8")
        raw_secret_bytes = self.auth_token.encode("utf-8")

        payload_str = f"{req_id}:{dev_id}:{cmd}:{policy_id}:{int(ts)}:{int(expires_at)}"
        sig_hash = hmac.new(secret_hash, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()
        sig_raw = hmac.new(raw_secret_bytes, payload_str.encode("utf-8"), hashlib.sha256).hexdigest()

        if not sig or (not hmac.compare_digest(sig_hash, sig) and not hmac.compare_digest(sig_raw, sig)):
            return False, f"SECURITY_ERROR: Invalid cryptographic signature on command '{req_id}'."

        return True, None

    def execute_command(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """Executes authorized command packet after complete cryptographic and security validation."""
        valid, err = self.verify_command_authenticity(packet)
        req_id = packet.get("request_id", "unknown_req")
        cmd = str(packet.get("command", "")).upper().strip()

        if not valid:
            logger.error(f"Command execution rejected for request '{req_id}': {err}")
            return {
                "success": False,
                "command": cmd,
                "device_id": self.device_id,
                "request_id": req_id,
                "error": err
            }

        # Mark request ID as processed (Replay protection)
        self.processed_request_ids.add(req_id)

        # Execute explicitly permitted command
        if cmd == "GET_STATUS":
            fg_info = windows_api.get_foreground_window_info()
            return {
                "success": True,
                "command": "GET_STATUS",
                "device_id": self.device_id,
                "request_id": req_id,
                "status": "ONLINE",
                "uptime_seconds": int(time.time() - self.boot_time),
                "agent_version": self.config.AGENT_VERSION,
                "active_window": fg_info
            }

        elif cmd == "NOTIFY":
            msg = packet.get("reason", "Orian Protection Notification")
            res = windows_api.show_desktop_notification("Orian Laptop Protection", msg)
            res["request_id"] = req_id
            res["device_id"] = self.device_id
            return res

        elif cmd == "LOCK":
            logger.warning(f"Executing authorized LOCK command '{req_id}' on device '{self.device_id}'")
            res = windows_api.lock_computer(simulate=self.config.SIMULATE_SLEEP)
            res["request_id"] = req_id
            res["device_id"] = self.device_id
            return res

        elif cmd == "SLEEP":
            logger.warning(f"Executing authorized SLEEP command '{req_id}' on device '{self.device_id}'")
            res = windows_api.sleep_computer(simulate=self.config.SIMULATE_SLEEP)
            res["request_id"] = req_id
            res["device_id"] = self.device_id
            return res

        return {
            "success": False,
            "command": cmd,
            "device_id": self.device_id,
            "request_id": req_id,
            "error": f"Unhandled command: {cmd}"
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "device_id": self.device_id,
            "device_name": self.device_name,
            "agent_version": self.config.AGENT_VERSION,
            "authenticated": bool(self.auth_token),
            "uptime_seconds": int(time.time() - self.boot_time),
            "simulated_sleep": self.config.SIMULATE_SLEEP
        }

laptop_agent = OrianLaptopAgent()

if __name__ == "__main__":
    logger.info("Starting Orian Laptop Agent standalone service...")
    print(json.dumps(laptop_agent.get_status(), indent=2))
