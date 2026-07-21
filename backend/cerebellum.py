import os
import sqlite3
import json
import datetime
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("CerebellumDB")

class CerebellumDB:
    """Database 2: Cerebellum (backend/db/cerebellum.db) — Execution, Orchestration, AI Agents, Tool Calls, Workflows, Retries, Performance."""

    def __init__(self, db_path=None):
        if not db_path:
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            db_path = os.path.join(backend_dir, "db", "cerebellum.db")
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

        # --- EXECUTION & AGENT TABLES ---
        c.execute('''CREATE TABLE IF NOT EXISTS agents
                     (name TEXT PRIMARY KEY, agent_type TEXT, description TEXT, capabilities TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS agent_status
                     (name TEXT PRIMARY KEY, status TEXT, current_task_id TEXT, last_active TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS agent_tasks
                     (task_id TEXT PRIMARY KEY, agent_name TEXT, command TEXT, status TEXT, assigned_at TEXT, finished_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS task_queue
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, priority TEXT, payload_json TEXT, queued_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS workflows
                     (id TEXT PRIMARY KEY, name TEXT, goal TEXT, status TEXT, created_at TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS workflow_steps
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, workflow_id TEXT, step_id TEXT, tool_name TEXT, status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS automation_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, action_name TEXT, status TEXT, duration_ms REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS execution_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, log_text TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS tool_calls
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, tool_name TEXT, tool_params TEXT, success INTEGER, output TEXT, error TEXT, duration_ms REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS retry_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, attempt_num INTEGER, error_reason TEXT, adapted_params TEXT, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS performance_metrics
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT, cpu_percent REAL, memory_percent REAL, execution_time_sec REAL, timestamp TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS scheduler
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, cron_expression TEXT, next_run TEXT, status TEXT)''')
        c.execute('''CREATE TABLE IF NOT EXISTS background_jobs
                     (id TEXT PRIMARY KEY, job_name TEXT, status TEXT, started_at TEXT, finished_at TEXT)''')

        # --- LEGACY PRESERVED TABLES ---
        c.execute('''CREATE TABLE IF NOT EXISTS mistakes
                     (timestamp TEXT, action_name TEXT, mistake_desc TEXT, correction TEXT)''')

        conn.commit()
        conn.close()

        # Seed agents if empty
        self._seed_default_agents()

    def _seed_default_agents(self):
        default_agents = [
            ("Desktop Agent", "desktop", "OS app launching and window interaction", "launch_app, fast_paste, observe_window"),
            ("Browser Agent", "browser", "Web browsing and Google searching", "web_search"),
            ("Coding Agent", "coding", "Code generation and editor interaction", "llm_code_generator, write_file"),
            ("File System Agent", "file", "File IO and document reading", "read_document, write_file"),
            ("Terminal Agent", "terminal", "Shell execution", "run_terminal"),
            ("AI Research Agent", "search", "Web search and summarization", "web_search"),
            ("Context Memory Agent", "memory", "Context recall and memory engine", "read_memory")
        ]
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        for name, a_type, desc, caps in default_agents:
            c.execute("INSERT OR IGNORE INTO agents (name, agent_type, description, capabilities) VALUES (?, ?, ?, ?)",
                      (name, a_type, desc, caps))
            c.execute("INSERT OR IGNORE INTO agent_status (name, status, current_task_id, last_active) VALUES (?, ?, ?, ?)",
                      (name, "IDLE", "", now))
        conn.commit()
        conn.close()

    # --- TOOL CALL LOGGING & METRICS ---
    def record_tool_call(self, task_id: str, tool_name: str, tool_params: Dict[str, Any], success: bool, output: str, error: Optional[str] = None, duration_ms: float = 0.0):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO tool_calls (task_id, tool_name, tool_params, success, output, error, duration_ms, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                  (task_id, tool_name, json.dumps(tool_params), 1 if success else 0, output, error or "", duration_ms, now))
        conn.commit()
        conn.close()

    def record_retry(self, task_id: str, attempt_num: int, error_reason: str, adapted_params: Dict[str, Any]):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO retry_history (task_id, attempt_num, error_reason, adapted_params, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (task_id, attempt_num, error_reason, json.dumps(adapted_params), now))
        conn.commit()
        conn.close()

    def update_agent_status(self, agent_name: str, status: str, task_id: str = ""):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT OR REPLACE INTO agent_status (name, status, current_task_id, last_active) VALUES (?, ?, ?, ?)",
                  (agent_name, status, task_id, now))
        conn.commit()
        conn.close()

    def record_performance_metric(self, task_id: str, cpu_percent: float, memory_percent: float, execution_time_sec: float):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO performance_metrics (task_id, cpu_percent, memory_percent, execution_time_sec, timestamp) VALUES (?, ?, ?, ?, ?)",
                  (task_id, cpu_percent, memory_percent, execution_time_sec, now))
        conn.commit()
        conn.close()

    def record_mistake(self, action_name: str, mistake_desc: str, correction: str):
        conn = self.get_connection()
        c = conn.cursor()
        now = datetime.datetime.now().isoformat()
        c.execute("INSERT INTO mistakes (timestamp, action_name, mistake_desc, correction) VALUES (?, ?, ?, ?)",
                  (now, action_name, mistake_desc, correction))
        conn.commit()
        conn.close()

    def get_recent_mistakes(self, limit: int = 5) -> List[Dict[str, Any]]:
        conn = self.get_connection()
        c = conn.cursor()
        c.execute("SELECT timestamp, action_name, mistake_desc, correction FROM mistakes ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = c.fetchall()
        conn.close()
        return [dict(r) for r in rows]

cerebellum_db = CerebellumDB()
