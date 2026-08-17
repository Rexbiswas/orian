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
from tools.tool_registry import tool_registry

logger = logging.getLogger("orian.automation_agent")

class AutomationAgent:
    """Agent 5 — Automation Agent: Handles system operations, application control, browser, file manager, terminal commands, and permission verification."""

    def __init__(self):
        self.agent_id = "AutomationAgent"

    def evaluate_risk(self, tool_name: str, params: dict) -> str:
        tool = tool_registry.get_tool(tool_name)
        if not tool:
            return "HIGH"
        return tool.permission_level

    async def execute_automation_action(self, tool_name: str, params: dict) -> Dict[str, Any]:
        risk = self.evaluate_risk(tool_name, params)
        logger.info(f"[{self.agent_id}] Executing automation action '{tool_name}' (Risk Level: {risk})")
        return await tool_registry.execute_tool(tool_name, params)

automation_agent = AutomationAgent()
