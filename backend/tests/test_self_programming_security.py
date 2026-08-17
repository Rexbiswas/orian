import sys
import os
import unittest

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.security.models import Role, User
from features.security.self_programming_guard import self_programming_guard
from features.neural.self_programmer import self_programmer

class TestSelfProgrammingSecurity(unittest.TestCase):

    def setUp(self):
        self.owner = User(id="u_owner", username="owner_dev", role=Role.OWNER)
        self.user = User(id="u_user", username="regular_user", role=Role.USER)

    def test_01_protected_files_policy_enforcement(self):
        """Tests that protected security files cannot be targeted by self-programming."""
        protected_paths = [
            "backend/features/security/gateway.py",
            "backend/features/security/auth_engine.py",
            ".env",
            "orian_storage/orian_core.db"
        ]

        for p in protected_paths:
            self.assertTrue(self_programming_guard.is_protected_file(p))
            with self.assertRaises(PermissionError):
                self_programming_guard.validate_modification_request(
                    user=self.owner,
                    target_files=[p]
                )

    def test_02_ast_static_analysis_safety_rules(self):
        """Tests that dangerous code constructs (eval, exec, __import__) are rejected by AST analysis."""
        # Safe code
        safe_code = """
def calculate_area(width, height):
    return width * height
"""
        is_safe, err = self_programming_guard.validate_code_safety(safe_code)
        self.assertTrue(is_safe)
        self.assertIsNone(err)

        # Unsafe code with eval
        unsafe_eval = """
def run_command(user_input):
    return eval(user_input)
"""
        is_safe, err = self_programming_guard.validate_code_safety(unsafe_eval)
        self.assertFalse(is_safe)
        self.assertIn("eval", err)

        # Unsafe code with exec
        unsafe_exec = """
def execute_payload(payload):
    exec(payload)
"""
        is_safe, err = self_programming_guard.validate_code_safety(unsafe_exec)
        self.assertFalse(is_safe)
        self.assertIn("exec", err)

    def test_03_non_owner_role_rejection(self):
        """Tests that non-OWNER users cannot trigger self-programming."""
        with self.assertRaises(PermissionError):
            self_programming_guard.validate_modification_request(
                user=self.user,
                target_files=["backend/features/tools/math_engine.py"]
            )

    def test_04_git_snapshot_and_audit(self):
        """Tests Git checkpoint creation and self-repair audit log."""
        snapshot = self_programmer.create_git_snapshot()
        self.assertTrue(len(snapshot) > 0)

        report = self_programmer.run_self_improvement("Inspect codebase AST syntax")
        self.assertTrue(report["success"])
        self.assertEqual(report["action"], "SELF_PROGRAMMING")
        self.assertTrue(report["audit"]["syntax_valid"])

if __name__ == "__main__":
    unittest.main()
