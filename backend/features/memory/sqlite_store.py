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

import json
import time
import uuid
from typing import List, Dict, Any, Optional
from database.sqlite_db import db
from database.brain_db import brain_db

class SQLiteMemoryStore:
    def store_user(self, user_id: str, username: str, display_name: str, email: str = "", preferences: dict = None) -> str:
        now = time.time()
        prefs_json = json.dumps(preferences or {})
        existing = db.fetch_one("SELECT id FROM users WHERE id = ?", (user_id,))
        if existing:
            db.execute(
                "UPDATE users SET username=?, display_name=?, email=?, preferences_json=?, updated_at=? WHERE id=?",
                (username, display_name, email, prefs_json, now, user_id)
            )
        else:
            db.execute(
                "INSERT INTO users (id, username, display_name, email, preferences_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (user_id, username, display_name, email, prefs_json, now, now)
            )
        # Mirror to Cerebrum (User Cognition)
        brain_db.execute("cerebrum",
            "INSERT OR REPLACE INTO users (id, username, display_name, email, preferences_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, display_name, email, prefs_json, now, now)
        )
        return user_id

    def store_project(self, project_id: str, name: str, path: str, description: str = "", metadata: dict = None) -> str:
        now = time.time()
        meta_json = json.dumps(metadata or {})
        existing = db.fetch_one("SELECT id FROM projects WHERE id = ?", (project_id,))
        if existing:
            db.execute(
                "UPDATE projects SET name=?, path=?, description=?, metadata_json=?, updated_at=? WHERE id=?",
                (name, path, description, meta_json, now, project_id)
            )
        else:
            db.execute(
                "INSERT INTO projects (id, name, path, description, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (project_id, name, path, description, meta_json, now, now)
            )
        # Mirror to Cerebrum (Project Reasoning)
        brain_db.execute("cerebrum",
            "INSERT OR REPLACE INTO projects (id, name, path, description, metadata_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (project_id, name, path, description, meta_json, now, now)
        )
        return project_id

    def add_message(self, conversation_id: str, role: str, content: str, metadata: dict = None) -> str:
        msg_id = str(uuid.uuid4())
        now = time.time()
        meta_json = json.dumps(metadata or {})
        
        # Ensure conversation exists
        conv = db.fetch_one("SELECT id FROM conversations WHERE id = ?", (conversation_id,))
        if not conv:
            db.execute("INSERT INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                       (conversation_id, f"Conversation {conversation_id[:8]}", now, now))
        else:
            db.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (now, conversation_id))

        db.execute(
            "INSERT INTO messages (id, conversation_id, role, content, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, meta_json, now)
        )

        # Mirror to Memory.db (Unified Cognitive Bridge)
        brain_db.execute("memory",
            "INSERT OR IGNORE INTO conversations (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (conversation_id, f"Conversation {conversation_id[:8]}", now, now)
        )
        brain_db.execute("memory",
            "INSERT INTO messages (id, conversation_id, role, content, metadata_json, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (msg_id, conversation_id, role, content, meta_json, now)
        )
        return msg_id

    def get_conversation_history(self, conversation_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        rows = db.fetch_all(
            "SELECT id, role, content, metadata_json, created_at FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
            (conversation_id, limit)
        )
        for r in rows:
            try:
                r["metadata"] = json.loads(r.get("metadata_json") or "{}")
            except Exception:
                r["metadata"] = {}
        return rows

    def store_task(self, task_id: str, title: str, status: str = "PENDING", risk_level: str = "LOW", payload: dict = None, request_id: str = None) -> str:
        now = time.time()
        payload_json = json.dumps(payload or {})
        existing = db.fetch_one("SELECT id FROM tasks WHERE id = ?", (task_id,))
        if existing:
            db.execute(
                "UPDATE tasks SET title=?, status=?, risk_level=?, payload_json=?, updated_at=? WHERE id=?",
                (title, status, risk_level, payload_json, now, task_id)
            )
        else:
            db.execute(
                "INSERT INTO tasks (id, title, request_id, status, risk_level, payload_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (task_id, title, request_id, status, risk_level, payload_json, now, now)
            )
        # Mirror to Cerebellum (Task Execution & Motor Controls)
        brain_db.execute("cerebellum",
            "INSERT OR REPLACE INTO tasks (id, title, request_id, status, risk_level, payload_json, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (task_id, title, request_id, status, risk_level, payload_json, now, now)
        )
        return task_id

    def update_task_status(self, task_id: str, status: str, result: dict = None, error_message: str = None):
        now = time.time()
        result_json = json.dumps(result or {})
        db.execute(
            "UPDATE tasks SET status=?, result_json=?, error_message=?, updated_at=? WHERE id=?",
            (status, result_json, error_message, now, task_id)
        )
        brain_db.execute("cerebellum",
            "UPDATE tasks SET status=?, result_json=?, error_message=?, updated_at=? WHERE id=?",
            (status, result_json, error_message, now, task_id)
        )

    def log_event(self, request_id: str, agent_id: str, level: str, category: str, message: str, payload: dict = None):
        now = time.time()
        payload_json = json.dumps(payload or {})
        db.execute(
            "INSERT INTO logs (request_id, agent_id, level, category, message, payload_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (request_id, agent_id, level, category, message, payload_json, now)
        )
        # Mirror to Medulla (Autonomic System & Telemetry Logs)
        brain_db.execute("medulla",
            "INSERT INTO logs (request_id, agent_id, level, category, message, payload_json, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (request_id, agent_id, level, category, message, payload_json, now)
        )

sqlite_store = SQLiteMemoryStore()
