import sys
import os
import time
import logging
from typing import Dict, List, Any, Optional

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.iot.database import iot_db
from features.iot.device_manager import device_manager

logger = logging.getLogger("orian.iot.telemetry")

class IoTTelemetryEngine:
    """Manages sensor data aggregation, climate metrics, and real-time streaming."""

    def __init__(self):
        self._cache: Dict[str, Any] = {
            "temperature": 26.8,
            "humidity": 58.0,
            "motion": "Clear",
            "air_quality": "Good",
            "last_updated": time.time()
        }

    def record_reading(self, device_id: str, sensor_type: str, value: float, unit: str = ""):
        """Records a sensor reading in SQLite and updates the active telemetry cache."""
        now = time.time()
        iot_db.execute("""
            INSERT INTO iot_sensor_data (device_id, sensor_type, value, unit, recorded_at)
            VALUES (?, ?, ?, ?, ?)
        """, (device_id, sensor_type, value, unit, now))

        if "temp" in sensor_type.lower():
            self._cache["temperature"] = round(value, 1)
        elif "hum" in sensor_type.lower():
            self._cache["humidity"] = round(value, 1)

        self._cache["last_updated"] = now

    def get_latest_climate(self) -> Dict[str, Any]:
        """Returns the most up-to-date temperature and humidity readings."""
        # Query latest temperature
        temp_row = iot_db.fetch_one("""
            SELECT value, unit, recorded_at FROM iot_sensor_data
            WHERE sensor_type LIKE '%temp%'
            ORDER BY recorded_at DESC LIMIT 1
        """)
        # Query latest humidity
        hum_row = iot_db.fetch_one("""
            SELECT value, unit, recorded_at FROM iot_sensor_data
            WHERE sensor_type LIKE '%hum%'
            ORDER BY recorded_at DESC LIMIT 1
        """)

        temp_val = temp_row["value"] if temp_row else self._cache.get("temperature", 26.8)
        hum_val = hum_row["value"] if hum_row else self._cache.get("humidity", 58.0)

        return {
            "temperature": float(temp_val),
            "temperature_unit": "°C",
            "humidity": float(hum_val),
            "humidity_unit": "%",
            "motion": self._cache.get("motion", "Clear"),
            "air_quality": self._cache.get("air_quality", "Good"),
            "last_updated": time.time(),
            "formatted": f"Current Room Climate: {temp_val}°C | Humidity: {hum_val}%"
        }

    def get_telemetry_history(self, device_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
        """Fetches historical sensor readings for charts and audit logs."""
        if device_id:
            rows = iot_db.fetch_all("""
                SELECT * FROM iot_sensor_data
                WHERE device_id = ?
                ORDER BY recorded_at DESC LIMIT ?
            """, (device_id, limit))
        else:
            rows = iot_db.fetch_all("""
                SELECT * FROM iot_sensor_data
                ORDER BY recorded_at DESC LIMIT ?
            """, (limit,))
        return [dict(r) for r in rows]

iot_telemetry = IoTTelemetryEngine()
