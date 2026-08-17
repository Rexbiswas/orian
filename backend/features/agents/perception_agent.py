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
import time
import os
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.perception_agent")

class StructuredIntentContext(BaseModel):
    input_type: str = "text"  # text, voice, image, file, screenshot
    raw_input: str
    normalized_intent: str
    extracted_entities: Dict[str, Any] = Field(default_factory=dict)
    environment_context: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)

class PerceptionAgent:
    """Agent 1 — Perception Agent: Converts voice, text, images, files, screenshots into normalized intent & context."""

    def __init__(self):
        self.agent_id = "PerceptionAgent"

    async def process_input(
        self,
        user_input: str,
        input_type: str = "text",
        media_path: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> StructuredIntentContext:
        logger.info(f"[{self.agent_id}] Processing perception input type '{input_type}'")

        env_ctx = {
            "os": os.name,
            "cwd": os.getcwd(),
            "timestamp": time.time(),
            "has_media": bool(media_path)
        }

        extracted_entities = {}
        normalized = user_input.strip()

        # Handle file input perception
        if input_type == "file" and media_path and os.path.exists(media_path):
            with open(media_path, "r", encoding="utf-8", errors="ignore") as f:
                file_text = f.read(2000)
            extracted_entities["file_snippet"] = file_text
            normalized = f"Process file ({media_path}): {user_input}"

        # Handle screenshot / vision perception
        elif input_type in ["image", "screenshot"] and media_path:
            extracted_entities["image_path"] = media_path
            normalized = f"Analyze image ({media_path}): {user_input}"

        # Entity extraction heuristics
        if "react" in normalized.lower():
            extracted_entities["framework"] = "react"
        if "python" in normalized.lower():
            extracted_entities["language"] = "python"

        intent = StructuredIntentContext(
            input_type=input_type,
            raw_input=user_input,
            normalized_intent=normalized,
            extracted_entities=extracted_entities,
            environment_context=env_ctx
        )

        await event_bus.publish(Event(
            event_type="perception.completed",
            sender=self.agent_id,
            data=intent.model_dump()
        ))

        return intent

perception_agent = PerceptionAgent()
