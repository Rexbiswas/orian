import sys
import os
import unittest
import time
from fastapi.testclient import TestClient

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from main import app
from features.security.auth_engine import auth_engine
from features.security.models import Role

class TestLaptopProtectionAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        # Authenticate owner
        self.owner_username = f"admin_{int(time.time()*1000)}"
        self.owner_user = auth_engine.register_user(
            username=self.owner_username,
            password="SecureAdminPassword2026!",
            role=Role.OWNER
        )
        token_res = auth_engine.authenticate_user(self.owner_username, "SecureAdminPassword2026!")
        self.auth_headers = {"Authorization": f"Bearer {token_res.access_token}"}
        self.device_id = f"api-laptop-{int(time.time()*1000)}"

    def test_01_device_api_registration_and_approval_flow(self):
        """API Test: /api/laptop/register -> /api/laptop/approve -> /api/laptop/heartbeat -> /api/laptop/status."""
        # 1. Register device
        reg_res = self.client.post("/api/laptop/register", json={
            "device_id": self.device_id,
            "device_name": "Executive Laptop Workstation",
            "agent_version": "1.0.0"
        })
        self.assertEqual(reg_res.status_code, 200)
        reg_data = reg_res.json()
        self.assertTrue(reg_data["success"])
        self.assertEqual(reg_data["status"], "PAIRING")
        self.assertIn("shared_secret", reg_data)

        # 2. Approve device
        app_res = self.client.post("/api/laptop/approve", json={
            "device_id": self.device_id,
            "approved": True
        }, headers=self.auth_headers)
        self.assertEqual(app_res.status_code, 200)
        self.assertTrue(app_res.json()["approved"])

        # 3. Heartbeat
        hb_res = self.client.post("/api/laptop/heartbeat", json={
            "device_id": self.device_id,
            "agent_version": "1.0.0",
            "active_app": "code.exe",
            "status": "ACTIVE"
        })
        self.assertEqual(hb_res.status_code, 200)
        self.assertTrue(hb_res.json()["success"])

        # 4. Query status
        status_res = self.client.get(f"/api/laptop/status?device_id={self.device_id}")
        self.assertEqual(status_res.status_code, 200)
        self.assertEqual(status_res.json()["device"]["status"], "ACTIVE")

    def test_02_protection_activity_and_policies_api(self):
        """API Test: /api/protection/activity, /api/protection/policies, /api/protection/dashboard."""
        # Register and approve device first
        self.client.post("/api/laptop/register", json={
            "device_id": self.device_id,
            "device_name": "Policy Test Laptop"
        })
        self.client.post("/api/laptop/approve", json={
            "device_id": self.device_id,
            "approved": True
        }, headers=self.auth_headers)

        # Start Focus Mode
        focus_res = self.client.post("/api/focus/start", json={
            "mode": "WORK",
            "schedule_start": "00:00",
            "schedule_end": "23:59",
            "schedule_days": ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
        }, headers=self.auth_headers)
        self.assertEqual(focus_res.status_code, 200)

        # Report Gaming Activity
        act_res = self.client.post("/api/protection/activity", json={
            "device_id": self.device_id,
            "application": "steam.exe",
            "process_name": "steam.exe",
            "duration_seconds": 30.0
        })
        self.assertEqual(act_res.status_code, 200)
        eval_data = act_res.json()["evaluation"]
        self.assertFalse(eval_data["allowed"])
        self.assertEqual(eval_data["action"], "WARN")
        self.assertIsNotNone(eval_data["violation_id"])

        # Submit Override
        viol_id = eval_data["violation_id"]
        override_res = self.client.post("/api/protection/override", json={
            "violation_id": viol_id,
            "reason": "Authorized break window",
            "password": "SecureAdminPassword2026!"
        }, headers=self.auth_headers)
        self.assertEqual(override_res.status_code, 200)
        self.assertTrue(override_res.json()["overridden"])

        # Fetch Dashboard
        dash_res = self.client.get("/api/protection/dashboard")
        self.assertEqual(dash_res.status_code, 200)
        dash_data = dash_res.json()
        self.assertTrue(dash_data["success"])
        self.assertIn("metrics", dash_data)
        self.assertTrue(dash_data["metrics"]["overrides_today"] >= 1)

    def test_03_laptop_command_and_ack_api(self):
        """API Test: /api/laptop/command -> /api/laptop/command/ack."""
        self.client.post("/api/laptop/register", json={
            "device_id": self.device_id,
            "device_name": "Command Test Laptop"
        })
        self.client.post("/api/laptop/approve", json={
            "device_id": self.device_id,
            "approved": True
        }, headers=self.auth_headers)

        # Dispatch signed command
        cmd_res = self.client.post("/api/laptop/command", json={
            "device_id": self.device_id,
            "command": "GET_STATUS",
            "reason": "Health check query"
        }, headers=self.auth_headers)
        self.assertEqual(cmd_res.status_code, 200)
        pkt = cmd_res.json()["command_packet"]
        self.assertEqual(pkt["command"], "GET_STATUS")
        self.assertIn("signature", pkt)

        # Acknowledge command execution
        ack_res = self.client.post("/api/laptop/command/ack", json={
            "request_id": pkt["request_id"],
            "success": True,
            "result_message": "Agent online and healthy"
        })
        self.assertEqual(ack_res.status_code, 200)
        self.assertTrue(ack_res.json()["success"])

if __name__ == "__main__":
    unittest.main()
