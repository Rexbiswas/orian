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

from features.iot.iot_security import iot_security
from features.iot.device_manager import device_manager
from features.iot.mqtt_manager import mqtt_manager

class TestIoTSecurity(unittest.TestCase):

    def test_01_device_registration_and_credentials(self):
        """Tests device registration with unique public ID and secret token."""
        dev_id = f"esp32_test_{int(time.time()*1000)}"
        reg = iot_security.register_device(
            device_id=dev_id,
            device_name="Test ESP32 Core",
            device_type="ESP32"
        )

        self.assertEqual(reg["device_id"], dev_id)
        self.assertTrue(reg["public_id"].startswith("pub_"))
        self.assertTrue(len(reg["secret_token"]) >= 32)
        self.assertEqual(reg["mqtt_topic"], f"orian/devices/{dev_id}/command")

        # Verify registration in database
        dev = device_manager.get_device(dev_id)
        self.assertIsNotNone(dev)
        self.assertEqual(dev["device_id"], dev_id)

    def test_02_secure_command_payload_construction(self):
        """Tests that secure command envelopes include nonce, timestamp, TTL, and HMAC signature."""
        dev_id = "esp32_main_core"
        packet = iot_security.build_secure_command_payload(
            device_id=dev_id,
            command="turn_on",
            parameters={"relay": 1}
        )

        self.assertTrue("request_id" in packet)
        self.assertTrue("timestamp" in packet)
        self.assertTrue("expires_at" in packet)
        self.assertTrue("nonce" in packet)
        self.assertTrue("signature" in packet)
        self.assertTrue(len(packet["signature"]) == 64) # SHA256 hex length

    def test_03_telemetry_timestamp_replay_check(self):
        """Tests that telemetry within replay window is accepted and expired timestamps are rejected."""
        dev_id = "esp32_main_core"
        now = time.time()

        # Valid telemetry with current timestamp
        self.assertTrue(iot_security.validate_inbound_telemetry(dev_id, timestamp=now))

        # Replayed / Expired telemetry from 5 minutes ago must be rejected
        old_timestamp = now - 300
        self.assertFalse(iot_security.validate_inbound_telemetry(dev_id, timestamp=old_timestamp))

    def test_04_unauthorized_device_rejection(self):
        """Tests that unauthenticated/unpaired devices are rejected."""
        fake_id = "rogue_esp32_unregistered"
        self.assertFalse(iot_security.validate_inbound_telemetry(fake_id))

if __name__ == "__main__":
    unittest.main()
