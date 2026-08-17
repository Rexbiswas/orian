import asyncio
import logging
import time
from typing import Dict, Any, List, Optional
from planner.task_planner import ExecutionPlan, SubTask
from agents.learning_security_agent import learning_security_agent
from tools.tool_registry import tool_registry
from memory.sqlite_store import sqlite_store
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.execution_engine")

class ExecutionEngine:
    """Executive Brain Execution Engine: Safely executes subtasks using the task state machine."""

    def __init__(self):
        self.pending_confirmations: Dict[str, SubTask] = {}

    async def execute_plan(self, plan: ExecutionPlan) -> List[Dict[str, Any]]:
        logger.info(f"ExecutionEngine starting plan {plan.plan_id} ({len(plan.tasks)} tasks)")
        results: List[Dict[str, Any]] = []

        for task in plan.tasks:
            # Task state transition to PLANNING -> RUNNING
            task.status = "RUNNING"
            sqlite_store.store_task(
                task_id=task.task_id,
                title=task.title,
                status=task.status,
                risk_level=task.risk_level,
                payload=task.params,
                request_id=plan.request_id
            )

            await event_bus.publish(Event(
                event_type="task.started",
                sender="ExecutionEngine",
                data={"task_id": task.task_id, "title": task.title, "risk": task.risk_level}
            ))

            # 1. Security Check
            sec_res = learning_security_agent.check_security_and_permission(
                actor="ReasoningAgent",
                action=task.title,
                tool_name=task.tool_name,
                params=task.params,
                risk_level=task.risk_level
            )

            if not sec_res["allowed"]:
                if sec_res.get("requires_confirmation"):
                    task.status = "REQUIRES_CONFIRMATION"
                    self.pending_confirmations[task.task_id] = task
                    sqlite_store.update_task_status(task.task_id, "REQUIRES_CONFIRMATION", error_message=sec_res["reason"])
                    
                    await event_bus.publish(Event(
                        event_type="task.blocked",
                        sender="ExecutionEngine",
                        data={"task_id": task.task_id, "reason": sec_res["reason"], "risk_level": task.risk_level}
                    ))
                    
                    results.append({
                        "task_id": task.task_id,
                        "status": "REQUIRES_CONFIRMATION",
                        "error": sec_res["reason"]
                    })
                    break  # Pause execution pending user approval
                else:
                    task.status = "BLOCKED"
                    sqlite_store.update_task_status(task.task_id, "BLOCKED", error_message=sec_res["reason"])
                    results.append({
                        "task_id": task.task_id,
                        "status": "BLOCKED",
                        "error": sec_res["reason"]
                    })
                    continue

            # 2. Tool Execution
            await event_bus.publish(Event(
                event_type="tool.called",
                sender="ExecutionEngine",
                data={"tool_name": task.tool_name, "params": task.params}
            ))

            res = await tool_registry.execute_tool(task.tool_name, task.params)
            
            if res.get("success"):
                task.status = "COMPLETED"
                sqlite_store.update_task_status(task.task_id, "COMPLETED", result=res)
                learning_security_agent.record_audit(
                    request_id=plan.request_id,
                    actor="ExecutionEngine",
                    action=task.tool_name,
                    target=str(task.params),
                    risk_level=task.risk_level,
                    result="SUCCESS"
                )
                
                await event_bus.publish(Event(
                    event_type="tool.completed",
                    sender="ExecutionEngine",
                    data={"task_id": task.task_id, "tool_name": task.tool_name, "result": res}
                ))

                await event_bus.publish(Event(
                    event_type="task.completed",
                    sender="ExecutionEngine",
                    data={"task_id": task.task_id}
                ))
            else:
                task.status = "FAILED"
                sqlite_store.update_task_status(task.task_id, "FAILED", error_message=res.get("error"))
                learning_security_agent.record_audit(
                    request_id=plan.request_id,
                    actor="ExecutionEngine",
                    action=task.tool_name,
                    target=str(task.params),
                    risk_level=task.risk_level,
                    result="FAILED"
                )

                await event_bus.publish(Event(
                    event_type="task.failed",
                    sender="ExecutionEngine",
                    data={"task_id": task.task_id, "error": res.get("error")}
                ))

            results.append({"task_id": task.task_id, "status": task.status, "output": res})

        return results

    async def approve_and_resume_task(self, task_id: str) -> Dict[str, Any]:
        """Resolves confirmation state for a pending task and executes it."""
        task = self.pending_confirmations.pop(task_id, None)
        if not task:
            return {"success": False, "error": f"No pending task found for id '{task_id}'"}

        logger.info(f"User approved execution of high/medium risk task: {task_id}")
        task.status = "RUNNING"
        sqlite_store.update_task_status(task_id, "RUNNING")

        res = await tool_registry.execute_tool(task.tool_name, task.params)
        if res.get("success"):
            task.status = "COMPLETED"
            sqlite_store.update_task_status(task_id, "COMPLETED", result=res)
        else:
            task.status = "FAILED"
            sqlite_store.update_task_status(task_id, "FAILED", error_message=res.get("error"))

        return {"success": True, "task_id": task_id, "result": res}

execution_engine = ExecutionEngine()
