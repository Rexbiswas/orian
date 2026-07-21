import os
import time
import json
import psutil
import datetime
import threading
import logging
from typing import Dict, Any, List, Optional
from cerebrum import cerebrum_db, CerebrumDB
from cerebellum import cerebellum_db, CerebellumDB
from brainstem import brainstem_db, BrainstemDB

logger = logging.getLogger("BrainManager")

class BrainManager:
    """Central Cognitive Controller coordinating Cerebrum (cerebrum.db), Cerebellum (cerebellum.db), and Brainstem (brainstem.db)."""

    def __init__(self):
        self.cerebrum: CerebrumDB = cerebrum_db
        self.cerebellum: CerebellumDB = cerebellum_db
        self.brainstem: BrainstemDB = brainstem_db
        self._cache: Dict[str, Any] = {}
        self._is_running = False
        self._consolidation_thread: Optional[threading.Thread] = None

    def start_background_services(self):
        if not self._is_running:
            self._is_running = True
            self._consolidation_thread = threading.Thread(target=self._consolidation_loop, daemon=True)
            self._consolidation_thread.start()
            logger.info("Brain Manager background memory consolidation loop active.")

    # --- PIPELINE STEP 1: CONTEXT RETRIEVAL ---
    def get_cognitive_context(self) -> str:
        """Retrieves combined memory across Cerebrum lobes and Cerebellum history for LLM Reasoning."""
        proj = self.cerebrum.get_last_project()
        convs = self.cerebrum.get_recent_conversations(3)
        user_name = self.cerebrum.get_preference("user_nickname", "Master")
        mistakes = self.cerebellum.get_recent_mistakes(2)

        conv_summary = " | ".join([f"User: '{c['user_input']}' -> Bot: '{c['bot_response']}'" for c in convs]) if convs else "None"
        mistake_summary = " | ".join([f"Mistake on '{m['action_name']}': {m['correction']}" for m in mistakes]) if mistakes else "None"

        context_str = (
            f"User Nickname: {user_name}\n"
            f"Active Project: '{proj['name']}' ({proj['path']})\n"
            f"Tech Stack: {proj['tech_stack']}\n"
            f"Recent Memory: {conv_summary}\n"
            f"Learned Corrections: {mistake_summary}"
        )
        return context_str

    # --- PIPELINE STEP 2: USER INTERACTION & MEMORY RECORDING ---
    def record_interaction(self, user_input: str, bot_response: str, context: str = "CHAT"):
        self.cerebrum.store_conversation(user_input, bot_response, context)
        self.brainstem.record_security_event("USER_INTERACTION", "API", f"Processed input ({len(user_input)} chars)")

    def record_execution_plan(self, plan_id: str, goal_text: str, plan_json: str):
        self.cerebrum.store_plan(plan_id, goal_text, plan_json)

    def record_tool_call(self, task_id: str, tool_name: str, tool_params: Dict[str, Any], success: bool, output: str, error: Optional[str] = None, duration_ms: float = 0.0):
        self.cerebellum.record_tool_call(task_id, tool_name, tool_params, success, output, error, duration_ms)
        if not success and error:
            self.cerebellum.record_mistake(tool_name, error, f"Adapted tool params or fallback for task {task_id}")

    def record_reflection(self, task_id: str, outcome: str, evaluation: str, lesson_learned: str):
        self.cerebrum.add_reflection(task_id, outcome, evaluation, lesson_learned)

    def update_agent_state(self, agent_name: str, status: str, task_id: str = ""):
        self.cerebellum.update_agent_status(agent_name, status, task_id)
        try:
            from task_scheduler import ws_manager
            import asyncio
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(ws_manager.broadcast({
                    "event": "AGENT_STATUS_UPDATED",
                    "agent": agent_name,
                    "status": status,
                    "task_id": task_id
                }))
        except Exception:
            pass

    # --- BRAINSTEM MONITORING & TELEMETRY ---
    def update_system_vitals(self) -> Dict[str, Any]:
        cpu = round(psutil.cpu_percent(), 1)
        mem = round(psutil.virtual_memory().percent, 1)
        disk = round(psutil.disk_usage('/').percent, 1)
        self.brainstem.record_health(cpu, mem, disk)
        return {"cpu_usage": cpu, "memory_usage": mem, "disk_usage": disk}

    def get_brain_status_summary(self) -> Dict[str, Any]:
        vitals = self.update_system_vitals()
        proj = self.cerebrum.get_last_project()
        return {
            "success": True,
            "system_vitals": vitals,
            "active_project": proj,
            "databases": {
                "cerebrum": "ONLINE (backend/db/cerebrum.db)",
                "cerebellum": "ONLINE (backend/db/cerebellum.db)",
                "brainstem": "ONLINE (backend/db/brainstem.db)"
            }
        }

    # --- BACKGROUND MEMORY CONSOLIDATION ---
    def _consolidation_loop(self):
        while self._is_running:
            try:
                time.sleep(60) # Consolidate memory every 60s
                self.update_system_vitals()
                self.brainstem.update_voice_engine_status("WebSpeech/ElevenLabs", "NOpBlnGInO9m6vDvFkFC", "IDLE", False)
            except Exception as e:
                logger.error(f"Memory consolidation loop fault: {e}")


brain_manager = BrainManager()
brain_manager.start_background_services()
