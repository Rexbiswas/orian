import sys
import os
import sqlite3
import json
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

from config import settings

logger = logging.getLogger("orian.iot.database")

class IoTDatabase:
    """Manages SQLite storage for IoT devices, commands, telemetry, schedules, and diagnostics."""

    def __init__(self, db_path: str = settings.SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. IoT Registered Devices
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iot_devices (
            id TEXT PRIMARY KEY,
            device_id TEXT UNIQUE NOT NULL,
            device_name TEXT NOT NULL,
            device_type TEXT NOT NULL,
            location TEXT DEFAULT 'Home',
            ip_address TEXT DEFAULT '',
            mqtt_topic TEXT NOT NULL,
            state TEXT DEFAULT 'OFF',
            status TEXT DEFAULT 'ONLINE',
            is_safety_critical INTEGER DEFAULT 0,
            last_seen REAL,
            meta_json TEXT DEFAULT '{}',
            created_at REAL
        )
        """)

        # 2. IoT Commands Audit & Verification
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iot_commands (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            command TEXT NOT NULL,
            payload_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'PENDING',
            response_json TEXT DEFAULT '{}',
            verified INTEGER DEFAULT 0,
            error_message TEXT DEFAULT '',
            latency_ms REAL DEFAULT 0,
            created_at REAL,
            FOREIGN KEY (device_id) REFERENCES iot_devices (device_id)
        )
        """)

        # 3. IoT Real-Time Sensor Telemetry
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iot_sensor_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT NOT NULL,
            sensor_type TEXT NOT NULL,
            value REAL NOT NULL,
            unit TEXT DEFAULT '',
            meta_json TEXT DEFAULT '{}',
            recorded_at REAL,
            FOREIGN KEY (device_id) REFERENCES iot_devices (device_id)
        )
        """)

        # 4. IoT Persistent Task Schedules
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iot_schedules (
            id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            command TEXT NOT NULL,
            payload_json TEXT DEFAULT '{}',
            scheduled_time REAL NOT NULL,
            recurrence TEXT DEFAULT 'once',
            status TEXT DEFAULT 'ACTIVE',
            created_at REAL,
            FOREIGN KEY (device_id) REFERENCES iot_devices (device_id)
        )
        """)

        # 5. IoT System Events & Diagnostics
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS iot_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            device_id TEXT DEFAULT '',
            event_type TEXT NOT NULL,
            severity TEXT DEFAULT 'INFO',
            description TEXT NOT NULL,
            meta_json TEXT DEFAULT '{}',
            timestamp REAL
        )
        """)

        # Indexes for ultra-fast query performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iot_dev_type ON iot_devices (device_type);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iot_dev_status ON iot_devices (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iot_cmd_dev ON iot_commands (device_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iot_sens_dev ON iot_sensor_data (device_id, recorded_at);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_iot_sched_stat ON iot_schedules (status, scheduled_time);")

        conn.commit()
        conn.close()
        logger.info(f"IoT Database subsystem verified on {self.db_path}")

    # Generic execution helpers
    def execute(self, query: str, params: tuple = ()) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        rowcount = cursor.rowcount
        conn.close()
        return rowcount

    def fetch_all(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows

    def fetch_one(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

iot_db = IoTDatabase()
