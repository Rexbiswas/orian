import sys
import os
import unittest
import time
import json
import hmac
import hashlib

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.protection import (
    protection_db, activity_whitelist, focus_manager,
    protection_risk_engine, orian_policy_engine, laptop_device_manager,
    laptop_command_gateway, laptop_protection_service,
    DeviceStatus, ProductivityCategory, SecurityCategory,
    EnforcementAction, ProtectionRiskLevel, FocusMode
)
from features.security.models import User, Role
from features.security.self_programming_guard import self_programming_guard
from laptop_agent.agent import OrianLaptopAgent
from laptop_agent.config import LaptopAgentConfig

class TestProtectionSecurity(unittest.TestCase):

    def setUp(self):
        self.owner = User(id="u_owner", username="orian_admin", role=Role.OWNER)
        self.attacker = User(id="u_attacker", username="malicious_guest", role=Role.GUEST)
        self.test_dev_id = f"sec-dev-{int(time.time()*1000)}"
        dev, self.secret = laptop_device_manager.initiate_pairing(self.test_dev_id, "Sec Test Laptop", owner_id=self.owner.id)
        laptop_device_manager.approve_device(self.test_dev_id, approved=True, owner_id=self.owner.id)

        cfg = LaptopAgentConfig(DEVICE_ID=self.test_dev_id, SIMULATE_SLEEP=True)
        self.agent = OrianLaptopAgent(config=cfg)
        self.agent.save_credentials(self.test_dev_id, self.secret)

    def test_01_unauthenticated_sleep_request_rejection(self):
        """Security Test: Unauthenticated or unsigned SLEEP packet must be rejected."""
        unauthenticated_packet = {
            "request_id": "cmd_attacker_fake_001",
            "device_id": self.test_dev_id,
            "command": "SLEEP",
            "policy_id": "none",
            "timestamp": time.time(),
            "expires_at": time.time() + 10,
            "signature": None  # No signature
        }

        res = self.agent.execute_command(unauthenticated_packet)
        self.assertFalse(res["success"])
        self.assertIn("SECURITY_ERROR", res["error"])

    def test_02_tampered_signature_rejection(self):
        """Security Test: Modified command payload or altered HMAC signature must be rejected."""
        valid_cmd = laptop_command_gateway.generate_signed_command(
            device_id=self.test_dev_id,
            command="SLEEP",
            reason="Valid command"
        )
        packet = valid_cmd.model_dump()

        # Attacker tampers with signature
        packet["signature"] = "deadbeef" * 8

        res = self.agent.execute_command(packet)
        self.assertFalse(res["success"])
        self.assertIn("Invalid cryptographic signature", res["error"])

    def test_03_replay_attack_prevention(self):
        """Security Test: Replaying a previously executed SLEEP command must be strictly blocked."""
        valid_cmd = laptop_command_gateway.generate_signed_command(
            device_id=self.test_dev_id,
            command="SLEEP",
            reason="Legitimate first execution"
        )
        packet = valid_cmd.model_dump()

        # 1st Execution -> Succeeds
        res1 = self.agent.execute_command(packet)
        self.assertTrue(res1["success"])

        # 2nd Replay Attempt -> Blocked by nonce uniqueness
        res2 = self.agent.execute_command(packet)
        self.assertFalse(res2["success"])
        self.assertIn("Replay Attack Blocked", res2["error"])

    def test_04_expired_command_rejection(self):
        """Security Test: Expired command packet must be rejected."""
        now = time.time()
        expired_packet = {
            "request_id": f"cmd_exp_{int(now)}",
            "device_id": self.test_dev_id,
            "command": "SLEEP",
            "policy_id": "test",
            "timestamp": now - 30.0,
            "expires_at": now - 15.0,  # Expired 15s ago
            "signature": "some_sig"
        }

        res = self.agent.execute_command(expired_packet)
        self.assertFalse(res["success"])
        self.assertIn("expired", res["error"].lower())

    def test_05_clock_skew_rejection(self):
        """Security Test: Command packet with future or excessive clock skew must be rejected."""
        now = time.time()
        skewed_packet = {
            "request_id": f"cmd_skew_{int(now)}",
            "device_id": self.test_dev_id,
            "command": "SLEEP",
            "policy_id": "test",
            "timestamp": now + 60.0,  # 60s into the future
            "expires_at": now + 75.0,
            "signature": "some_sig"
        }

        res = self.agent.execute_command(skewed_packet)
        self.assertFalse(res["success"])
        self.assertIn("clock skew", res["error"].lower())

    def test_06_prohibited_arbitrary_commands_rejection(self):
        """Security Test: Attempting to execute unexposed arbitrary commands (EXECUTE_COMMAND, RUN_SHELL, etc.) must fail."""
        prohibited_commands = [
            "EXECUTE_COMMAND", "RUN_SHELL", "RUN_POWERSHELL",
            "EXECUTE_ARBITRARY_PROGRAM", "DELETE_FILE", "DOWNLOAD_FILE",
            "FORMAT_DRIVE", "SPAWN_PROCESS"
        ]

        for bad_cmd in prohibited_commands:
            bad_packet = {
                "request_id": f"cmd_bad_{int(time.time()*1000)}",
                "device_id": self.test_dev_id,
                "command": bad_cmd,
                "timestamp": time.time(),
                "expires_at": time.time() + 15,
                "signature": "sig"
            }

            res = self.agent.execute_command(bad_packet)
            self.assertFalse(res["success"])
            self.assertIn("prohibited", res["error"].lower())

            # Command Gateway also rejects generating signed packet
            with self.assertRaises(ValueError):
                laptop_command_gateway.generate_signed_command(
                    device_id=self.test_dev_id,
                    command=bad_cmd
                )

    def test_07_security_tampering_critical_detection(self):
        """Security Test: Unauthorized attempts to disable security or kill agent trigger CRITICAL response."""
        eval_res = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="taskkill.exe",
            process_name="taskkill.exe",
            security_signal={"type": "SECURITY_TAMPERING", "action": "attempt_kill_orian_agent"}
        )

        self.assertFalse(eval_res.allowed)
        self.assertEqual(eval_res.category, "SECURITY_TAMPERING")
        self.assertEqual(eval_res.risk_level, ProtectionRiskLevel.CRITICAL)
        self.assertEqual(eval_res.action, EnforcementAction.BLOCK)

    def test_08_protected_data_access_critical_detection(self):
        """Security Test: Attempts to extract credentials or access protected keys trigger CRITICAL."""
        eval_res = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="credential_stealer.exe",
            process_name="credential_stealer.exe",
            security_signal={"type": "PROTECTED_DATA_ACCESS", "target": "sec_users"}
        )

        self.assertFalse(eval_res.allowed)
        self.assertEqual(eval_res.category, "PROTECTED_DATA_ACCESS")
        self.assertEqual(eval_res.risk_level, ProtectionRiskLevel.CRITICAL)
        self.assertEqual(eval_res.action, EnforcementAction.BLOCK)

    def test_09_unauthorized_override_rejection(self):
        """Security Test: Non-owner / guest users cannot override policy violations."""
        focus_manager.start_focus(mode=FocusMode.WORK, schedule_start="00:00", schedule_end="23:59", schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        report = laptop_protection_service.process_activity_report(
            device_id=self.test_dev_id,
            application="steam.exe",
            process_name="steam.exe",
            duration_seconds=60.0
        )
        viol_id = report["violation_id"]

        with self.assertRaises(PermissionError):
            laptop_protection_service.submit_owner_override(
                violation_id=viol_id,
                user=self.attacker,
                reason="Attacker trying to bypass policy"
            )

    def test_10_self_programming_protection_boundaries(self):
        """Security Test: Self-programming subsystem cannot modify protection or laptop agent code."""
        protected_paths = [
            "backend/features/protection/policy_engine.py",
            "backend/features/protection/command_gateway.py",
            "backend/features/protection/device_manager.py",
            "backend/laptop_agent/agent.py",
            "backend/laptop_agent/windows_api.py"
        ]

        for path in protected_paths:
            self.assertTrue(self_programming_guard.is_protected_file(path), f"Path '{path}' must be protected from self-programming")
            with self.assertRaises(PermissionError):
                self_programming_guard.validate_modification_request(
                    user=self.owner,
                    target_files=[path]
                )

    def test_11_fail_safe_behavior(self):
        """Security Test: Expired, disconnected, or malformed requests never cause automatic sleep."""
        # Unpaired / unknown device
        unknown_packet = {
            "request_id": "cmd_unknown_999",
            "device_id": "unknown-phantom-laptop",
            "command": "SLEEP",
            "timestamp": time.time(),
            "expires_at": time.time() + 15,
            "signature": "dummy"
        }
        res = self.agent.execute_command(unknown_packet)
        self.assertFalse(res["success"])

if __name__ == "__main__":
    unittest.main()
