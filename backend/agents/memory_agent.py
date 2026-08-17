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
