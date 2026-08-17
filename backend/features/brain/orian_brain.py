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

import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
features_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if features_dir not in sys.path:
    sys.path.insert(0, features_dir)

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

from database.brain_db import brain_db

logger = logging.getLogger("orian.brain")

class OrianBrain:
    """Master Cognitive Coordinator of Orian AI Digital Brain uniting Perception, Memory, Reasoning, Executive, and Learning/Security."""

    def __init__(self):
        self.brain_state = "IDLE"  # LISTENING, THINKING, RECALLING, PLANNING, CODING, EXECUTING, LEARNING, WAITING FOR PERMISSION
        self._register_agents_to_brain_db()

    def _register_agents_to_brain_db(self):
        """Connects all cognitive agents to their anatomical brain DB region via memory.db bridge."""
        agent_mappings = [
            ("PerceptionAgent", "MEDULLA"),          # Sensory inputs & telemetry
            ("MemoryAgent", "MEMORY"),              # Cognitive memory bridge
            ("ReasoningAgent", "CEREBRUM"),          # High-level thinking & cognition
            ("DeveloperAgent", "CEREBRUM"),          # Code reasoning & architecture
            ("AutomationAgent", "CEREBELLUM"),       # Motor controls & task execution
            ("LearningSecurityAgent", "MEDULLA")      # Autonomic safety & audit trail
        ]
        now = time.time()
        for agent_id, region in agent_mappings:
            brain_db.execute("memory",
                "INSERT OR REPLACE INTO agent_connections (agent_id, assigned_region, status, last_ping) VALUES (?, ?, 'ACTIVE', ?)",
                (agent_id, region, now)
            )
        logger.info("Connected all 6 Cognitive Agents to Anatomical Brain DB (Cerebrum, Cerebellum, Medulla, Memory)")

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

        # 1.5. UNIVERSAL COMMAND ROUTER & DETERMINISTIC TOOL EXECUTOR
        from tools.tool_router import tool_router
        tool_response = tool_router.route_and_execute(user_input)

        if tool_response.action != "GENERAL_CONVERSATION":
            await self._update_brain_state("EXECUTING")
            
            # Record execution in Cerebrum & Medulla via brain_db
            try:
                brain_db.execute("medulla",
                    "INSERT INTO logs (request_id, module, level, event_type, message) VALUES (?, ?, ?, ?, ?)",
                    (req_id, f"ToolRouter:{tool_response.action}", "INFO" if tool_response.success else "ERROR", tool_response.action, tool_response.message)
                )
            except Exception:
                pass

            await memory_manager.record_interaction(
                session_id=sess_id,
                user_input=user_input,
                agent_response=tool_response.message,
                user_id=user_id,
                project_id=project_id
            )
            await self._update_brain_state("IDLE")

            return {
                "request_id": req_id,
                "session_id": sess_id,
                "brain_state": "IDLE",
                "intent": {"action": tool_response.action, "target": tool_response.target},
                "plan": {"action": tool_response.action, "success": tool_response.success},
                "execution_results": [tool_response.model_dump()],
                "response": tool_response.message,
                "timestamp": time.time()
            }

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

if __name__ == "__main__":
    async def main():
        print("=== ORIAN BRAIN INITIALIZED & CONNECTED TO BRAIN_DB ===")
        res = await orian_brain.process_user_request("Analyze system status and test brain DB connections")
        print(f"Status: {res['brain_state']}")
        print(f"Request ID: {res['request_id']}")
        print(f"Response: {res['response']}")

    asyncio.run(main())
