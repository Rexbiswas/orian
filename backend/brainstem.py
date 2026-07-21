import os
import sqlite3
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("BrainstemDB")

class BrainstemDB:
    """Database 3: Brainstem (backend/db/brainstem.db) — Core Infrastructure, System Health, Voice Engine, Hardware, Security, Recovery."""

    def __init__(self, db_path=None):
        if not db_path:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, "db", "brainstem.db")
        self.db_path = db_path
        self._init_schema()


    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        c = conn.cursor()

        c.execute('''CREATE TABLE IF NOT EXISTS system_health
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, cpu_usage REAL, memory_usage REAL, disk_usage REAL, uptime_sec REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS services
                     (service_name TEXT PRIMARY KEY, status TEXT, port INTEGER, pid INTEGER, last_ping TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS voice_engine
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, engine_type TEXT, voice_id TEXT, vad_status TEXT, is_speaking INTEGER, last_active TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS wake_word
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, wake_phrase TEXT, sensitivity REAL, status TEXT, trigger_count INTEGER, last_triggered TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS api_connections
                     (endpoint TEXT PRIMARY KEY, service_name TEXT, status TEXT, latency_ms REAL, last_check TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS database_status
                     (db_name TEXT PRIMARY KEY, status TEXT, size_bytes INTEGER, integrity_check TEXT, last_check TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS network_status
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sent_mb REAL, recv_mb REAL, ping_ms REAL, status TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS hardware_status
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, cpu_temp REAL, gpu_usage REAL, available_ram_mb REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS security_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, source TEXT, details TEXT, severity TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS audit_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, action TEXT, target TEXT, status TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS model_status
                     (model_name TEXT PRIMARY KEY, provider TEXT, status TEXT, latency_ms REAL, fallback_model TEXT, last_used TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS recovery_events
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, service_name TEXT, error_reason TEXT, recovery_action TEXT, success INTEGER, timestamp TEXT)''')

        conn.commit()
        conn.close()
        self._seed_services()

    def _seed_services(self):
        default_services = [
            ("FastAPI Backend", 8000, "ONLINE"),
            ("Task Scheduler & Orchestrator", 8000, "ONLINE"),
            ("Command Relay Bridge", 0, "ONLINE"),
            ("VAD Voice Engine", 0, "ONLINE")
        ]
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        for name, port, status in default_services:
            c.execute("INSERT OR REPLACE INTO services (service_name, status, port, pid, last_ping) VALUES (?, ?, ?, ?, ?)",
                      (name, status, port, os.getpid(), now))
        conn.commit()
        conn.close()

    def record_health(self, cpu_usage: float, memory_usage: float, disk_usage: float = 0.0, uptime_sec: float = 0.0):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO system_health (cpu_usage, memory_usage, disk_usage, uptime_sec, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (cpu_usage, memory_usage, disk_usage, uptime_sec, now))
        conn.commit()
        conn.close()

    def update_voice_engine_status(self, engine_type: str = "WebSpeech/ElevenLabs", voice_id: str = "NOpBlnGInO9m6vDvFkFC", vad_status: str = "IDLE", is_speaking: bool = False):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO voice_engine (engine_type, voice_id, vad_status, is_speaking, last_active) VALUES (?, ?, ?, ?, ?)",
                  (engine_type, voice_id, vad_status, 1 if is_speaking else 0, now))
        conn.commit()
        conn.close()

    def record_security_event(self, event_type: str, source: str, details: str, severity: str = "INFO"):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO security_logs (event_type, source, details, severity, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (event_type, source, details, severity, now))
        conn.commit()
        conn.close()

    def record_recovery_event(self, service_name: str, error_reason: str, recovery_action: str, success: bool):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO recovery_events (service_name, error_reason, recovery_action, success, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (service_name, error_reason, recovery_action, 1 if success else 0, now))
        conn.commit()
        conn.close()

    def get_latest_health(self) -> Dict[str, Any]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT cpu_usage, memory_usage, disk_usage, uptime_sec, timestamp FROM system_health ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return dict(row)
        return {"cpu_usage": 0.0, "memory_usage": 0.0, "disk_usage": 0.0, "uptime_sec": 0.0, "timestamp": datetime.datetime.now().isoformat()}

brainstem_db = BrainstemDB()
