import logging
from typing import Dict, Any, List, Optional
from models.model_factory import get_llm_provider
from events.event_bus import event_bus, Event

logger = logging.getLogger("orian.reasoning_agent")

class ReasoningAgent:
    """Agent 3 — Reasoning Agent: Handles high-level cognition, thinking, planning, tool selection, and response synthesis."""

    def __init__(self, provider_name: Optional[str] = None):
        self.agent_id = "ReasoningAgent"
        self.llm = get_llm_provider(provider_name)

    async def generate_plan_and_thought(
        self,
        intent: str,
        cognitive_context: Dict[str, Any],
        available_tools: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        logger.info(f"[{self.agent_id}] Initiating reasoning & planning for intent: '{intent}'")

        await event_bus.publish(Event(
            event_type="reasoning.started",
            sender=self.agent_id,
            data={"intent": intent}
        ))

        system_prompt = (
            "You are the Reasoning Brain of Orian AI. Evaluate context, select relevant tools, "
            "and create a step-by-step subtask execution plan."
        )

        plan_result = self.llm.generate_json(
            prompt=intent,
            context={
                "intent": intent,
                "memory_context": cognitive_context,
                "available_tools": [t["name"] for t in available_tools]
            },
            system_prompt=system_prompt
        )

        await event_bus.publish(Event(
            event_type="plan.created",
            sender=self.agent_id,
            data={"plan_result": plan_result}
        ))

        return plan_result

    async def synthesize_final_response(
        self,
        user_query: str,
        execution_results: List[Dict[str, Any]],
        cognitive_context: Dict[str, Any]
    ) -> str:
        logger.info(f"[{self.agent_id}] Synthesizing response based on execution results")

        system_prompt = "You are Orian AI. Synthesize a helpful, precise final answer for the user based on task execution results."
        
        prompt = f"User Request: {user_query}\nExecution Summary:\n{execution_results}"
        
        response = self.llm.generate_response(
            prompt=prompt,
            context=cognitive_context,
            system_prompt=system_prompt
        )

        await event_bus.publish(Event(
            event_type="response.generated",
            sender=self.agent_id,
            data={"query": user_query, "response_snippet": response[:100]}
        ))

        return response

reasoning_agent = ReasoningAgent()
