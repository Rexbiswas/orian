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

import logging
from typing import Dict, Any, Optional
from memory.memory_manager import memory_manager
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.memory_agent")

class MemoryAgent:
    """Agent 2 — Memory Agent: Handles memory retrieval, storage, summarization, and context ranking across SQLite, Redis, and Qdrant."""

    def __init__(self):
        self.agent_id = "MemoryAgent"

    async def prepare_cognitive_context(
        self,
        query: str,
        session_id: str,
        user_id: str = "default_user",
        project_id: str = "default_project"
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id}] Preparing cognitive context for query: '{query[:40]}...'")
        
        await event_bus.publish(Event(
            event_type="memory.retrieval.requested",
            sender=self.agent_id,
            data={"session_id": session_id, "query": query}
        ))

        context = await memory_manager.retrieve_context_for_reasoning(
            query=query,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id
        )

        return context

    async def consolidate_memory(self, session_id: str, user_id: str = "default_user", project_id: str = "default_project"):
        logger.info(f"[{self.agent_id}] Consolidating memories for session {session_id}")
        memory_manager.summarize_and_consolidate(session_id, user_id, project_id)

memory_agent = MemoryAgent()
