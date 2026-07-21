import os
import sqlite3
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CerebrumDB")

class CerebrumDB:
    """Database 1: Cerebrum (backend/db/cerebrum.db) — Intelligence, Reasoning, Multi-Lobe Memory, Context, Vision, Reflection."""

    def __init__(self, db_path=None):
        if not db_path:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, "db", "cerebrum.db")
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

        # --- FRONTAL LOBE (Reasoning, Planning, Decisions, Reflection) ---
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_goals
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, goal TEXT, status TEXT, importance INTEGER, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_plans
                     (id TEXT PRIMARY KEY, goal_id INTEGER, plan_json TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_tasks
                     (id TEXT PRIMARY KEY, plan_id TEXT, command TEXT, tool_name TEXT, tool_params TEXT, agent_type TEXT, priority TEXT, dependencies TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_decisions
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, context TEXT, rationale TEXT, chosen_path TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_priorities
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, priority_score REAL, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS frontal_reflections
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, outcome TEXT, evaluation TEXT, lesson_learned TEXT, timestamp TEXT)''')

        # --- PARIETAL LOBE (Context, Apps, Windows, Clipboard, Environment) ---
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_context
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, key TEXT UNIQUE, value TEXT, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_apps
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, app_name TEXT, window_title TEXT, state TEXT, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_windows
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, handle TEXT, title TEXT, is_active INTEGER, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_browser
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, url TEXT, title TEXT, tab_index INTEGER, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_clipboard
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, content TEXT, content_type TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS parietal_environment
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, var_name TEXT UNIQUE, var_val TEXT, updated_at TEXT)''')

        # --- TEMPORAL LOBE (Memory, Conversations, Preferences, Projects, Skills) ---
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_short_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, content TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_long_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, memory_type TEXT, content TEXT, importance_score REAL, confidence REAL, source TEXT, project_id TEXT, tags TEXT, related_ids TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_working_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, key TEXT, value TEXT, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_semantic_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, concept TEXT UNIQUE, definition TEXT, confidence REAL, source TEXT, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_procedural_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, skill_name TEXT UNIQUE, steps_json TEXT, success_rate REAL, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_episodic_memory
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, episode_title TEXT, details TEXT, importance_score REAL, confidence REAL, source TEXT, project_id TEXT, tags TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_conversations
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_input TEXT, bot_response TEXT, context TEXT, importance_score REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_preferences
                     (key TEXT PRIMARY KEY, value TEXT, updated_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_projects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, path TEXT UNIQUE, tech_stack TEXT, last_active TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS temporal_skills
                     (skill_name TEXT PRIMARY KEY, status TEXT, last_used TEXT)''')

        # --- OCCIPITAL LOBE (Visual, OCR, UI Elements) ---
        c.execute('''CREATE TABLE IF NOT EXISTS occipital_screens
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, image_path TEXT, width INTEGER, height INTEGER, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS occipital_ocr
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, screen_id INTEGER, extracted_text TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS occipital_ui
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, screen_id INTEGER, element_type TEXT, bounds TEXT, text TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS occipital_objects
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, screen_id INTEGER, object_name TEXT, confidence REAL)''')
        c.execute('''CREATE TABLE IF NOT EXISTS occipital_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT, visual_summary TEXT, timestamp TEXT)''')

        conn.commit()
        conn.close()

    # --- FRONTAL LOBE METHODS ---
    def store_plan(self, plan_id: str, goal_text: str, plan_json: str):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO frontal_goals (goal, status, importance, timestamp) VALUES (?, ?, ?, ?)",
                  (goal_text, "ACTIVE", 5, now))
        goal_id = c.lastrowid
        c.execute("INSERT OR REPLACE INTO frontal_plans (id, goal_id, plan_json, created_at) VALUES (?, ?, ?, ?)",
                  (plan_id, goal_id, plan_json, now))
        conn.commit()
        conn.close()

    def add_reflection(self, task_id: str, outcome: str, evaluation: str, lesson_learned: str):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO frontal_reflections (task_id, outcome, evaluation, lesson_learned, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (task_id, outcome, evaluation, lesson_learned, now))
        conn.commit()
        conn.close()

    # --- PARIETAL LOBE METHODS ---
    def update_context(self, key: str, value: str):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO parietal_context (key, value, updated_at) VALUES (?, ?, ?)",
                  (key, value, now))
        conn.commit()
        conn.close()

    def get_context(self, key: str) -> Optional[str]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM parietal_context WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row["value"] if row else None

    def update_windows(self, active_windows: List[str]):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("DELETE FROM parietal_windows")
        for i, win in enumerate(active_windows):
            c.execute("INSERT INTO parietal_windows (handle, title, is_active, updated_at) VALUES (?, ?, ?, ?)",
                      (str(i), win, 1 if i == 0 else 0, now))
        conn.commit()
        conn.close()

    # --- TEMPORAL LOBE METHODS ---
    def store_conversation(self, user_input: str, bot_response: str, context: str = "", importance_score: float = 1.0):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO temporal_conversations (user_input, bot_response, context, importance_score, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (user_input, bot_response, context, importance_score, now))
        conn.commit()
        conn.close()

    def get_recent_conversations(self, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT user_input, bot_response, context, timestamp FROM temporal_conversations ORDER BY id DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def store_project(self, name: str, path: str, tech_stack: str = "React / Vite / Python"):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO temporal_projects (name, path, tech_stack, last_active) VALUES (?, ?, ?, ?)",
                  (name, path, tech_stack, now))
        conn.commit()
        conn.close()

    def get_last_project(self) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT name, path, tech_stack, last_active FROM temporal_projects ORDER BY last_active DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            return dict(row)
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return {"name": "orionAI", "path": root_dir, "tech_stack": "React / Vite / Python FastAPI", "last_active": datetime.datetime.now().isoformat()}

    def set_preference(self, key: str, value: str):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO temporal_preferences (key, value, updated_at) VALUES (?, ?, ?)",
                  (key, value, now))
        conn.commit()
        conn.close()

    def get_preference(self, key: str, default: str = "") -> str:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT value FROM temporal_preferences WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        return row["value"] if row else default

    # --- OCCIPITAL LOBE METHODS ---
    def record_screen_vision(self, image_path: str, width: int = 1920, height: int = 1080, ocr_text: str = ""):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO occipital_screens (image_path, width, height, timestamp) VALUES (?, ?, ?, ?)",
                  (image_path, width, height, now))
        screen_id = c.lastrowid
        if ocr_text:
            c.execute("INSERT INTO occipital_ocr (screen_id, extracted_text, timestamp) VALUES (?, ?, ?)",
                      (screen_id, ocr_text, now))
        conn.commit()
        conn.close()

cerebrum_db = CerebrumDB()
