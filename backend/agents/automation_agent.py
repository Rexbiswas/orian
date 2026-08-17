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
