import sys
import os

for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

import unittest
import time
from planner.intent_detector import intent_detector, IntentCategory
from execution.app_resolver import app_resolver
from tools.system_cleanup import system_cleanup
from tools.math_engine import math_engine
from planner.real_world_reasoner import real_world_reasoner
from neural.self_diagnostic import self_diagnostic
from neural.self_programmer import self_programmer
from tools.tool_router import tool_router

class TestOrianAIUpgrade(unittest.TestCase):
    """Automated Test Suite for Orian AI Universal Command Execution, Reasoning & Self-Programming Upgrade."""

    def test_01_intent_detection(self):
        print("\n[TEST 1] Testing Intent Classification Engine...")
        intent_app, _, _ = intent_detector.detect_intent("Open Notepad")
        self.assertEqual(intent_app, IntentCategory.DESKTOP_ACTION)

        intent_cleanup, _, _ = intent_detector.detect_intent("Clear temp files")
        self.assertEqual(intent_cleanup, IntentCategory.SYSTEM_CLEANUP)

        intent_math, _, meta = intent_detector.detect_intent("Calculate 2 + 2")
        self.assertEqual(intent_math, IntentCategory.SIMPLE_CALCULATION)
        self.assertIn("2 + 2", meta.get("expression", ""))

        intent_adv_math, _, _ = intent_detector.detect_intent("Find the derivative of x^2")
        self.assertEqual(intent_adv_math, IntentCategory.ADVANCED_MATHEMATICS)

        intent_diag, _, _ = intent_detector.detect_intent("Check yourself for errors")
        self.assertEqual(intent_diag, IntentCategory.SELF_DIAGNOSTIC)

        intent_prog, _, _ = intent_detector.detect_intent("Fix yourself and improve code")
        self.assertEqual(intent_prog, IntentCategory.SELF_PROGRAMMING)
        print("  [OK] Intent Detection Passed 100%.")

    def test_02_desktop_software_control(self):
        print("\n[TEST 2] Testing Application Discovery & Launch...")
        resolved = app_resolver.resolve_app("notepad")
        self.assertIsNotNone(resolved, "Notepad executable could not be resolved.")
        print(f"  [OK] Resolved Notepad Path: {resolved}")

        # Test launch
        launch_res = app_resolver.launch_app("notepad")
        self.assertTrue(launch_res["success"])
        self.assertIn("pid", launch_res)
        print(f"  [OK] Launched Notepad PID: {launch_res['pid']}")

        time.sleep(1.0)
        # Test close
        close_res = app_resolver.close_app("notepad")
        self.assertTrue(close_res["success"])
        print(f"  [OK] Closed Notepad Process(es): {close_res.get('count', 1)}")

    def test_03_system_cleanup(self):
        print("\n[TEST 3] Testing Temporary File Cleanup Engine...")
        res = system_cleanup.clear_temp_files()
        self.assertTrue(res["success"])
        self.assertIn("space_recovered", res)
        print(f"  [OK] Cleanup Summary: {res['space_recovered']} recovered across {res['files_scanned']} scanned files.")

    def test_04_mathematics_engine(self):
        print("\n[TEST 4] Testing Simple & Advanced Mathematics Engine...")
        # Simple Math AST
        res_simple = math_engine.evaluate_simple("25 * 4")
        self.assertTrue(res_simple["success"])
        self.assertEqual(res_simple["result"], 100)
        print(f"  [OK] AST Simple Math: 25 * 4 = {res_simple['result']}")

        res_sqrt = math_engine.evaluate_simple("sqrt(144)")
        self.assertTrue(res_sqrt["success"])
        self.assertEqual(res_sqrt["result"], 12)
        print(f"  [OK] AST Simple Math: sqrt(144) = {res_sqrt['result']}")

        # Advanced Math SymPy
        res_adv = math_engine.evaluate_advanced("derivative of x^2")
        self.assertTrue(res_adv["success"])
        self.assertIn("2*x", res_adv["result"])
        print(f"  [OK] SymPy Advanced Calculus: {res_adv['result']}")

    def test_05_real_world_reasoning(self):
        print("\n[TEST 5] Testing Real-World Reasoning Pipeline...")
        res = real_world_reasoner.solve_problem("My laptop is running slowly. What should I check?")
        self.assertTrue(res["success"])
        self.assertTrue(len(res["solutions"]) > 0)
        print(f"  [OK] Generated {len(res['solutions'])} structured action steps for real-world problem.")

    def test_06_self_diagnostics(self):
        print("\n[TEST 6] Testing Self-Diagnostic Engine...")
        res = self_diagnostic.run_diagnostics()
        self.assertTrue(res["success"])
        self.assertGreaterEqual(res["health_score"], 0.0)
        print(f"  [OK] Health Check Completed. Score: {res['health_score']}%. Faults: {len(res['faults'])}.")

    def test_07_self_programming(self):
        print("\n[TEST 7] Testing Self-Programming & Code Integrity Engine...")
        res = self_programmer.run_self_improvement("Check codebase syntax and health")
        self.assertTrue(res["success"])
        self.assertIn("snapshot_id", res)
        print(f"  [OK] Self-Programming Inspection Snapshot Created: {res['snapshot_id']}")

    def test_08_tool_router_end_to_end(self):
        print("\n[TEST 8] Testing Universal Orian Tool Router End-to-End...")
        resp_calc = tool_router.route_and_execute("Calculate 987 * 456")
        self.assertTrue(resp_calc.success)
        self.assertIn("450072", resp_calc.message)
        print(f"  [OK] Tool Router Executed Math: {resp_calc.message}")

if __name__ == "__main__":
    unittest.main()
