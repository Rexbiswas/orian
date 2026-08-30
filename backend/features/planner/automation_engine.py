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
import time
import logging
from typing import Dict, List, Any, Optional

logger = logging.getLogger("AutomationEngine")

class AutomationItem:
    def __init__(
        self,
        id: str,
        name: str,
        category: str,
        initial_val: int = 0,
        initial_status: str = "Idle",
        color: str = "bg-cyan-400",
        description: str = "",
        interval: int = 45
    ):
        self.id = id
        self.name = name
        self.category = category
        self.val = initial_val
        self.status = initial_status  # "Running", "Completed", "Idle", "Paused", "Error"
        self.color = color
        self.description = description
        self.interval = interval
        self.last_run = time.time()
        self.logs: List[Dict[str, Any]] = []
        self.execution_count = 0
        self._running_task: Optional[asyncio.Task] = None
        self._paused = False

    def add_log(self, text: str):
        entry = {
            "timestamp": time.strftime("%H:%M:%S"),
            "message": text
        }
        self.logs.append(entry)
        if len(self.logs) > 30:
            self.logs.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "val": self.val,
            "status": self.status,
            "color": self.color,
            "description": self.description,
            "logs": self.logs[-5:],
            "execution_count": self.execution_count,
            "last_run": time.strftime("%H:%M:%S", time.localtime(self.last_run))
        }


class AutomationEngine:
    """Python Backend Automation Orchestrator for Real-Time HUD & Background Operations."""

    def __init__(self):
        self.automations: Dict[str, AutomationItem] = {
            "web_search": AutomationItem(
                id="web_search",
                name="Web Search Automation",
                category="INTELLIGENCE",
                initial_val=75,
                initial_status="Running",
                color="bg-cyan-400",
                description="Crawling real-time indices, security alerts, and threat bulletins.",
                interval=30
            ),
            "email_draft": AutomationItem(
                id="email_draft",
                name="Email Draft Generator",
                category="COMMUNICATION",
                initial_val=60,
                initial_status="Running",
                color="bg-cyan-400",
                description="Synthesizing project reports & generating neural email drafts.",
                interval=45
            ),
            "file_organizer": AutomationItem(
                id="file_organizer",
                name="File Organizer",
                category="FILESYSTEM",
                initial_val=100,
                initial_status="Completed",
                color="bg-emerald-400",
                description="Indexed workspace artifacts and cleaned temporary system staging.",
                interval=60
            ),
            "meeting_assistant": AutomationItem(
                id="meeting_assistant",
                name="AI Meeting Assistant",
                category="PRODUCTIVITY",
                initial_val=0,
                initial_status="Idle",
                color="bg-slate-700",
                description="Standing by to transcribe voice streams and aggregate action items.",
                interval=90
            ),
            "data_extractor": AutomationItem(
                id="data_extractor",
                name="Data Extractor",
                category="ANALYTICS",
                initial_val=40,
                initial_status="Running",
                color="bg-cyan-400",
                description="Extracting structured entities from memory database & telemetry logs.",
                interval=40
            ),
            "system_optimizer": AutomationItem(
                id="system_optimizer",
                name="System Cache Optimizer",
                category="SYSTEM",
                initial_val=85,
                initial_status="Running",
                color="bg-purple-400",
                description="Defragmenting memory pipelines and trimming runtime buffers.",
                interval=50
            )
        }
        self.is_running = False
        self._bg_loop_task: Optional[asyncio.Task] = None

    def start(self):
        if not self.is_running:
            self.is_running = True
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    self._bg_loop_task = asyncio.create_task(self._background_cycle())
            except RuntimeError:
                pass
            logger.info("AutomationEngine background cycle started.")

    async def _broadcast_update(self, item: AutomationItem):
        try:
            from features.planner.task_scheduler import ws_manager
            await ws_manager.broadcast({
                "event": "AUTOMATION_UPDATED",
                "automation": item.to_dict(),
                "all_automations": self.get_all()
            })
        except Exception as e:
            logger.debug(f"Broadcast exception: {e}")

    async def _background_cycle(self):
        """Gradually updates running automations and cycles completed ones."""
        while self.is_running:
            try:
                await asyncio.sleep(2.5)
                for item in self.automations.values():
                    if item.status == "Running":
                        item.val = min(100, item.val + 5)
                        if item.val >= 100:
                            item.status = "Completed"
                            item.color = "bg-emerald-400"
                            item.execution_count += 1
                            item.last_run = time.time()
                            item.add_log("Execution completed successfully.")
                        await self._broadcast_update(item)
                    elif item.status == "Completed":
                        # If completed for more than interval, cycle back to running
                        if time.time() - item.last_run > item.interval:
                            item.status = "Running"
                            item.val = 5
                            item.color = "bg-cyan-400"
                            item.add_log(f"Auto-triggered periodic run: {item.name}")
                            await self._broadcast_update(item)
            except Exception as e:
                logger.error(f"Error in automation cycle: {e}")
                await asyncio.sleep(5)

    def get_all(self) -> List[Dict[str, Any]]:
        return [item.to_dict() for item in self.automations.values()]

    async def trigger(self, automation_id: str) -> Dict[str, Any]:
        item = self.automations.get(automation_id)
        if not item:
            return {"success": False, "error": f"Automation {automation_id} not found."}

        item.status = "Running"
        item.val = 5
        item.color = "bg-cyan-400"
        item.last_run = time.time()
        item.add_log(f"Manual trigger initiated.")
        await self._broadcast_update(item)
        return {"success": True, "automation": item.to_dict()}

    async def pause(self, automation_id: str) -> Dict[str, Any]:
        item = self.automations.get(automation_id)
        if not item:
            return {"success": False, "error": f"Automation {automation_id} not found."}

        if item.status == "Running":
            item.status = "Paused"
            item.color = "bg-amber-400"
            item.add_log("Automation paused by operator.")
        elif item.status == "Paused":
            item.status = "Running"
            item.color = "bg-cyan-400"
            item.add_log("Automation resumed.")

        await self._broadcast_update(item)
        return {"success": True, "automation": item.to_dict()}

    async def reset(self, automation_id: str) -> Dict[str, Any]:
        item = self.automations.get(automation_id)
        if not item:
            return {"success": False, "error": f"Automation {automation_id} not found."}

        item.status = "Idle"
        item.val = 0
        item.color = "bg-slate-700"
        item.add_log("Automation reset to Idle.")
        await self._broadcast_update(item)
        return {"success": True, "automation": item.to_dict()}

automation_engine = AutomationEngine()
