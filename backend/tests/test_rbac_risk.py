import sys
import os
import unittest
import time

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.security.models import Role, Permission, RiskLevel, User
from features.security.rbac import rbac_engine
from features.security.risk_engine import risk_engine
from features.security.confirmation_engine import confirmation_engine
from features.security.tool_policy import tool_policy_engine
from features.security.gateway import security_gateway

class TestRBACAndRisk(unittest.TestCase):

    def setUp(self):
        self.guest = User(id="u_guest", username="guest_user", role=Role.GUEST)
        self.user = User(id="u_user", username="regular_user", role=Role.USER)
        self.trusted = User(id="u_trusted", username="trusted_user", role=Role.TRUSTED_USER)
        self.admin = User(id="u_admin", username="admin_user", role=Role.ADMIN)
        self.owner = User(id="u_owner", username="owner_user", role=Role.OWNER)

    def test_01_rbac_permission_matrix(self):
        """Tests that permissions are correctly enforced across all roles."""
        # GUEST can chat and calculate, but cannot delete files or control IoT
        self.assertTrue(rbac_engine.check_user_permission(self.guest, Permission.CHAT))
        self.assertTrue(rbac_engine.check_user_permission(self.guest, Permission.CALCULATOR))
        self.assertFalse(rbac_engine.check_user_permission(self.guest, Permission.IOT_CONTROL))
        self.assertFalse(rbac_engine.check_user_permission(self.guest, Permission.DELETE_FILE))

        # USER can read files & IoT, but cannot delete files or run self_program
        self.assertTrue(rbac_engine.check_user_permission(self.user, Permission.READ_FILE))
        self.assertTrue(rbac_engine.check_user_permission(self.user, Permission.IOT_READ))
        self.assertFalse(rbac_engine.check_user_permission(self.user, Permission.DELETE_FILE))
        self.assertFalse(rbac_engine.check_user_permission(self.user, Permission.SELF_PROGRAM))

        # TRUSTED_USER can control desktop apps and IoT, but cannot delete files
        self.assertTrue(rbac_engine.check_user_permission(self.trusted, Permission.OPEN_APPLICATION))
        self.assertTrue(rbac_engine.check_user_permission(self.trusted, Permission.IOT_CONTROL))
        self.assertFalse(rbac_engine.check_user_permission(self.trusted, Permission.DELETE_FILE))

        # ADMIN can delete files and manage system, but cannot self_program without OWNER
        self.assertTrue(rbac_engine.check_user_permission(self.admin, Permission.DELETE_FILE))
        self.assertTrue(rbac_engine.check_user_permission(self.admin, Permission.SYSTEM_CONTROL))
        self.assertFalse(rbac_engine.check_user_permission(self.admin, Permission.SELF_PROGRAM))

        # OWNER has all permissions
        for perm in Permission:
            self.assertTrue(rbac_engine.check_user_permission(self.owner, perm))

    def test_02_risk_engine_classification(self):
        """Tests that commands receive appropriate risk levels."""
        low_res = risk_engine.assess_risk("calculator", command="What is 25 * 4?")
        self.assertEqual(low_res.risk_level, RiskLevel.LOW)
        self.assertFalse(low_res.requires_confirmation)

        med_res = risk_engine.assess_risk("desktop_action", target="Notepad")
        self.assertEqual(med_res.risk_level, RiskLevel.MEDIUM)

        high_res = risk_engine.assess_risk("system_cleanup", target="Temporary Directories")
        self.assertEqual(high_res.risk_level, RiskLevel.HIGH)
        self.assertTrue(high_res.requires_confirmation)

        crit_res = risk_engine.assess_risk("security_admin", command="modify_security_gateway")
        self.assertEqual(crit_res.risk_level, RiskLevel.CRITICAL)
        self.assertTrue(crit_res.requires_confirmation)

    def test_03_confirmation_ticket_lifecycle(self):
        """Tests confirmation ticket generation, approval, and verification."""
        ticket = confirmation_engine.create_ticket(
            user_id=self.owner.id,
            action="system_cleanup",
            target="Temp Files",
            risk_level=RiskLevel.HIGH,
            command="clean temp files"
        )
        self.assertFalse(ticket.confirmed)

        # Submit approval
        approved = confirmation_engine.submit_confirmation(ticket.ticket_id, self.owner.id, approved=True)
        self.assertTrue(approved)

        updated_ticket = confirmation_engine.get_ticket(ticket.ticket_id)
        self.assertTrue(updated_ticket.confirmed)

    def test_04_gateway_secured_execution(self):
        """Tests that the Security Gateway executes allowed tools and blocks unauthorized ones."""
        # Allowed execution for owner
        calc_res = security_gateway.execute_secured(
            user=self.owner,
            tool_name="math_engine",
            tool_callable=lambda expr: {"result": 42},
            arguments={"expr": "6 * 7"}
        )
        self.assertTrue(calc_res["success"])
        self.assertEqual(calc_res["result"]["result"], 42)

        # GUEST trying to run system cleanup must be denied
        cleanup_res = security_gateway.execute_secured(
            user=self.guest,
            tool_name="system_cleanup",
            tool_callable=lambda: {"cleaned": True}
        )
        self.assertFalse(cleanup_res["success"])
        self.assertTrue(cleanup_res.get("permission_denied"))

if __name__ == "__main__":
    unittest.main()
