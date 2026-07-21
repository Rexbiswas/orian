import os
import sqlite3
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("BrainstreamDB")

class BrainstreamDB:
    """Database 4: Brainstream (backend/db/brainstream.db) — Real-Time Thought Stream, Cognitive Signal Sync, Telemetry, and Sensory Flow."""

    def __init__(self, db_path=None):
        if not db_path:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, "db", "brainstream.db")
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

        c.execute('''CREATE TABLE IF NOT EXISTS thought_stream
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, thought_type TEXT, content TEXT, confidence REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS sensory_stream
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sensor_type TEXT, payload_summary TEXT, raw_signal TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS action_stream
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT, target TEXT, status TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS telemetry_stream
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, event_type TEXT, metric_json TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS memory_sync_stream
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, sync_type TEXT, source_db TEXT, target_db TEXT, synced_items INTEGER, timestamp TEXT)''')

        conn.commit()
        conn.close()

    def record_thought(self, content: str, thought_type: str = "REASONING", task_id: str = "", confidence: float = 1.0):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO thought_stream (task_id, thought_type, content, confidence, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (task_id, thought_type, content, confidence, now))
        conn.commit()
        conn.close()

    def record_sensory_event(self, sensor_type: str, payload_summary: str, raw_signal: str = ""):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO sensory_stream (sensor_type, payload_summary, raw_signal, timestamp) VALUES (?, ?, ?, ?)",
                  (sensor_type, payload_summary, raw_signal, now))
        conn.commit()
        conn.close()

    def record_action_signal(self, action_type: str, target: str, status: str = "EXECUTING"):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO action_stream (action_type, target, status, timestamp) VALUES (?, ?, ?, ?)",
                  (action_type, target, status, now))
        conn.commit()
        conn.close()

    def record_telemetry_event(self, event_type: str, metric_data: Dict[str, Any]):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO telemetry_stream (event_type, metric_json, timestamp) VALUES (?, ?, ?)",
                  (event_type, json.dumps(metric_data), now))
        conn.commit()
        conn.close()

    def record_synaptic_sync(self, sync_type: str, source_db: str, target_db: str, synced_items: int):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO memory_sync_stream (sync_type, source_db, target_db, synced_items, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (sync_type, source_db, target_db, synced_items, now))
        conn.commit()
        conn.close()

    def get_recent_thoughts(self, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT thought_type, content, confidence, timestamp FROM thought_stream ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

brainstream_db = BrainstreamDB()
