import sys
import os
import unittest
import time
import json
import uuid

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
    laptop_command_gateway, laptop_protection_service, orian_notification_service,
    DeviceStatus, ProductivityCategory, SecurityCategory,
    EnforcementAction, ProtectionRiskLevel, FocusMode, RuleType,
    MobileAlertCategory, ProductivityPolicy, ActivityRule, MobileDevice
)
from features.security.models import User, Role
from features.security.audit_logger import audit_logger
from laptop_agent.agent import OrianLaptopAgent
from laptop_agent.config import LaptopAgentConfig

class TestProtectionEndToEndScenario(unittest.TestCase):

    def setUp(self):
        self.owner = User(id="u_owner_e2e", username="orian_owner", role=Role.OWNER)
        orian_policy_engine.set_master_protection(True)
        orian_policy_engine.set_automatic_sleep(True)

    def test_complete_19_step_protection_lifecycle_scenario(self):
        """Tests the full 19-step End-to-End Scenario:
        1. Register laptop.
        2. Register mobile.
        3. Authenticate / Approve both.
        4. Enable Focus Mode.
        5. Configure a blocked application.
        6. Open the application (ingest activity report).
        7. Activity Monitor detects it.
        8. Policy Engine evaluates it.
        9. Risk Engine calculates risk.
        10. Windows warning appears.
        11. Mobile alert is generated.
        12. Mobile receives notification.
        13. User does not override.
        14. Grace period expires.
        15. Security Gateway authorizes action.
        16. Laptop Agent receives authenticated SLEEP.
        17. Windows enters sleep (simulated).
        18. Mobile receives: "Automatic Sleep Executed."
        19. Audit event is recorded.
        """
        # Step 1: Register Laptop
        lap_id = f"lap-e2e-{uuid.uuid4().hex[:8]}"
        lap_dev, lap_secret = laptop_device_manager.initiate_pairing(
            device_id=lap_id,
            device_name="Owner Windows Laptop Workstation",
            agent_version="1.0.0",
            owner_id=self.owner.id
        )
        self.assertEqual(lap_dev.status, DeviceStatus.PAIRING)

        # Step 2: Register Mobile
        mob_id = f"mob-e2e-{uuid.uuid4().hex[:8]}"
        mob_dev = MobileDevice(
            device_id=mob_id,
            device_name="Owner iPhone 16 Pro",
            owner_id=self.owner.id,
            auth_token_hash="mob_hash_secret_123",
            status=DeviceStatus.PAIRING,
            pairing_code="PAIR-998877"
        )
        protection_db.register_mobile_device(mob_dev)

        # Step 3: Authenticate & Approve Both
        laptop_device_manager.approve_device(lap_id, approved=True, owner_id=self.owner.id)
        self.assertTrue(laptop_device_manager.is_device_active(lap_id))

        protection_db.update_mobile_device_status(mob_id, status=DeviceStatus.ACTIVE)
        active_mob = protection_db.get_mobile_device(mob_id)
        self.assertEqual(active_mob.status, DeviceStatus.ACTIVE)

        # Initialize Agent Client with paired credentials
        agent_cfg = LaptopAgentConfig(DEVICE_ID=lap_id, SIMULATE_SLEEP=True)
        agent = OrianLaptopAgent(config=agent_cfg)
        agent.save_credentials(lap_id, lap_secret)

        # Step 4: Enable Focus Mode
        focus_session = focus_manager.start_focus(mode=FocusMode.WORK, user_id=self.owner.id)
        self.assertTrue(focus_manager.is_focus_active_now())

        # Step 5: Configure a Blocked Application Policy
        policy_id = f"pol_e2e_game_{uuid.uuid4().hex[:6]}"
        test_policy = ProductivityPolicy(
            policy_id=policy_id,
            category=ProductivityCategory.GAMING,
            name="Block Gaming During Focus",
            enabled=True,
            focus_only=True,
            min_duration_seconds=0,
            max_violations_before_escalation=1,
            default_action=EnforcementAction.WARN,
            escalation_action=EnforcementAction.SLEEP,
            grace_period_seconds=1,  # Short grace period for deterministic testing
            risk_level=ProtectionRiskLevel.MEDIUM,
            match_apps=["cyberpunk2077.exe", "steam.exe"]
        )
        protection_db.save_productivity_policy(test_policy)

        # Step 6 & 7: Open Application / Ingest Activity Report
        eval_payload = laptop_protection_service.process_activity_report(
            device_id=lap_id,
            application="Cyberpunk 2077",
            process_name="cyberpunk2077.exe",
            duration_seconds=125.0,
            window_title="Cyberpunk 2077 (Focus Mode Violation)"
        )

        # Step 8 & 9: Policy Engine evaluates & Risk Engine calculates risk
        self.assertFalse(eval_payload["allowed"])
        self.assertEqual(eval_payload["action"], "WARN")
        self.assertEqual(eval_payload["risk_level"], "MEDIUM")
        violation_id = eval_payload["violation_id"]
        self.assertIsNotNone(violation_id)

        # Step 10: Local Windows warning issued
        violation = protection_db.get_active_violation(violation_id)
        self.assertIsNotNone(violation)
        self.assertEqual(violation.status, "WARNED")

        # Step 11 & 12: Mobile Alert is generated and received
        notif_events = protection_db.list_notification_events(limit=5)
        self.assertTrue(len(notif_events) > 0)
        matching_notif = next((n for n in notif_events if n.activity == "cyberpunk2077.exe"), None)
        self.assertIsNotNone(matching_notif)
        self.assertEqual(matching_notif.type, MobileAlertCategory.PRODUCTIVITY_WARNING)

        # Step 13 & 14: User does not override -> Grace period expires
        # Trigger grace expiration callback directly
        laptop_protection_service._on_grace_period_expired(violation_id, lap_id, EnforcementAction.SLEEP)

        # Step 15: Security Gateway authorizes action & generates signed SLEEP command
        updated_viol = protection_db.get_active_violation(violation_id)
        self.assertEqual(updated_viol.status, "ENFORCED")

        signed_cmd = laptop_command_gateway.generate_signed_command(
            device_id=lap_id,
            command="SLEEP",
            policy_id=policy_id,
            reason="GRACE_PERIOD_EXPIRED_ENFORCEMENT"
        )
        self.assertEqual(signed_cmd.command, "SLEEP")
        self.assertIsNotNone(signed_cmd.signature)

        # Step 16 & 17: Laptop Agent receives authenticated SLEEP and enters sleep
        agent_exec_res = agent.execute_command(signed_cmd.model_dump())
        self.assertTrue(agent_exec_res["success"])
        self.assertEqual(agent_exec_res["command"], "SLEEP")
        self.assertTrue(agent_exec_res.get("simulated", False) or agent_exec_res.get("status") == "SUSPEND_STATE_TRIGGERED")

        # Step 18: Mobile receives "Automatic Sleep Executed" alert
        all_notifs = protection_db.list_notification_events(limit=10)
        sleep_notif = next((n for n in all_notifs if n.type == MobileAlertCategory.AUTOMATIC_SLEEP and n.device_id == lap_id), None)
        self.assertIsNotNone(sleep_notif)
        self.assertEqual(sleep_notif.action, "Laptop sent to sleep")

        # Step 19: Audit event is recorded
        audit_logs = audit_logger.query_audit_logs(limit=25)
        self.assertTrue(any("MOBILE_ALERT" in a["action"] or "POLICY_WARNING" in a["action"] for a in audit_logs))

if __name__ == "__main__":
    unittest.main()
