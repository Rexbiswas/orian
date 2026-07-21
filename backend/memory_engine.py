import os
import logging
from typing import Dict, Any, List, Optional
from brain_manager import brain_manager

logger = logging.getLogger("MemoryEngine")

class MemoryEngine:
    """Facade wrapping Memory Operations to route through BrainManager."""

    def record_project(self, name: str, path: str, tech_stack: str = "React/Node"):
        brain_manager.cerebrum.store_project(name, path, tech_stack)

    def get_last_active_project(self) -> Dict[str, Any]:
        return brain_manager.cerebrum.get_last_project()

    def set_preference(self, key: str, value: str):
        brain_manager.cerebrum.set_preference(key, value)

    def get_context_summary(self) -> str:
        return brain_manager.get_cognitive_context()

memory_engine = MemoryEngine()
