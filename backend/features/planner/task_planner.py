import logging
import uuid
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from tools.tool_registry import tool_registry

logger = logging.getLogger("orian.task_planner")

class SubTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task-{uuid.uuid4().hex[:8]}")
    title: str
    tool_name: str
    params: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"
    depends_on: List[str] = Field(default_factory=list)
    status: str = "PENDING"  # PENDING, PLANNING, RUNNING, WAITING, COMPLETED, FAILED, CANCELLED, BLOCKED, REQUIRES_CONFIRMATION

class ExecutionPlan(BaseModel):
    plan_id: str = Field(default_factory=lambda: f"plan-{uuid.uuid4().hex[:8]}")
    request_id: str
    user_query: str
    tasks: List[SubTask]

class TaskPlanner:
    """Central Task Planner decomposing high-level user goals into executable subtasks."""

    def __init__(self):
        pass

    def create_plan(self, request_id: str, user_query: str, raw_plan_data: Dict[str, Any]) -> ExecutionPlan:
        logger.info(f"Building ExecutionPlan for request {request_id}")
        subtasks: List[SubTask] = []
        raw_items = raw_plan_data.get("plan", [])

        if not raw_items:
            # Fallback single task
            subtasks.append(SubTask(
                title=f"Execute query: {user_query[:30]}",
                tool_name="read_file",
                params={"file_path": "README.md"},
                risk_level="LOW"
            ))
        else:
            for idx, item in enumerate(raw_items):
                tool_name = item.get("tool", "inspect_project")
                tool_def = tool_registry.get_tool(tool_name)
                risk = item.get("risk_level") or (tool_def.permission_level if tool_def else "LOW")
                
                t_id = item.get("task_id") or f"subtask-{idx+1}"
                deps = [subtasks[idx-1].task_id] if idx > 0 else []

                subtasks.append(SubTask(
                    task_id=t_id,
                    title=item.get("title", f"Subtask {idx+1}"),
                    tool_name=tool_name,
                    params=item.get("params", {}),
                    risk_level=risk,
                    depends_on=deps
                ))

        return ExecutionPlan(
            request_id=request_id,
            user_query=user_query,
            tasks=subtasks
        )

task_planner = TaskPlanner()
