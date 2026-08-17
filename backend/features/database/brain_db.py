import sys
import os

for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

import sqlite3
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional
from config import settings

logger = logging.getLogger("orian.brain_db")

class BrainDBManager:
    """
    Anatomical Brain Database Architecture for Orian AI:
    - cerebrum.db : High-level reasoning, planning, complex tasks, project knowledge & user preferences
    - cerebellum.db : Motor controls, fast execution, tool calls, automation scripts & active tasks
    - medulla.db   : Autonomic survival, telemetry, logs, sensor data, heartbeats & system status
    - memory.db    : Unified short-term & long-term cognitive memory bridge connecting all DBs & agents
    """

    def __init__(self, storage_dir: str = os.path.join(settings.ORIAN_ROOT_DIR, "brain_db")):
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)

        self.cerebrum_path = os.path.join(self.storage_dir, "cerebrum.db")
        self.cerebellum_path = os.path.join(self.storage_dir, "cerebellum.db")
        self.medulla_path = os.path.join(self.storage_dir, "medulla.db")
        self.memory_path = os.path.join(self.storage_dir, "memory.db")

        self._init_all_databases()

    def get_connection(self, db_name: str) -> sqlite3.Connection:
        db_map = {
            "cerebrum": self.cerebrum_path,
            "cerebellum": self.cerebellum_path,
            "medulla": self.medulla_path,
            "memory": self.memory_path
        }
        target_path = db_map.get(db_name, self.memory_path)
        conn = sqlite3.connect(target_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_all_databases(self):
        # 1. CEREBRUM.DB - Thinking, Reasoning, Knowledge & Users
        conn = self.get_connection("cerebrum")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS reasoning_traces (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            query TEXT NOT NULL,
            reasoning_chain_json TEXT DEFAULT '[]',
            confidence_score REAL,
            created_at REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            metadata_json TEXT DEFAULT '{}',
            created_at REAL,
            updated_at REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT,
            preferences_json TEXT DEFAULT '{}',
            created_at REAL,
            updated_at REAL
        )""")
        conn.commit()
        conn.close()

        # 2. CEREBELLUM.DB - Execution, Tools, Automations & Motor Tasks
        conn = self.get_connection("cerebellum")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            request_id TEXT,
            parent_task_id TEXT,
            status TEXT DEFAULT 'PENDING',
            risk_level TEXT DEFAULT 'LOW',
            priority INTEGER DEFAULT 1,
            payload_json TEXT DEFAULT '{}',
            result_json TEXT DEFAULT '{}',
            error_message TEXT,
            created_at REAL,
            updated_at REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tool_execution_history (
            id TEXT PRIMARY KEY,
            task_id TEXT,
            tool_name TEXT NOT NULL,
            params_json TEXT DEFAULT '{}',
            result_json TEXT DEFAULT '{}',
            duration_seconds REAL,
            status TEXT DEFAULT 'SUCCESS',
            executed_at REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS active_automations (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            trigger_type TEXT NOT NULL,
            action_payload_json TEXT DEFAULT '{}',
            is_active INTEGER DEFAULT 1,
            last_run REAL
        )""")
        conn.commit()
        conn.close()

        # 3. MEDULLA.DB - Autonomic System, Telemetry & Logs
        conn = self.get_connection("medulla")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS system_telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cpu_usage REAL,
            ram_usage REAL,
            active_processes INTEGER,
            network_status TEXT,
            timestamp REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            agent_id TEXT,
            level TEXT DEFAULT 'INFO',
            category TEXT,
            message TEXT,
            payload_json TEXT DEFAULT '{}',
            timestamp REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            risk_level TEXT,
            result TEXT,
            timestamp REAL
        )""")
        conn.commit()
        conn.close()

        # 4. MEMORY.DB - Unified Cognitive Memory Bridge (Inter-connects Cerebrum, Cerebellum & Medulla)
        conn = self.get_connection("memory")
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            status TEXT DEFAULT 'active',
            created_at REAL,
            updated_at REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at REAL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS cognitive_memories (
            id TEXT PRIMARY KEY,
            brain_region TEXT NOT NULL, -- CEREBRUM, CEREBELLUM, MEDULLA
            memory_type TEXT NOT NULL,
            key_subject TEXT,
            content TEXT NOT NULL,
            importance REAL DEFAULT 1.0,
            metadata_json TEXT DEFAULT '{}',
            timestamp REAL
        )""")
        cur.execute("""
        CREATE TABLE IF NOT EXISTS agent_connections (
            agent_id TEXT PRIMARY KEY,
            assigned_region TEXT NOT NULL, -- CEREBRUM, CEREBELLUM, MEDULLA
            status TEXT DEFAULT 'ACTIVE',
            last_ping REAL
        )""")
        conn.commit()
        conn.close()

        logger.info(f"Initialized Human Brain Architecture DBs in: {self.storage_dir}")
        logger.info(" -> cerebrum.db (Cognition, Reasoning, Projects)")
        logger.info(" -> cerebellum.db (Execution, Motor Tools, Automations)")
        logger.info(" -> medulla.db (Telemetry, Autonomic Heartbeat, System Logs)")
        logger.info(" -> memory.db (Unified Cognitive Bridge connecting all Agents)")

    # Universal Query Execution
    def execute(self, db_name: str, query: str, params: tuple = ()) -> int:
        conn = self.get_connection(db_name)
        cur = conn.cursor()
        cur.execute(query, params)
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount

    def fetch_all(self, db_name: str, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        conn = self.get_connection(db_name)
        cur = conn.cursor()
        cur.execute(query, params)
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def fetch_one(self, db_name: str, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        conn = self.get_connection(db_name)
        cur = conn.cursor()
        cur.execute(query, params)
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

# Singleton Instance
brain_db = BrainDBManager()
