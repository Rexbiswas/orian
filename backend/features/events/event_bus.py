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

import asyncio
import logging
import time
from typing import Callable, Dict, List, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("orian.event_bus")

class Event(BaseModel):
    event_type: str
    data: Dict[str, Any] = Field(default_factory=dict)
    sender: str = "system"
    timestamp: float = Field(default_factory=time.time)
    request_id: Optional[str] = None

class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], Any]]] = {}
        self._history: List[Event] = []

    def subscribe(self, event_type: str, callback: Callable[[Event], Any]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed callback to {event_type}")

    async def publish(self, event: Event):
        self._history.append(event)
        if len(self._history) > 1000:
            self._history.pop(0)

        logger.info(f"[EVENT] {event.event_type} (from: {event.sender})")
        
        callbacks = self._subscribers.get(event.event_type, [])
        wildcard_callbacks = self._subscribers.get("*", [])

        all_callbacks = callbacks + wildcard_callbacks
        for cb in all_callbacks:
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event)
                else:
                    cb(event)
            except Exception as e:
                logger.error(f"Error executing event subscriber for {event.event_type}: {e}", exc_info=True)

    def get_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        return [e.model_dump() for e in self._history[-limit:]]

# Global singleton event bus
event_bus = EventBus()
