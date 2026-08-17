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

import re
import uuid
import time
from enum import Enum
from typing import List, Dict, Any, Optional
from llm_planner import planner, ExecutionPlan

class TaskStatus(str, Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

class TaskPriority(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

class Task:
    def __init__(
        self,
        command: str,
        agent_type: str,
        tool_name: str = "launch_app",
        tool_params: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.HIGH,
        dependencies: Optional[List[str]] = None,
        task_id: Optional[str] = None
    ):
        self.id = task_id or f"task_{uuid.uuid4().hex[:8]}"
        self.command = command
        self.agent_type = agent_type
        self.tool_name = tool_name
        self.tool_params = tool_params or {}
        self.priority = priority if isinstance(priority, TaskPriority) else TaskPriority(priority) if priority in TaskPriority.__members__ else TaskPriority.HIGH
        self.dependencies = dependencies or []
        self.status = TaskStatus.QUEUED
        self.progress = 0
        self.current_action = "Queued for execution"
        self.logs: List[str] = [f"[{time.strftime('%H:%M:%S')}] Task initialized: '{command}' (Tool: {tool_name})"]
        self.eta_seconds = 10
        self.created_at = time.time()
        self.started_at: Optional[float] = None
        self.finished_at: Optional[float] = None
        self.cpu_usage = 0.0
        self.mem_usage = 0.0
        self.retry_count = 0
        self.max_retries = 3
        self.result: Optional[Any] = None
        self.observation: Optional[str] = None
        self.error: Optional[str] = None

    def add_log(self, msg: str):
        timestamp = time.strftime('%H:%M:%S')
        self.logs.append(f"[{timestamp}] {msg}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "command": self.command,
            "agent_type": self.agent_type,
            "tool_name": self.tool_name,
            "tool_params": self.tool_params,
            "priority": self.priority.value if isinstance(self.priority, TaskPriority) else self.priority,
            "dependencies": self.dependencies,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "progress": self.progress,
            "current_action": self.current_action,
            "logs": self.logs[-20:],
            "eta_seconds": max(0, int(self.eta_seconds)),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "cpu_usage": self.cpu_usage,
            "mem_usage": self.mem_usage,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "result": self.result,
            "observation": self.observation,
            "error": self.error
        }


class MultiCommandParser:
    """Delegates prompt decomposition to the LLM Reasoning Planner."""

    @classmethod
    def parse_prompt(cls, prompt: str, context_memory: str = "") -> List[Task]:
        prompt_clean = prompt.strip()
        if not prompt_clean:
            return []

        # Invoke LLM Planner to break down goal into structured tool steps
        execution_plan: ExecutionPlan = planner.decompose_goal(prompt_clean, context_memory)
        
        tasks: List[Task] = []
        step_id_map = {}

        for step in execution_plan.steps:
            # Map step_id (e.g. step_1) to actual task UUID
            real_task_id = f"task_{uuid.uuid4().hex[:8]}"
            step_id_map[step.step_id] = real_task_id

            # Map dependencies
            mapped_deps = [step_id_map[d] for d in step.dependencies if d in step_id_map]

            task = Task(
                command=step.command,
                agent_type=step.agent_type,
                tool_name=step.tool_name,
                tool_params=step.tool_params,
                priority=step.priority,
                dependencies=mapped_deps,
                task_id=real_task_id
            )
            tasks.append(task)

        return tasks
