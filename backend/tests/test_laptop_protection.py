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
    EnforcementAction, ProtectionRiskLevel, FocusMode, RuleType,
    ProductivityPolicy, ActivityRule
)
from features.security.models import User, Role
from laptop_agent.agent import OrianLaptopAgent
from laptop_agent.config import LaptopAgentConfig

class TestLaptopProtection(unittest.TestCase):

    def setUp(self):
        self.owner = User(id="u_owner", username="orian_admin", role=Role.OWNER)
        self.test_dev_id = f"test-laptop-{int(time.time()*1000)}"
        orian_policy_engine.set_master_protection(True)
        orian_policy_engine.set_automatic_sleep(True)

    def test_01_device_registration_and_pairing_lifecycle(self):
        """Tests device registration state machine: UNREGISTERED -> PAIRING -> OWNER APPROVAL -> ACTIVE."""
        # 1. Initiate pairing
        dev, secret = laptop_device_manager.initiate_pairing(
            device_id=self.test_dev_id,
            device_name="Test Laptop Workstation",
            agent_version="1.0.0",
            owner_id=self.owner.id
        )
        self.assertEqual(dev.device_id, self.test_dev_id)
        self.assertEqual(dev.status, DeviceStatus.PAIRING)
        self.assertTrue(dev.pairing_code.startswith("PAIR-"))
        self.assertFalse(laptop_device_manager.is_device_active(self.test_dev_id))

        # 2. Owner approves pairing
        approved = laptop_device_manager.approve_device(self.test_dev_id, approved=True, owner_id=self.owner.id)
        self.assertTrue(approved)
        self.assertTrue(laptop_device_manager.is_device_active(self.test_dev_id))

        # 3. Heartbeat
        hb = laptop_device_manager.heartbeat(self.test_dev_id, agent_version="1.0.0", metadata={"active_app": "code.exe"})
        self.assertTrue(hb)

    def test_02_device_revocation(self):
        """Tests device revocation and immediate rejection of privileged commands."""
        dev_id = f"revoke-dev-{int(time.time()*1000)}"
        dev, secret = laptop_device_manager.initiate_pairing(dev_id, "Revocable Laptop", owner_id=self.owner.id)
        laptop_device_manager.approve_device(dev_id, approved=True, owner_id=self.owner.id)
        self.assertTrue(laptop_device_manager.is_device_active(dev_id))

        # Revoke device
        revoked = laptop_device_manager.revoke_device(dev_id, reason="Security audit", owner_id=self.owner.id)
        self.assertTrue(revoked)
        self.assertFalse(laptop_device_manager.is_device_active(dev_id))

        # Cannot generate signed command for revoked device
        with self.assertRaises(PermissionError):
            laptop_command_gateway.generate_signed_command(
                device_id=dev_id,
                command="SLEEP",
                reason="Test"
            )

    def test_03_whitelist_priority_evaluation(self):
        """Tests that developer tools and programming environments are whitelisted and never penalized."""
        whitelisted_apps = [
            "code.exe", "python.exe", "pythonw.exe", "git.exe",
            "node.exe", "studio64.exe", "notepad.exe", "docker.exe"
        ]

        for app in whitelisted_apps:
            eval_res = orian_policy_engine.evaluate_activity(
                device_id=self.test_dev_id,
                application=app,
                process_name=app,
                duration_seconds=3600.0  # Even after 1 hour of continuous use
            )
            self.assertTrue(eval_res.allowed, f"App '{app}' should be allowed under ALWAYS_ALLOWED whitelist")
            self.assertEqual(eval_res.action, EnforcementAction.LOG)
            self.assertEqual(eval_res.risk_level, ProtectionRiskLevel.LOW)

    def test_04_cybersecurity_lab_whitelist(self):
        """Tests that security research in authorized lab networks is explicitly whitelisted."""
        lab_targets = ["localhost", "127.0.0.1", "10.0.1.5", "192.168.1.100", "testlab.local"]

        for target in lab_targets:
            self.assertTrue(activity_whitelist.is_authorized_security_lab(target))

            eval_res = orian_policy_engine.evaluate_activity(
                device_id=self.test_dev_id,
                application="nmap.exe",
                process_name="nmap.exe",
                domain=target,
                security_signal={"type": "UNAUTHORIZED_HACKING", "target_network": target}
            )
            self.assertTrue(eval_res.allowed)
            self.assertEqual(eval_res.action, EnforcementAction.LOG)

    def test_05_focus_mode_schedules_and_state(self):
        """Tests focus mode state management and schedule evaluation."""
        # Start focus mode WORK
        session = focus_manager.start_focus(
            mode=FocusMode.WORK,
            schedule_start="00:00",
            schedule_end="23:59",
            schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"],
            user_id="test_user"
        )
        self.assertTrue(session.is_active)
        self.assertTrue(focus_manager.is_focus_active_now())

        status = focus_manager.get_status()
        self.assertTrue(status["active"])
        self.assertEqual(status["mode"], "WORK")

        # Stop focus mode
        focus_manager.stop_focus(user_id="test_user")
        self.assertFalse(focus_manager.is_focus_active_now())

    def test_06_productivity_gaming_policy_evaluation(self):
        """Tests gaming detection during active focus mode."""
        # Activate Focus Mode
        focus_manager.start_focus(
            mode=FocusMode.WORK,
            schedule_start="00:00",
            schedule_end="23:59",
            schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        )

        eval_res = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="steam.exe",
            process_name="steam.exe",
            duration_seconds=60.0
        )
        self.assertFalse(eval_res.allowed)
        self.assertEqual(eval_res.category, "GAMING")
        self.assertEqual(eval_res.action, EnforcementAction.WARN)
        self.assertEqual(eval_res.risk_level, ProtectionRiskLevel.MEDIUM)
        self.assertEqual(eval_res.grace_period_seconds, 10)

    def test_07_terminal_duration_protection(self):
        """Tests that terminal usage is ignored for brief durations (<30s) and logged up to threshold (>120s)."""
        focus_manager.start_focus(mode=FocusMode.WORK, schedule_start="00:00", schedule_end="23:59", schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])

        # 1. Terminal open for 15s -> Ignored / Allowed
        eval_brief = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="powershell.exe",
            process_name="powershell.exe",
            duration_seconds=15.0
        )
        self.assertTrue(eval_brief.allowed)
        self.assertEqual(eval_brief.action, EnforcementAction.LOG)

        # 2. Terminal open for 60s (< 120s policy threshold) -> Logged / Allowed
        eval_mid = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="powershell.exe",
            process_name="powershell.exe",
            duration_seconds=60.0
        )
        self.assertTrue(eval_mid.allowed)
        self.assertEqual(eval_mid.action, EnforcementAction.LOG)

        # 3. Terminal open for 150s (> 120s policy threshold) -> Triggers WARN
        eval_long = orian_policy_engine.evaluate_activity(
            device_id=self.test_dev_id,
            application="powershell.exe",
            process_name="powershell.exe",
            duration_seconds=150.0
        )
        self.assertFalse(eval_long.allowed)
        self.assertEqual(eval_long.action, EnforcementAction.WARN)

    def test_08_violation_escalation_ladder(self):
        """Tests violation escalation from WARN -> WARN -> BLOCK -> SLEEP."""
        policy = protection_db.get_productivity_policy("gaming-focus")
        self.assertIsNotNone(policy)

        # 1st violation
        r1, a1, _ = protection_risk_engine.assess_productivity_risk(policy, 60.0, 0)
        self.assertEqual(a1, EnforcementAction.WARN)

        # 2nd violation
        r2, a2, _ = protection_risk_engine.assess_productivity_risk(policy, 60.0, 1)
        self.assertEqual(a2, EnforcementAction.WARN)

        # 3rd violation
        r3, a3, _ = protection_risk_engine.assess_productivity_risk(policy, 60.0, 2)
        self.assertEqual(a3, EnforcementAction.BLOCK)

        # 4th violation -> SLEEP
        r4, a4, _ = protection_risk_engine.assess_productivity_risk(policy, 60.0, 3)
        self.assertEqual(a4, EnforcementAction.SLEEP)

    def test_09_warning_grace_period_and_owner_override(self):
        """Tests end-to-end warning issuance, grace period tracking, and owner override."""
        focus_manager.start_focus(mode=FocusMode.WORK, schedule_start="00:00", schedule_end="23:59", schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        dev_id = f"override-dev-{int(time.time()*1000)}"
        laptop_device_manager.initiate_pairing(dev_id, "Override Laptop", owner_id=self.owner.id)
        laptop_device_manager.approve_device(dev_id, approved=True, owner_id=self.owner.id)

        # Trigger activity report
        report_res = laptop_protection_service.process_activity_report(
            device_id=dev_id,
            application="valorant.exe",
            process_name="valorant.exe",
            duration_seconds=60.0
        )

        self.assertFalse(report_res["allowed"])
        self.assertEqual(report_res["action"], "WARN")
        self.assertIsNotNone(report_res["violation_id"])
        violation_id = report_res["violation_id"]

        # Check violation in DB
        viol = protection_db.get_active_violation(violation_id)
        self.assertIsNotNone(viol)
        self.assertEqual(viol.status, "WARNED")

        # Owner submits override
        success = laptop_protection_service.submit_owner_override(
            violation_id=violation_id,
            user=self.owner,
            reason="Authorized gaming test session"
        )
        self.assertTrue(success)

        # Violation should now be OVERRIDDEN
        updated_viol = protection_db.get_active_violation(violation_id)
        self.assertEqual(updated_viol.status, "OVERRIDDEN")
        self.assertTrue(updated_viol.overridden)

    def test_10_cancel_violation_on_activity_stopped(self):
        """Tests that enforcement is cancelled if the user stops offending activity during grace period."""
        focus_manager.start_focus(mode=FocusMode.WORK, schedule_start="00:00", schedule_end="23:59", schedule_days=["mon", "tue", "wed", "thu", "fri", "sat", "sun"])
        dev_id = f"stop-dev-{int(time.time()*1000)}"
        laptop_device_manager.initiate_pairing(dev_id, "Stop Test Laptop", owner_id=self.owner.id)
        laptop_device_manager.approve_device(dev_id, approved=True, owner_id=self.owner.id)

        report_res = laptop_protection_service.process_activity_report(
            device_id=dev_id,
            application="csgo.exe",
            process_name="csgo.exe",
            duration_seconds=60.0
        )
        viol_id = report_res["violation_id"]
        self.assertIsNotNone(viol_id)

        # Activity stopped
        cancelled = laptop_protection_service.cancel_violation_if_activity_stopped(viol_id)
        self.assertTrue(cancelled)

        viol = protection_db.get_active_violation(viol_id)
        self.assertEqual(viol.status, "CANCELLED")

    def test_11_command_gateway_and_laptop_agent_execution(self):
        """Tests cryptographic command signing and controlled laptop agent execution."""
        dev_id = f"agent-dev-{int(time.time()*1000)}"
        dev, secret = laptop_device_manager.initiate_pairing(dev_id, "Agent Execution Laptop", owner_id=self.owner.id)
        laptop_device_manager.approve_device(dev_id, approved=True, owner_id=self.owner.id)

        # Configure local agent instance
        cfg = LaptopAgentConfig(DEVICE_ID=dev_id, SIMULATE_SLEEP=True)
        agent = OrianLaptopAgent(config=cfg)
        agent.save_credentials(dev_id, secret)

        # 1. Issue signed GET_STATUS command
        cmd_status = laptop_command_gateway.generate_signed_command(
            device_id=dev_id,
            command="GET_STATUS",
            reason="Status query"
        )
        res_status = agent.execute_command(cmd_status.model_dump())
        self.assertTrue(res_status["success"])
        self.assertEqual(res_status["command"], "GET_STATUS")

        # 2. Issue signed LOCK command
        cmd_lock = laptop_command_gateway.generate_signed_command(
            device_id=dev_id,
            command="LOCK",
            reason="Workstation lock test"
        )
        res_lock = agent.execute_command(cmd_lock.model_dump())
        self.assertTrue(res_lock["success"])
        self.assertEqual(res_lock["command"], "LOCK")

        # 3. Issue signed SLEEP command
        cmd_sleep = laptop_command_gateway.generate_signed_command(
            device_id=dev_id,
            command="SLEEP",
            policy_id="gaming-focus",
            reason="Productivity Enforcement"
        )
        res_sleep = agent.execute_command(cmd_sleep.model_dump())
        self.assertTrue(res_sleep["success"])
        self.assertEqual(res_sleep["command"], "SLEEP")
        self.assertEqual(res_sleep["device_id"], dev_id)

if __name__ == "__main__":
    unittest.main()
