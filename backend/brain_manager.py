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
from brainstream import brainstream_db, BrainstreamDB

logger = logging.getLogger("BrainManager")

class BrainManager:
    """Central Cognitive Controller coordinating Cerebrum (cerebrum.db), Cerebellum (cerebellum.db), Brainstem (brainstem.db), and Brainstream (brainstream.db)."""

    def __init__(self):
        self.cerebrum: CerebrumDB = cerebrum_db
        self.cerebellum: CerebellumDB = cerebellum_db
        self.brainstem: BrainstemDB = brainstem_db
        self.brainstream: BrainstreamDB = brainstream_db
        self._cache: Dict[str, Any] = {}
        self._is_running = False
        self._consolidation_thread: Optional[threading.Thread] = None

    def start_background_services(self):
        if not self._is_running:
            self._is_running = True
            self._consolidation_thread = threading.Thread(target=self._consolidation_loop, daemon=True)
            self._consolidation_thread.start()
            logger.info("Brain Manager background memory consolidation & thought stream loop active.")

    # --- PIPELINE STEP 1: CONTEXT RETRIEVAL ---
    def get_cognitive_context(self) -> str:
        """Retrieves combined memory across Cerebrum lobes and Brainstream thought history for LLM Reasoning."""
        proj = self.cerebrum.get_last_project()
        convs = self.cerebrum.get_recent_conversations(3)
        user_name = self.cerebrum.get_preference("user_nickname", "Master")
        mistakes = self.cerebellum.get_recent_mistakes(2)
        thoughts = self.brainstream.get_recent_thoughts(2)

        conv_summary = " | ".join([f"User: '{c['user_input']}' -> Bot: '{c['bot_response']}'" for c in convs]) if convs else "None"
        mistake_summary = " | ".join([f"Mistake on '{m['action_name']}': {m['correction']}" for m in mistakes]) if mistakes else "None"
        thought_summary = " | ".join([f"Thought [{t['thought_type']}]: {t['content']}" for t in thoughts]) if thoughts else "None"

        context_str = (
            f"User Nickname: {user_name}\n"
            f"Active Project: '{proj['name']}' ({proj['path']})\n"
            f"Tech Stack: {proj['tech_stack']}\n"
            f"Cognitive Thought Stream: {thought_summary}\n"
            f"Recent Memory: {conv_summary}\n"
            f"Learned Corrections: {mistake_summary}"
        )
        return context_str

    # --- PIPELINE STEP 2: USER INTERACTION & MEMORY RECORDING ---
    def record_interaction(self, user_input: str, bot_response: str, context: str = "CHAT"):
        self.cerebrum.store_conversation(user_input, bot_response, context)
        self.brainstream.record_thought(f"User intent received: '{user_input}'", "INTENT_PERCEPTION")
        self.brainstem.record_security_event("USER_INTERACTION", "API", f"Processed input ({len(user_input)} chars)")

    def record_execution_plan(self, plan_id: str, goal_text: str, plan_json: str):
        self.cerebrum.store_plan(plan_id, goal_text, plan_json)
        self.brainstream.record_thought(f"Formulated cognitive execution plan for goal: '{goal_text}'", "PLAN_DECOMPOSITION", task_id=plan_id)

    def record_tool_call(self, task_id: str, tool_name: str, tool_params: Dict[str, Any], success: bool, output: str, error: Optional[str] = None, duration_ms: float = 0.0):
        self.cerebellum.record_tool_call(task_id, tool_name, tool_params, success, output, error, duration_ms)
        self.brainstream.record_action_signal(tool_name, str(tool_params), "SUCCESS" if success else "FAILED")
        if not success and error:
            self.cerebellum.record_mistake(tool_name, error, f"Adapted tool params or fallback for task {task_id}")
            self.brainstream.record_thought(f"Action '{tool_name}' failed with error: {error}", "ERROR_OBSERVATION", task_id=task_id)

    def record_reflection(self, task_id: str, outcome: str, evaluation: str, lesson_learned: str):
        self.cerebrum.add_reflection(task_id, outcome, evaluation, lesson_learned)
        self.brainstream.record_thought(f"Cognitive reflection on step: {lesson_learned}", "SELF_REFLECTION", task_id=task_id)

    def update_agent_state(self, agent_name: str, status: str, task_id: str = ""):
        self.cerebellum.update_agent_status(agent_name, status, task_id)

    # --- BRAINSTEM MONITORING & TELEMETRY ---
    def update_system_vitals(self) -> Dict[str, Any]:
        cpu = round(psutil.cpu_percent(), 1)
        mem = round(psutil.virtual_memory().percent, 1)
        disk = round(psutil.disk_usage('/').percent, 1)
        self.brainstem.record_health(cpu, mem, disk)
        self.brainstream.record_telemetry_event("SYSTEM_VITALS", {"cpu": cpu, "memory": mem, "disk": disk})
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
                "brainstem": "ONLINE (backend/db/brainstem.db)",
                "brainstream": "ONLINE (backend/db/brainstream.db)"
            }
        }

    # --- BACKGROUND MEMORY CONSOLIDATION & SYNAPTIC SYNC ---
    def _consolidation_loop(self):
        while self._is_running:
            try:
                time.sleep(60) # Consolidate memory & sync synaptic signals every 60s
                self.update_system_vitals()
                self.brainstem.update_voice_engine_status("WebSpeech/ElevenLabs", "NOpBlnGInO9m6vDvFkFC", "IDLE", False)
                self.brainstream.record_synaptic_sync("CONSOLIDATION", "brainstream.db", "cerebrum.db", 1)
            except Exception as e:
                logger.error(f"Memory consolidation loop fault: {e}")


brain_manager = BrainManager()
brain_manager.start_background_services()
