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
    protection_db, orian_notification_service,
    MobileAlertCategory, NotificationPriority, NotificationDeliveryStatus,
    NotificationEvent, NotificationDelivery, MobileDevice, DeviceStatus,
    ProtectionRiskLevel, NotificationActionType
)
from features.security.models import User, Role

class TestMobileNotificationService(unittest.TestCase):

    def setUp(self):
        self.service = orian_notification_service
        self.db = protection_db
        self.owner = User(id="u_owner_test", username="orian_owner", role=Role.OWNER)
        self.guest = User(id="u_guest_test", username="guest_user", role=Role.GUEST)

    def test_01_mobile_device_registration_and_lifecycle(self):
        """Tests pairing, approval, heartbeat, and revocation of mobile devices."""
        mob_id = f"mob-{uuid.uuid4().hex[:8]}"
        mob = MobileDevice(
            device_id=mob_id,
            device_name="Owner iPhone 16 Pro",
            owner_id=self.owner.id,
            auth_token_hash="fake_hash_123",
            fcm_token="fcm_token_sample",
            status=DeviceStatus.PAIRING,
            pairing_code="PAIR-554433"
        )
        self.db.register_mobile_device(mob)

        fetched = self.db.get_mobile_device(mob_id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.status, DeviceStatus.PAIRING)

        # Approve mobile device
        self.db.update_mobile_device_status(mob_id, DeviceStatus.ACTIVE)
        active_list = self.db.list_mobile_devices(active_only=True)
        self.assertTrue(any(d.device_id == mob_id for d in active_list))

        # Heartbeat update
        hb = self.db.update_mobile_heartbeat(mob_id, fcm_token="new_fcm_token")
        self.assertTrue(hb)

        # Revoke mobile device
        rev = self.db.revoke_mobile_device(mob_id, reason="Device lost")
        self.assertTrue(rev)
        revoked_dev = self.db.get_mobile_device(mob_id)
        self.assertEqual(revoked_dev.status, DeviceStatus.REVOKED)
        self.assertTrue(revoked_dev.revoked)

    def test_02_notification_creation_and_delivery_pipeline(self):
        """Tests structured alert generation, persistence, and delivery pipeline."""
        evt_id = f"evt_test_{uuid.uuid4().hex[:8]}"
        alert = self.service.create_and_send_alert(
            alert_type=MobileAlertCategory.PRODUCTIVITY_WARNING,
            title="ORIAN ALERT",
            device_id="My Windows Laptop",
            risk=ProtectionRiskLevel.MEDIUM,
            policy_id="work-hours-policy",
            policy_name="Work Hours",
            activity="Gaming detected",
            reason="Gaming detected during active Focus Mode",
            action="Warning issued",
            event_id=evt_id,
            force_send=True
        )
        self.assertIsNotNone(alert)
        self.assertEqual(alert.event_id, evt_id)
        self.assertEqual(alert.type, MobileAlertCategory.PRODUCTIVITY_WARNING)
        self.assertEqual(alert.risk, ProtectionRiskLevel.MEDIUM)
        self.assertEqual(alert.status, "UNREAD")

        # Query from DB
        stored = self.db.get_notification_event(evt_id)
        self.assertIsNotNone(stored)
        self.assertEqual(stored.activity, "Gaming detected")

    def test_03_duplicate_alert_idempotency_protection(self):
        """Tests that identical event_id or duplicate rapid alerts are blocked."""
        evt_id = f"evt_dedup_{uuid.uuid4().hex[:8]}"
        # 1st send -> OK
        alert1 = self.service.create_and_send_alert(
            alert_type=MobileAlertCategory.BLOCKED_APPLICATION,
            device_id="My Windows Laptop",
            risk=ProtectionRiskLevel.HIGH,
            activity="Blocked App",
            reason="Owner-configured blacklist",
            action="Blocked",
            event_id=evt_id,
            force_send=False
        )
        self.assertIsNotNone(alert1)

        # 2nd send with same event_id -> Blocked as duplicate
        alert2 = self.service.create_and_send_alert(
            alert_type=MobileAlertCategory.BLOCKED_APPLICATION,
            device_id="My Windows Laptop",
            risk=ProtectionRiskLevel.HIGH,
            activity="Blocked App",
            reason="Owner-configured blacklist",
            action="Blocked",
            event_id=evt_id,
            force_send=False
        )
        self.assertIsNone(alert2, "Duplicate alert with same event_id must return None")

    def test_04_all_16_alert_categories_supported(self):
        """Tests that all 16 required mobile alert categories format and save correctly."""
        categories = [
            MobileAlertCategory.PRODUCTIVITY_WARNING,
            MobileAlertCategory.PRODUCTIVITY_VIOLATION,
            MobileAlertCategory.BLOCKED_APPLICATION,
            MobileAlertCategory.BLOCKED_WEBSITE,
            MobileAlertCategory.FOCUS_MODE_VIOLATION,
            MobileAlertCategory.SECURITY_ALERT,
            MobileAlertCategory.SECURITY_TAMPERING,
            MobileAlertCategory.UNAUTHORIZED_ACCESS,
            MobileAlertCategory.MALWARE_ALERT,
            MobileAlertCategory.UNAUTHORIZED_HACKING_ALERT,
            MobileAlertCategory.NEW_DEVICE_CONNECTED,
            MobileAlertCategory.LAPTOP_AGENT_OFFLINE,
            MobileAlertCategory.LAPTOP_AGENT_TAMPERING,
            MobileAlertCategory.AUTOMATIC_SLEEP,
            MobileAlertCategory.OWNER_OVERRIDE,
            MobileAlertCategory.POLICY_CHANGED,
        ]

        for cat in categories:
            evt_id = f"evt_cat_{uuid.uuid4().hex[:8]}"
            alert = self.service.create_and_send_alert(
                alert_type=cat,
                device_id="My Windows Laptop",
                risk=ProtectionRiskLevel.CRITICAL if "SECURITY" in cat.value or "MALWARE" in cat.value else ProtectionRiskLevel.MEDIUM,
                activity=f"Activity for {cat.value}",
                reason=f"Reason for {cat.value}",
                action="Action taken",
                event_id=evt_id,
                force_send=True
            )
            self.assertIsNotNone(alert)
            self.assertEqual(alert.type, cat)

    def test_05_notification_acknowledgment(self):
        """Tests owner acknowledging an unread notification."""
        evt_id = f"evt_ack_{uuid.uuid4().hex[:8]}"
        self.service.create_and_send_alert(
            alert_type=MobileAlertCategory.SECURITY_TAMPERING,
            device_id="My Windows Laptop",
            risk=ProtectionRiskLevel.CRITICAL,
            activity="Attempt to disable agent",
            reason="Service stop signal received",
            action="Blocked",
            event_id=evt_id,
            force_send=True
        )

        ack = self.service.acknowledge_alert(evt_id, self.owner)
        self.assertTrue(ack)

        event = self.db.get_notification_event(evt_id)
        self.assertEqual(event.status, "ACKNOWLEDGED")
        self.assertEqual(event.acknowledged_by, self.owner.username)

    def test_06_unauthenticated_action_rejection(self):
        """Security Test: Non-privileged user or unverified action must be rejected."""
        evt_id = f"evt_sec_act_{uuid.uuid4().hex[:8]}"
        self.service.create_and_send_alert(
            alert_type=MobileAlertCategory.PRODUCTIVITY_WARNING,
            device_id="My Windows Laptop",
            risk=ProtectionRiskLevel.MEDIUM,
            reason="Test",
            action="Warn",
            event_id=evt_id,
            force_send=True
        )

        # Guest attempting OWNER_OVERRIDE -> PermissionError
        with self.assertRaises(PermissionError):
            self.service.handle_secure_action(
                event_id=evt_id,
                action_type=NotificationActionType.OWNER_OVERRIDE,
                user=self.guest,
                reason="Malicious override"
            )

if __name__ == "__main__":
    unittest.main()
