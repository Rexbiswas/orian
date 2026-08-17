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

import time
import asyncio
import logging
import traceback
from typing import Dict, Any, Callable, Optional
from task_engine import Task, TaskStatus
from tools import tool_registry, ToolResult
from llm_planner import planner
from memory_engine import memory_engine

logger = logging.getLogger("AgentOrchestrator")

class BaseAgent:
    def __init__(self, name: str, agent_type: str):
        self.name = name
        self.agent_type = agent_type

    async def execute_tool_call(self, task: Task, progress_cb: Callable[[Task], None], task_results_map: Dict[str, Any]) -> ToolResult:
        from tools.tool_router import tool_router
        tool_res_router = tool_router.route_and_execute(task.command)
        if tool_res_router.action != "GENERAL_CONVERSATION":
            task.current_action = f"Executing '{tool_res_router.action}' on {tool_res_router.target}"
            task.add_log(f"ToolRouter [{tool_res_router.action}]: {tool_res_router.message}")
            task.progress = 100
            progress_cb(task)
            return ToolResult(tool_res_router.success, tool_res_router.message, error=tool_res_router.error)

        tool = tool_registry.get_tool(task.tool_name)
        if not tool:
            # Fallback tool selection
            if self.agent_type == "browser" or self.agent_type == "search":
                tool = tool_registry.get_tool("web_search")
            elif self.agent_type == "coding":
                tool = tool_registry.get_tool("llm_code_generator")
            elif self.agent_type == "file":
                tool = tool_registry.get_tool("read_document")
            else:
                tool = tool_registry.get_tool("launch_app")

        # Resolve parameter placeholders like {{step_2.result}}
        resolved_params = {}
        for k, v in (task.tool_params or {}).items():
            if isinstance(v, str) and "{{" in v and "}}" in v:
                for parent_id, parent_val in task_results_map.items():
                    placeholder = f"{{{{{parent_id}.result}}}}"
                    if placeholder in v:
                        v = v.replace(placeholder, str(parent_val or ""))
            resolved_params[k] = v

        task.current_action = f"Executing tool '{tool.name}' with params: {resolved_params}"
        task.add_log(f"Tool invoke: {tool.name}({resolved_params})")
        task.progress = 50
        progress_cb(task)

        # Run tool execution in thread executor to prevent event loop blocking
        loop = asyncio.get_running_loop()
        tool_res = await loop.run_in_executor(None, tool.execute, resolved_params)
        return tool_res


class DesktopAgent(BaseAgent):
    def __init__(self):
        super().__init__("TITAN AI", "desktop")


class BrowserAgent(BaseAgent):
    def __init__(self):
        super().__init__("TITAN AI", "browser")


class FileSystemAgent(BaseAgent):
    def __init__(self):
        super().__init__("TITAN AI", "file")


class CodingAgent(BaseAgent):
    def __init__(self):
        super().__init__("GUARDIAN AI", "coding")


class SearchAgent(BaseAgent):
    def __init__(self):
        super().__init__("CORTEX AI", "search")


class TerminalAgent(BaseAgent):
    def __init__(self):
        super().__init__("TITAN AI", "terminal")


class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("CORTEX AI", "memory")

    async def execute_tool_call(self, task: Task, progress_cb: Callable[[Task], None], task_results_map: Dict[str, Any]) -> ToolResult:
        summary = memory_engine.get_context_summary()
        return ToolResult(True, summary, metadata={"memory": True})


class AgentOrchestrator:
    """Central Task Orchestrator managing tool-calling multi-agents with Observation Feedback Loops & Re-Planning."""

    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {
            "desktop": DesktopAgent(),
            "browser": BrowserAgent(),
            "file": FileSystemAgent(),
            "coding": CodingAgent(),
            "search": SearchAgent(),
            "terminal": TerminalAgent(),
            "memory": MemoryAgent()
        }

    async def run_task(self, task: Task, progress_cb: Callable[[Task], None], task_results_map: Dict[str, Any]):
        from brain_manager import brain_manager
        agent = self.agents.get(task.agent_type, self.agents["desktop"])
        task.started_at = time.time()
        task.status = TaskStatus.RUNNING
        task.add_log(f"Assigned to {agent.name} [{agent.agent_type}]")
        brain_manager.update_agent_state(agent.name, "BUSY", task.id)
        progress_cb(task)

        while task.retry_count <= task.max_retries:
            try:
                start_t = time.time()
                # Execute Tool Call
                tool_res: ToolResult = await agent.execute_tool_call(task, progress_cb, task_results_map)
                duration_ms = (time.time() - start_t) * 1000.0

                # Record in Cerebellum via BrainManager
                brain_manager.record_tool_call(
                    task.id,
                    task.tool_name,
                    task.tool_params,
                    tool_res.success,
                    tool_res.output,
                    tool_res.error,
                    duration_ms
                )
                
                # Layer 7: Observation Inspection
                task.observation = tool_res.output if tool_res.success else tool_res.error
                task.add_log(f"Observation Result: success={tool_res.success}, output='{tool_res.output[:200]}'")

                if tool_res.success:
                    task.status = TaskStatus.COMPLETED
                    task.progress = 100
                    task.finished_at = time.time()
                    task.result = tool_res.output
                    task.current_action = f"Completed step ({tool_res.output[:60]}...)"
                    task.add_log("Step finished successfully.")
                    task_results_map[task.id] = tool_res.output
                    brain_manager.update_agent_state(agent.name, "IDLE", "")
                    progress_cb(task)
                    return
                else:
                    # Layer 7: Observation Failed -> Trigger Re-Planner Node
                    task.retry_count += 1
                    task.add_log(f"Observation Failure (Attempt {task.retry_count}/{task.max_retries}): {tool_res.error}")

                    if task.retry_count <= task.max_retries:
                        task.current_action = f"Observing error & Re-planning step ({task.retry_count}/{task.max_retries})..."
                        progress_cb(task)
                        await asyncio.sleep(0.5)

                        # LLM Re-Planner adapts the tool parameters or tool choice
                        replanned_step = planner.replan_failed_step(task, tool_res)
                        if replanned_step:
                            task.command = replanned_step.command
                            task.tool_name = replanned_step.tool_name
                            task.tool_params = replanned_step.tool_params
                            task.add_log(f"LLM Re-Planner adapted step -> Tool: '{task.tool_name}', Params: {task.tool_params}")
                    else:
                        task.status = TaskStatus.FAILED
                        task.error = tool_res.error
                        task.finished_at = time.time()
                        task.current_action = f"Step failed after {task.max_retries} attempts: {tool_res.error}"
                        task.add_log("Execution terminated permanently.")
                        brain_manager.update_agent_state(agent.name, "ERROR", task.id)
                        progress_cb(task)
                        return


            except Exception as e:
                task.retry_count += 1
                err_msg = f"Orchestrator Exception: {str(e)}\n{traceback.format_exc()}"
                logger.error(err_msg)
                task.add_log(f"Execution fault: {str(e)}")

                if task.retry_count > task.max_retries:
                    task.status = TaskStatus.FAILED
                    task.error = str(e)
                    task.finished_at = time.time()
                    task.current_action = f"Task failed: {str(e)}"
                    progress_cb(task)
                    return

orchestrator = AgentOrchestrator()
