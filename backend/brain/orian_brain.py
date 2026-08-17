import asyncio
import logging
import uuid
import time
from typing import Dict, Any, Optional
from agents.perception_agent import perception_agent
from agents.memory_agent import memory_agent
from agents.reasoning_agent import reasoning_agent
from agents.developer_agent import developer_agent
from agents.automation_agent import automation_agent
from agents.learning_security_agent import learning_security_agent
from planner.task_planner import task_planner
from execution.execution_engine import execution_engine
from tools.tool_registry import tool_registry
from memory.memory_manager import memory_manager
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.brain")

class OrianBrain:
    """Master Cognitive Coordinator of Orian AI Digital Brain uniting Perception, Memory, Reasoning, Executive, and Learning/Security."""

    def __init__(self):
        self.brain_state = "IDLE"  # LISTENING, THINKING, RECALLING, PLANNING, CODING, EXECUTING, LEARNING, WAITING FOR PERMISSION

    async def _update_brain_state(self, new_state: str):
        self.brain_state = new_state
        logger.info(f"[ORIAN BRAIN STATE] ---> {new_state}")
        await event_bus.publish(Event(
            event_type="brain.state_changed",
            sender="OrianBrain",
            data={"state": new_state}
        ))

    async def process_user_request(
        self,
        user_input: str,
        input_type: str = "text",
        session_id: Optional[str] = None,
        user_id: str = "default_user",
        project_id: str = "default_project",
        media_path: Optional[str] = None
    ) -> Dict[str, Any]:
        req_id = f"req-{uuid.uuid4().hex[:8]}"
        sess_id = session_id or f"session-{uuid.uuid4().hex[:8]}"

        logger.info(f"=== Orian Brain Processing Request [{req_id}] ===")
        await event_bus.publish(Event(
            event_type="user.input.received",
            sender="OrianBrain",
            data={"request_id": req_id, "session_id": sess_id, "input": user_input, "input_type": input_type}
        ))

        # 1. PERCEPTION BRAIN (Eyes & Ears)
        await self._update_brain_state("LISTENING")
        intent_ctx = await perception_agent.process_input(
            user_input=user_input,
            input_type=input_type,
            media_path=media_path
        )

        # 2. MEMORY BRAIN (Hippocampus)
        await self._update_brain_state("RECALLING")
        cognitive_context = await memory_agent.prepare_cognitive_context(
            query=intent_ctx.normalized_intent,
            session_id=sess_id,
            user_id=user_id,
            project_id=project_id
        )

        # 3. REASONING BRAIN (Prefrontal Cortex)
        await self._update_brain_state("THINKING")
        available_tools = tool_registry.list_tools()
        raw_plan = await reasoning_agent.generate_plan_and_thought(
            intent=intent_ctx.normalized_intent,
            cognitive_context=cognitive_context,
            available_tools=available_tools
        )

        # 4. TASK PLANNER (Cognitive Strategy)
        await self._update_brain_state("PLANNING")
        execution_plan = task_planner.create_plan(
            request_id=req_id,
            user_query=intent_ctx.normalized_intent,
            raw_plan_data=raw_plan
        )

        # Check if developer tasks exist
        has_dev_tasks = any(t.tool_name in ["write_file", "inspect_project", "run_terminal_command"] for t in execution_plan.tasks)
        if has_dev_tasks:
            await self._update_brain_state("CODING")
        else:
            await self._update_brain_state("EXECUTING")

        # 5. EXECUTIVE BRAIN & EXECUTION ENGINE (Motor Cortex)
        execution_results = await execution_engine.execute_plan(execution_plan)

        # Check if execution requires confirmation
        requires_perm = any(r.get("status") == "REQUIRES_CONFIRMATION" for r in execution_results)
        if requires_perm:
            await self._update_brain_state("WAITING FOR PERMISSION")

        # 6. RESPONSE SYNTHESIS
        final_answer = await reasoning_agent.synthesize_final_response(
            user_query=user_input,
            execution_results=execution_results,
            cognitive_context=cognitive_context
        )

        # 7. LEARNING & MEMORY UPDATE (Cerebellum)
        await self._update_brain_state("LEARNING")
        await memory_manager.record_interaction(
            session_id=sess_id,
            user_input=user_input,
            agent_response=final_answer,
            user_id=user_id,
            project_id=project_id
        )

        if not requires_perm:
            await self._update_brain_state("IDLE")

        return {
            "request_id": req_id,
            "session_id": sess_id,
            "brain_state": self.brain_state,
            "intent": intent_ctx.model_dump(),
            "plan": execution_plan.model_dump(),
            "execution_results": execution_results,
            "response": final_answer,
            "timestamp": time.time()
        }

orian_brain = OrianBrain()
