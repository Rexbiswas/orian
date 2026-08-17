import asyncio
import time
import psutil
import json
import logging
from typing import Dict, List, Set, Optional, Any
from fastapi import WebSocket, WebSocketDisconnect
from task_engine import Task, TaskStatus, TaskPriority, MultiCommandParser
from agent_orchestrator import orchestrator

logger = logging.getLogger("TaskScheduler")

class WebSocketManager:
    """Manages active WebSockets for live streaming task updates."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"WebSocket client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: Dict[str, Any]):
        if not self.active_connections:
            return
        
        payload = json.dumps(message)
        disconnected = set()
        for connection in list(self.active_connections):
            try:
                await connection.send_text(payload)
            except Exception as e:
                disconnected.add(connection)

        for conn in disconnected:
            self.disconnect(conn)

ws_manager = WebSocketManager()


class TaskScheduler:
    """Async Parallel Scheduler with Dependency Graph and Real-Time Event Dispatcher."""

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.task_results_map: Dict[str, Any] = {}
        self.is_running = False
        self._loop_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self._loop_task = asyncio.create_task(self._scheduler_loop())
            logger.info("Real-Time Task Scheduler started.")

    async def add_prompt(self, prompt: str) -> List[Task]:
        from memory_engine import memory_engine
        context_summary = memory_engine.get_context_summary()
        new_tasks = MultiCommandParser.parse_prompt(prompt, context_summary)
        async with self._lock:
            for task in new_tasks:
                self.tasks[task.id] = task

        await ws_manager.broadcast({
            "event": "TASKS_ADDED",
            "prompt": prompt,
            "tasks": [t.to_dict() for t in new_tasks]
        })

        # Ensure background loop is running
        self.start()
        return new_tasks

    def get_all_tasks(self) -> List[Dict[str, Any]]:
        # Sort by priority and creation time
        sorted_tasks = sorted(
            self.tasks.values(),
            key=lambda t: (0 if t.priority == TaskPriority.CRITICAL else 1 if t.priority == TaskPriority.HIGH else 2 if t.priority == TaskPriority.MEDIUM else 3, t.created_at)
        )
        return [t.to_dict() for t in sorted_tasks]

    async def cancel_task(self, task_id: str) -> bool:
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status in [TaskStatus.QUEUED, TaskStatus.RUNNING]:
                    task.status = TaskStatus.CANCELED
                    task.current_action = "Task canceled by user"
                    task.finished_at = time.time()
                    task.add_log("User canceled execution.")
                    await self._notify_task_update(task, event="TASK_CANCELED")
                    return True
        return False

    async def retry_task(self, task_id: str) -> bool:
        async with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = TaskStatus.QUEUED
                task.progress = 0
                task.retry_count = 0
                task.error = None
                task.current_action = "Queued for retry"
                task.add_log("Re-queued task for manual retry.")
                await self._notify_task_update(task, event="TASK_REQUEUED")
                return True
        return False

    async def _notify_task_update(self, task: Task, event: str = "TASK_UPDATED"):
        await ws_manager.broadcast({
            "event": event,
            "task": task.to_dict(),
            "all_tasks": self.get_all_tasks()
        })

    def _on_task_progress(self, task: Task):
        # Update CPU / Memory telemetry for task
        try:
            task.cpu_usage = round(psutil.cpu_percent(), 1)
            task.mem_usage = round(psutil.virtual_memory().percent, 1)
        except: pass

        # Fire and forget async broadcast
        asyncio.create_task(self._notify_task_update(task))

    async def _scheduler_loop(self):
        while self.is_running:
            try:
                await asyncio.sleep(0.3)

                ready_tasks: List[Task] = []
                async with self._lock:
                    for task in self.tasks.values():
                        if task.status == TaskStatus.QUEUED:
                            # Check dependencies
                            deps_satisfied = True
                            for dep_id in task.dependencies:
                                dep_task = self.tasks.get(dep_id)
                                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                                    deps_satisfied = False
                                    break
                            
                            if deps_satisfied:
                                ready_tasks.append(task)

                # Launch ready tasks concurrently
                for task in ready_tasks:
                    asyncio.create_task(orchestrator.run_task(task, self._on_task_progress, self.task_results_map))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")

task_scheduler = TaskScheduler()

