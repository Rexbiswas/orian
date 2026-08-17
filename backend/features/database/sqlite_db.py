import sqlite3
import json
import logging
import os
import time
from typing import Dict, List, Any, Optional
from config import settings

logger = logging.getLogger("orian.sqlite_db")

class Database:
    def __init__(self, db_path: str = settings.SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT,
            email TEXT,
            preferences_json TEXT DEFAULT '{}',
            created_at REAL,
            updated_at REAL
        )
        """)

        # Projects
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'active',
            metadata_json TEXT DEFAULT '{}',
            created_at REAL,
            updated_at REAL
        )
        """)

        # Conversations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            title TEXT,
            status TEXT DEFAULT 'active',
            created_at REAL,
            updated_at REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
        """)

        # Messages
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            metadata_json TEXT DEFAULT '{}',
            created_at REAL,
            FOREIGN KEY (conversation_id) REFERENCES conversations (id)
        )
        """)

        # Installed Software
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS installed_software (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            path TEXT,
            version TEXT,
            type TEXT,
            metadata_json TEXT DEFAULT '{}',
            detected_at REAL
        )
        """)

        # Tasks
        cursor.execute("""
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
        )
        """)

        # Agent State
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_state (
            agent_id TEXT PRIMARY KEY,
            status TEXT DEFAULT 'IDLE',
            last_active REAL,
            current_task_id TEXT,
            metrics_json TEXT DEFAULT '{}'
        )
        """)

        # File Index
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS file_index (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            file_path TEXT UNIQUE NOT NULL,
            file_type TEXT,
            file_hash TEXT,
            size_bytes INTEGER,
            indexed_at REAL,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
        """)

        # Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            agent_id TEXT,
            level TEXT DEFAULT 'INFO',
            category TEXT,
            message TEXT,
            payload_json TEXT DEFAULT '{}',
            timestamp REAL
        )
        """)

        # Permissions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS permissions (
            id TEXT PRIMARY KEY,
            resource TEXT NOT NULL,
            action TEXT NOT NULL,
            risk_level TEXT DEFAULT 'MEDIUM',
            status TEXT DEFAULT 'PENDING',
            requested_by TEXT,
            approved_by TEXT,
            timestamp REAL
        )
        """)

        # System Config
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at REAL
        )
        """)

        # Audit Trail
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            request_id TEXT,
            actor TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            risk_level TEXT,
            result TEXT,
            timestamp REAL
        )
        """)

        # Create Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages (conversation_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks (status);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_logs_req ON logs (request_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_file_index_proj ON file_index (project_id);")

        conn.commit()
        conn.close()
        logger.info(f"Initialized SQLite Core System-of-Record at {self.db_path}")

    # Helper CRUD Methods
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

db = Database()
