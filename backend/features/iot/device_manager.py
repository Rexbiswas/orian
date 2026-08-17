import sys
import os
import time
import uuid
import json
import logging
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.iot.database import iot_db

logger = logging.getLogger("orian.iot.device_manager")

class IoTDevice(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    device_name: str
    device_type: str  # light, fan, relay, sensor, ac, lock, heater, esp32
    location: str = "Room"
    ip_address: str = "192.168.1.105"
    mqtt_topic: str
    state: str = "OFF"  # ON, OFF, or value like "24.5"
    status: str = "ONLINE"  # ONLINE, OFFLINE, UNREACHABLE
    is_safety_critical: bool = False
    last_seen: float = Field(default_factory=time.time)
    meta: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)

class DeviceManager:
    """Manages IoT device registration, discovery, state verification, and heartbeat monitoring."""

    # Default starter demonstration hardware devices
    DEFAULT_DEVICES = [
        {
            "device_id": "esp32_main_core",
            "device_name": "Orian ESP32 Hub",
            "device_type": "esp32",
            "location": "Central Hub",
            "ip_address": "192.168.1.105",
            "mqtt_topic": "orian/devices/esp32_main_core",
            "state": "ONLINE",
            "status": "ONLINE",
            "is_safety_critical": False,
            "meta": {"gpio_pins": [2, 4, 15, 18], "firmware": "v2.0-esp32"}
        },
        {
            "device_id": "room_light",
            "device_name": "Room Light",
            "device_type": "light",
            "location": "Bedroom",
            "ip_address": "192.168.1.105",
            "mqtt_topic": "orian/devices/room_light",
            "state": "OFF",
            "status": "ONLINE",
            "is_safety_critical": False,
            "meta": {"gpio": 2, "icon": "Lightbulb"}
        },
        {
            "device_id": "bedroom_fan",
            "device_name": "Bedroom Fan",
            "device_type": "fan",
            "location": "Bedroom",
            "ip_address": "192.168.1.105",
            "mqtt_topic": "orian/devices/bedroom_fan",
            "state": "OFF",
            "status": "ONLINE",
            "is_safety_critical": False,
            "meta": {"gpio": 4, "relay_channel": 1, "icon": "Fan"}
        },
        {
            "device_id": "living_room_ac",
            "device_name": "Living Room AC",
            "device_type": "ac",
            "location": "Living Room",
            "ip_address": "192.168.1.108",
            "mqtt_topic": "orian/devices/living_room_ac",
            "state": "OFF",
            "status": "ONLINE",
            "is_safety_critical": False,
            "meta": {"temp_set": 24, "icon": "Wind"}
        },
        {
            "device_id": "dht22_temp_sensor",
            "device_name": "Room Climate Sensor",
            "device_type": "sensor",
            "location": "Bedroom",
            "ip_address": "192.168.1.105",
            "mqtt_topic": "orian/devices/dht22_temp_sensor",
            "state": "26.8",
            "status": "ONLINE",
            "is_safety_critical": False,
            "meta": {"temperature": 26.8, "humidity": 58.0, "icon": "Thermometer"}
        },
        {
            "device_id": "room_heater",
            "device_name": "Room Heater",
            "device_type": "heater",
            "location": "Bedroom",
            "ip_address": "192.168.1.112",
            "mqtt_topic": "orian/devices/room_heater",
            "state": "OFF",
            "status": "ONLINE",
            "is_safety_critical": True,
            "meta": {"power_watts": 1500, "icon": "Flame"}
        }
    ]

    def __init__(self):
        self._ensure_default_devices()

    def _ensure_default_devices(self):
        """Populates baseline devices if SQLite store is clean."""
        count = iot_db.fetch_one("SELECT COUNT(*) as cnt FROM iot_devices")
        if not count or count["cnt"] == 0:
            logger.info("Initializing baseline Orian IoT devices in SQLite...")
            for dev in self.DEFAULT_DEVICES:
                self.register_device(
                    device_id=dev["device_id"],
                    device_name=dev["device_name"],
                    device_type=dev["device_type"],
                    location=dev.get("location", "Home"),
                    ip_address=dev.get("ip_address", "192.168.1.105"),
                    mqtt_topic=dev.get("mqtt_topic", f"orian/devices/{dev['device_id']}"),
                    state=dev.get("state", "OFF"),
                    status=dev.get("status", "ONLINE"),
                    is_safety_critical=dev.get("is_safety_critical", False),
                    meta=dev.get("meta", {})
                )

    def register_device(
        self,
        device_id: str,
        device_name: str,
        device_type: str,
        location: str = "Home",
        ip_address: str = "",
        mqtt_topic: str = "",
        state: str = "OFF",
        status: str = "ONLINE",
        is_safety_critical: bool = False,
        meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Registers a new or existing IoT hardware peripheral in SQLite."""
        uid = str(uuid.uuid4())
        topic = mqtt_topic or f"orian/devices/{device_id}"
        meta_str = json.dumps(meta or {})
        now = time.time()

        existing = self.get_device(device_id)
        if existing:
            iot_db.execute("""
                UPDATE iot_devices SET
                    device_name = ?, device_type = ?, location = ?, ip_address = ?,
                    mqtt_topic = ?, state = ?, status = ?, is_safety_critical = ?,
                    last_seen = ?, meta_json = ?
                WHERE device_id = ?
            """, (device_name, device_type, location, ip_address, topic, state, status, int(is_safety_critical), now, meta_str, device_id))
        else:
            iot_db.execute("""
                INSERT INTO iot_devices (
                    id, device_id, device_name, device_type, location, ip_address,
                    mqtt_topic, state, status, is_safety_critical, last_seen, meta_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (uid, device_id, device_name, device_type, location, ip_address, topic, state, status, int(is_safety_critical), now, meta_str, now))

        logger.info(f"Registered IoT Device: {device_name} ({device_id}) on topic '{topic}'")
        return self.get_device(device_id) or {}

    def get_device(self, device_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single registered device by device_id."""
        row = iot_db.fetch_one("SELECT * FROM iot_devices WHERE device_id = ?", (device_id,))
        if row:
            d = dict(row)
            try:
                d["meta"] = json.loads(d.get("meta_json") or "{}")
            except Exception:
                d["meta"] = {}
            return d
        return None

    def find_device_by_natural_name(self, query: str) -> Optional[Dict[str, Any]]:
        """Fuzzy matches natural language user input (e.g. 'my room light', 'fan', 'temperature') to registered device."""
        q = query.lower().strip()
        all_devs = self.list_all_devices()

        # 1. Exact ID or exact name match
        for d in all_devs:
            if d["device_id"].lower() == q or d["device_name"].lower() == q:
                return d

        # 2. Substring & Type matching
        for d in all_devs:
            d_name = d["device_name"].lower()
            d_type = d["device_type"].lower()
            d_loc = d.get("location", "").lower()

            if d_name in q or q in d_name:
                return d
            if d_loc in q and d_type in q:
                return d

        # 3. Keyword matching for common devices
        keywords_map = {
            "light": ["light", "bulb", "lamp", "led"],
            "fan": ["fan", "cooler", "blower"],
            "ac": ["ac", "air conditioner", "air condition", "cooling"],
            "sensor": ["temperature", "temp", "humidity", "climate", "sensor"],
            "heater": ["heater", "geyser", "heating"],
            "esp32": ["esp32", "esp", "microcontroller", "controller", "board"]
        }

        for target_type, terms in keywords_map.items():
            if any(term in q for term in terms):
                for d in all_devs:
                    if d["device_type"].lower() == target_type:
                        # Prioritize location match if mentioned
                        if d.get("location", "").lower() in q:
                            return d
                for d in all_devs:
                    if d["device_type"].lower() == target_type:
                        return d

        return None

    def list_all_devices(self) -> List[Dict[str, Any]]:
        """Lists all registered IoT devices with parsed metadata."""
        rows = iot_db.fetch_all("SELECT * FROM iot_devices ORDER BY created_at ASC")
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["meta"] = json.loads(d.get("meta_json") or "{}")
            except Exception:
                d["meta"] = {}
            result.append(d)
        return result

    def update_device_state(self, device_id: str, new_state: str, new_status: str = "ONLINE") -> bool:
        """Updates device state (e.g. ON, OFF) and last_seen timestamp."""
        now = time.time()
        rowcount = iot_db.execute("""
            UPDATE iot_devices SET
                state = ?, status = ?, last_seen = ?
            WHERE device_id = ?
        """, (new_state, new_status, now, device_id))
        return rowcount > 0

    def update_heartbeat(self, device_id: str, ip_address: Optional[str] = None) -> bool:
        """Registers a heartbeat ping from an ESP32 or sensor."""
        now = time.time()
        if ip_address:
            rowcount = iot_db.execute("""
                UPDATE iot_devices SET
                    status = 'ONLINE', last_seen = ?, ip_address = ?
                WHERE device_id = ?
            """, (now, ip_address, device_id))
        else:
            rowcount = iot_db.execute("""
                UPDATE iot_devices SET
                    status = 'ONLINE', last_seen = ?
                WHERE device_id = ?
            """, (now, device_id))
        return rowcount > 0

    def remove_device(self, device_id: str) -> bool:
        """Removes device from registration."""
        rowcount = iot_db.execute("DELETE FROM iot_devices WHERE device_id = ?", (device_id,))
        return rowcount > 0

    def check_and_update_offline_devices(self, timeout_seconds: float = 120.0) -> List[Dict[str, Any]]:
        """Checks for devices that missed heartbeats and marks them OFFLINE."""
        cutoff = time.time() - timeout_seconds
        devices = self.list_all_devices()
        offline_devs = []

        for d in devices:
            if d.get("last_seen", 0) < cutoff and d.get("status") == "ONLINE":
                iot_db.execute("UPDATE iot_devices SET status = 'OFFLINE' WHERE device_id = ?", (d["device_id"],))
                d["status"] = "OFFLINE"
                offline_devs.append(d)

        return offline_devs

device_manager = DeviceManager()
