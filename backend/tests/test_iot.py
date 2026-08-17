import sys
import os
import unittest
import time

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

from features.iot.database import iot_db
from features.iot.device_manager import device_manager
from features.iot.mqtt_manager import mqtt_manager
from features.iot.scheduler import iot_scheduler
from features.iot.telemetry import iot_telemetry
from features.iot.health_check import iot_health_check
from features.iot.iot_tool import iot_tool
from features.tools.tool_router import OrianToolRouter
from features.planner.intent_detector import intent_detector, IntentCategory

class TestOrianIoTControlSystem(unittest.TestCase):
    """Comprehensive test suite for Orian AI Mobile IoT Control System."""

    def setUp(self):
        self.router = OrianToolRouter()

    def test_01_device_registration_and_discovery(self):
        print("\n[TEST IoT 1] Testing Device Registration & Discovery...")
        dev = device_manager.register_device(
            device_id="test_patio_light",
            device_name="Patio Light",
            device_type="light",
            location="Outdoor",
            state="OFF",
            status="ONLINE"
        )
        self.assertEqual(dev["device_id"], "test_patio_light")
        self.assertEqual(dev["device_name"], "Patio Light")

        # Fuzzy natural language matching
        matched = device_manager.find_device_by_natural_name("patio light")
        self.assertIsNotNone(matched)
        self.assertEqual(matched["device_id"], "test_patio_light")
        print("  [OK] Device registered and discovered via fuzzy NLP.")

    def test_02_atomic_control_and_verification(self):
        print("\n[TEST IoT 2] Testing Atomic Control & State Verification...")
        # 1. Turn On
        on_res = iot_tool.turn_on("room_light")
        self.assertTrue(on_res["success"])
        self.assertEqual(on_res["state"], "ON")
        self.assertTrue(on_res["verified"])

        # Check DB State
        dev = device_manager.get_device("room_light")
        self.assertEqual(dev["state"], "ON")
        print("  [OK] Turn ON confirmed with hardware verification.")

        # 2. Turn Off
        off_res = iot_tool.turn_off("room_light")
        self.assertTrue(off_res["success"])
        self.assertEqual(off_res["state"], "OFF")
        self.assertTrue(off_res["verified"])

        dev = device_manager.get_device("room_light")
        self.assertEqual(dev["state"], "OFF")
        print("  [OK] Turn OFF confirmed with hardware verification.")

    def test_03_safety_check_gate(self):
        print("\n[TEST IoT 3] Testing Safety Gate on Critical Appliances...")
        # Room heater is marked safety critical
        res = iot_tool.turn_on("room_heater")
        self.assertEqual(res.get("action"), "IOT_SAFETY_CONFIRMATION_REQUIRED")
        self.assertIn("Safety Notice", res.get("message", ""))
        print("  [OK] Safety confirmation triggered before activating high-power appliance.")

    def test_04_sensor_telemetry(self):
        print("\n[TEST IoT 4] Testing Sensor Telemetry Ingestion & Query...")
        iot_telemetry.record_reading("dht22_temp_sensor", "temperature", 24.5, "°C")
        iot_telemetry.record_reading("dht22_temp_sensor", "humidity", 55.0, "%")

        temp_res = iot_tool.get_temperature()
        self.assertTrue(temp_res["success"])
        self.assertEqual(temp_res["value"], 24.5)

        hum_res = iot_tool.get_humidity()
        self.assertTrue(hum_res["success"])
        self.assertEqual(hum_res["value"], 55.0)
        print("  [OK] Real-time sensor readings recorded and queried accurately.")

    def test_05_persistent_task_scheduling(self):
        print("\n[TEST IoT 5] Testing Persistent SQLite Scheduling...")
        sched = iot_scheduler.schedule_command("bedroom_fan", "turn_on", delay_seconds=300)
        self.assertIsNotNone(sched["schedule_id"])
        self.assertEqual(sched["command"], "turn_on")

        schedules = iot_scheduler.list_schedules(status="ACTIVE")
        self.assertTrue(len(schedules) > 0)

        # Cancel schedule
        canceled = iot_scheduler.cancel_schedule(sched["schedule_id"])
        self.assertTrue(canceled)
        print("  [OK] Persistent task schedule created and canceled successfully.")

    def test_06_iot_health_diagnostics(self):
        print("\n[TEST IoT 6] Testing IoT System Health Check Engine...")
        diag = iot_health_check.run_health_check()
        self.assertTrue(diag["health_score"] >= 80.0)
        self.assertEqual(diag["database_status"], "HEALTHY")
        self.assertTrue(diag["devices_total"] > 0)
        print(f"  [OK] IoT Health Check Score: {diag['health_score']}%. Status: {diag['database_status']}.")

    def test_07_intent_and_tool_router_nlp(self):
        print("\n[TEST IoT 7] Testing End-to-End Natural Language Voice/Text Commands...")
        
        # Test Intent Detection
        intent, _, _ = intent_detector.detect_intent("turn on my room light")
        self.assertEqual(intent, IntentCategory.IOT_CONTROL)

        intent_q, _, _ = intent_detector.detect_intent("what is the room temperature?")
        self.assertEqual(intent_q, IntentCategory.IOT_QUERY)

        # Test Router Execution
        res_ctrl = self.router.route_and_execute("turn on my room light")
        self.assertTrue(res_ctrl.success)
        self.assertIn("ON", res_ctrl.message)

        res_temp = self.router.route_and_execute("what is the room temperature?")
        self.assertTrue(res_temp.success)
        self.assertIn("°C", res_temp.message)

        res_diag = self.router.route_and_execute("check my iot system")
        self.assertTrue(res_diag.success)
        self.assertIn("Health Score", res_diag.message)

        print("  [OK] Full End-to-End NLP Voice and Text execution verified.")

if __name__ == "__main__":
    unittest.main()
