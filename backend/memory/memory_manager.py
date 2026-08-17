import logging
import time
from typing import List, Dict, Any, Optional
from memory.sqlite_store import sqlite_store
from memory.redis_store import redis_store
from memory.qdrant_store import qdrant_store
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.memory_manager")

class MemoryManager:
    """Central Memory Manager coordinating SQLite (Structured), Redis (Working), and Qdrant (Semantic Long-Term)."""

    def __init__(self):
        self.sqlite = sqlite_store
        self.redis = redis_store
        self.qdrant = qdrant_store

    async def initialize_session(self, session_id: str, user_id: str = "default_user", project_id: str = "default_project") -> Dict[str, Any]:
        """Initializes session working context in Redis and loads historical context."""
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "start_time": time.time(),
            "active_tasks": [],
            "current_focus": "idle"
        }
        self.redis.set_working_context(session_id, "session_state", session_data)
        logger.info(f"Initialized Memory Session: {session_id}")
        return session_data

    async def record_interaction(
        self,
        session_id: str,
        user_input: str,
        agent_response: str,
        user_id: str = "default_user",
        project_id: str = "default_project",
        metadata: dict = None
    ):
        """Records a user-agent exchange into SQLite structured log and updates Redis working context."""
        meta = metadata or {}
        
        # 1. SQLite System-of-Record
        user_msg_id = self.sqlite.add_message(session_id, "user", user_input, meta)
        agent_msg_id = self.sqlite.add_message(session_id, "assistant", agent_response, meta)

        # 2. Redis Working Memory update
        recent_history = self.sqlite.get_conversation_history(session_id, limit=10)
        self.redis.set_working_context(session_id, "conversation_history", recent_history)

        # 3. Check for memory promotion to Qdrant if user provided explicit instructions or key knowledge
        if any(kw in user_input.lower() for kw in ["remember", "prefer", "always", "note that", "architecture", "key rule"]):
            mem_id = self.qdrant.store_memory(
                content=f"User preference/fact: {user_input}",
                memory_type="user_preference",
                importance=1.5,
                user_id=user_id,
                project_id=project_id,
                source="user_explicit"
            )
            logger.info(f"Promoted memory to Qdrant: {mem_id}")

        await event_bus.publish(Event(
            event_type="memory.updated",
            sender="MemoryManager",
            data={"session_id": session_id, "user_msg_id": user_msg_id, "agent_msg_id": agent_msg_id}
        ))

    async def retrieve_context_for_reasoning(
        self,
        query: str,
        session_id: str,
        user_id: str = "default_user",
        project_id: str = "default_project",
        limit_semantic: int = 5
    ) -> Dict[str, Any]:
        """Retrieves structured, working, and semantic memories for Reasoning Agent context assembly."""
        
        # 1. Redis Working Memory (Short-Term Conversation & Session State)
        working_conv = self.redis.get_working_context(session_id, "conversation_history") or []
        session_state = self.redis.get_working_context(session_id, "session_state") or {}

        # 2. Qdrant Semantic Long-Term Memory (Relevant docs, preferences, past experiences)
        semantic_memories = self.qdrant.search_memories(
            query=query,
            limit=limit_semantic,
            user_id=user_id,
            project_id=project_id
        )

        # 3. SQLite Recent System-of-Record (Projects & User details)
        recent_messages = self.sqlite.get_conversation_history(session_id, limit=6)

        context_package = {
            "query": query,
            "session_id": session_id,
            "user_id": user_id,
            "project_id": project_id,
            "working_memory": {
                "recent_conversation": working_conv[-6:],
                "session_state": session_state
            },
            "long_term_semantic_memories": semantic_memories,
            "recent_messages": recent_messages
        }

        await event_bus.publish(Event(
            event_type="memory.retrieval.completed",
            sender="MemoryManager",
            data={"session_id": session_id, "semantic_count": len(semantic_memories)}
        ))

        return context_package

    def summarize_and_consolidate(self, session_id: str, user_id: str = "default_user", project_id: str = "default_project"):
        """Consolidates short-term working context into long-term semantic memory summary."""
        history = self.sqlite.get_conversation_history(session_id, limit=50)
        if not history:
            return

        text_content = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
        summary_text = f"Conversation Session {session_id} Summary: {text_content[:400]}..."

        self.qdrant.store_memory(
            content=summary_text,
            memory_type="conversation_summary",
            importance=1.0,
            user_id=user_id,
            project_id=project_id,
            source="memory_consolidation"
        )
        logger.info(f"Consolidated memory for session {session_id}")

    def get_memory_stats() -> Dict[str, Any]:
        """Provides telemetry for UI Memory Activity monitor."""
        conn = self.sqlite.get_connection()
        c = conn.cursor()
        msg_count = c.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        task_count = c.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        proj_count = c.execute("SELECT COUNT(*) FROM projects").fetchone()[0]
        conn.close()

        return {
            "sqlite": {
                "status": "connected",
                "messages_count": msg_count,
                "tasks_count": task_count,
                "projects_count": proj_count
            },
            "redis": {
                "status": "active",
                "is_real": self.redis.is_real_redis
            },
            "qdrant": {
                "status": "active",
                "is_real": self.qdrant.is_real_qdrant
            }
        }

memory_manager = MemoryManager()
