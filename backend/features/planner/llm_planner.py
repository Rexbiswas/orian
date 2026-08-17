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

import json
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from tools import tool_registry, ToolResult
from llm_core import llm

logger = logging.getLogger("LLMPlanner")

class PlannedStep:
    def __init__(
        self,
        step_id: str,
        command: str,
        tool_name: str,
        tool_params: Dict[str, Any],
        agent_type: str = "desktop",
        priority: str = "HIGH",
        dependencies: Optional[List[str]] = None
    ):
        self.step_id = step_id
        self.command = command
        self.tool_name = tool_name
        self.tool_params = tool_params
        self.agent_type = agent_type
        self.priority = priority
        self.dependencies = dependencies or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "command": self.command,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "agent_type": self.agent_type,
            "priority": self.priority,
            "dependencies": self.dependencies
        }


class ExecutionPlan:
    def __init__(self, goal: str, steps: List[PlannedStep]):
        self.goal = goal
        self.steps = steps

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "steps": [s.to_dict() for s in self.steps]
        }


class LLMPlanner:
    """LLM Reasoning Engine for Goal Decomposition, Tool Selection & Dynamic Re-planning."""

    SYSTEM_PROMPT = """You are the Senior Cognitive Planner of OrionAI, an autonomous desktop AI agent framework.
Your task is to understand user intent, decompose high-level goals into structured sub-tasks, select appropriate tools, and assign specialized agents.

Available Tools Schema:
{tools_schema}

Context & Memory:
{context_memory}

User Request: "{user_prompt}"

Return ONLY a valid JSON object with the following schema, with no conversational preamble:
{{
  "goal": "<Summary of high-level goal>",
  "steps": [
    {{
      "step_id": "step_1",
      "command": "<Action description>",
      "tool_name": "<One of available tool names>",
      "tool_params": {{ "<param_name>": "<param_value>" }},
      "agent_type": "desktop|browser|coding|file|terminal|search|memory",
      "priority": "CRITICAL|HIGH|MEDIUM|LOW",
      "dependencies": []
    }}
  ]
}}
"""

    @classmethod
    def decompose_goal(cls, user_prompt: str, context_memory: str = "") -> ExecutionPlan:
        from brain_manager import brain_manager
        tools_schema_json = json.dumps(tool_registry.get_all_schemas(), indent=2)
        prompt = cls.SYSTEM_PROMPT.format(
            tools_schema=tools_schema_json,
            context_memory=context_memory or "None",
            user_prompt=user_prompt
        )

        plan = None
        try:
            response_text = llm.generate_response(user_prompt, context=prompt)
            plan = cls._parse_json_plan(response_text, user_prompt)
        except Exception as e:
            logger.warn(f"LLM Reasoning JSON parsing fault: {e}. Falling back to structured heuristic reasoner.")

        if not plan or not plan.steps:
            plan = cls._heuristic_reasoner(user_prompt)

        # Record plan in Cerebrum via BrainManager
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        brain_manager.record_execution_plan(plan_id, user_prompt, json.dumps(plan.to_dict()))

        return plan

    @classmethod
    def replan_failed_step(cls, failed_task: Any, tool_result: ToolResult, context_memory: str = "") -> Optional[PlannedStep]:
        from brain_manager import brain_manager
        prompt = (
            f"OrionAI Action Failure Recovery.\n"
            f"Goal/Command: '{failed_task.command}'\n"
            f"Used Tool: '{failed_task.tool_name}' with params: {failed_task.tool_params}\n"
            f"Error Observation: '{tool_result.error or tool_result.output}'\n"
            f"Suggest an alternative tool or modified parameters to fix this step.\n"
            f"Return ONLY a JSON object representing the single corrected step: "
            f'{{"step_id": "{failed_task.id}_retry", "command": "<fixed command>", "tool_name": "<tool>", "tool_params": {{}}, "agent_type": "desktop", "priority": "HIGH", "dependencies": []}}'
        )

        try:
            resp = llm.generate_response("Re-plan failed step", context=prompt)
            json_match = re.search(r"\{.*\}", resp, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                step = PlannedStep(
                    step_id=data.get("step_id", f"{failed_task.id}_retry"),
                    command=data.get("command", failed_task.command),
                    tool_name=data.get("tool_name", failed_task.tool_name),
                    tool_params=data.get("tool_params", failed_task.tool_params),
                    agent_type=data.get("agent_type", failed_task.agent_type),
                    priority=data.get("priority", "HIGH"),
                    dependencies=[]
                )
                brain_manager.record_reflection(
                    failed_task.id,
                    "RE_PLANNED",
                    f"Observation fault: {tool_result.error or tool_result.output}",
                    f"Re-planned to tool '{step.tool_name}' with params: {step.tool_params}"
                )
                return step
        except Exception as e:
            logger.error(f"Re-planner fault: {e}")
        return None


    @classmethod
    def _parse_json_plan(cls, text: str, fallback_prompt: str) -> Optional[ExecutionPlan]:
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if not json_match:
            return None
        
        data = json.loads(json_match.group(0))
        goal = data.get("goal", fallback_prompt)
        raw_steps = data.get("steps", [])

        steps = []
        for s in raw_steps:
            steps.append(PlannedStep(
                step_id=s.get("step_id", f"step_{len(steps)+1}"),
                command=s.get("command", fallback_prompt),
                tool_name=s.get("tool_name", "launch_app"),
                tool_params=s.get("tool_params", {}),
                agent_type=s.get("agent_type", "desktop"),
                priority=s.get("priority", "HIGH"),
                dependencies=s.get("dependencies", [])
            ))
        return ExecutionPlan(goal, steps)

    @classmethod
    def _heuristic_reasoner(cls, prompt: str) -> ExecutionPlan:
        """High-fidelity local reasoning engine when offline or no API key is set."""
        p_lower = prompt.lower()
        steps = []

        if "notepad" in p_lower:
            steps.append(PlannedStep(
                step_id="step_1",
                command="Launch Notepad application",
                tool_name="launch_app",
                tool_params={"app_name": "notepad"},
                agent_type="desktop"
            ))

            if "write" in p_lower or "html" in p_lower or "code" in p_lower:
                lang = "html" if "html" in p_lower else "python" if "python" in p_lower else "text"
                steps.append(PlannedStep(
                    step_id="step_2",
                    command=f"Generate dynamic {lang.upper()} code payload",
                    tool_name="llm_code_generator",
                    tool_params={"prompt": prompt, "language": lang},
                    agent_type="coding",
                    dependencies=["step_1"]
                ))
                steps.append(PlannedStep(
                    step_id="step_3",
                    command="Paste generated code into Notepad in real time",
                    tool_name="fast_paste",
                    tool_params={"app_title": "notepad", "text": "{{step_2.result}}"},
                    agent_type="desktop",
                    dependencies=["step_2"]
                ))

        elif "chrome" in p_lower or "search" in p_lower or "browse" in p_lower:
            query = prompt.replace("open chrome and", "").replace("search for", "").replace("search", "").strip() or "Latest AI News"
            steps.append(PlannedStep(
                step_id="step_1",
                command=f"Perform real-time web search for '{query}'",
                tool_name="web_search",
                tool_params={"query": query},
                agent_type="browser"
            ))

        elif "vscode" in p_lower or "react" in p_lower or "project" in p_lower or "build" in p_lower:
            steps.append(PlannedStep(
                step_id="step_1",
                command="Launch Visual Studio Code IDE",
                tool_name="launch_app",
                tool_params={"app_name": "vscode"},
                agent_type="coding"
            ))

        elif any(w in p_lower for w in ["open", "launch", "start", "run", "execute", "play"]):
            app_name = prompt
            for verb in ["open", "launch", "start", "run", "execute", "play"]:
                app_name = re.sub(r'(?i)\b' + re.escape(verb) + r'\b', '', app_name)
            app_name = app_name.strip()

            steps.append(PlannedStep(
                step_id="step_1",
                command=prompt,
                tool_name="launch_app",
                tool_params={"app_name": app_name},
                agent_type="desktop"
            ))

        return ExecutionPlan(goal=prompt, steps=steps)

planner = LLMPlanner()
