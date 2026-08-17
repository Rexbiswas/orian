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

import logging
from typing import Dict, Any
from pydantic import BaseModel, Field

from planner.intent_detector import intent_detector, IntentCategory
from execution.app_resolver import app_resolver
from tools.system_cleanup import system_cleanup
from tools.math_engine import math_engine
from planner.real_world_reasoner import real_world_reasoner
from neural.self_diagnostic import self_diagnostic
from neural.self_programmer import self_programmer

logger = logging.getLogger("orian.tool_router")

class StandardToolResponse(BaseModel):
    success: bool
    action: str
    target: str = ""
    message: str
    error: str = ""
    recovery: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)

class OrianToolRouter:
    """Central Orian Tool Router routing user intent to desktop, math, cleanup, diagnostic, and self-programming engines."""

    def route_and_execute(self, user_prompt: str) -> StandardToolResponse:
        intent, confidence, meta = intent_detector.detect_intent(user_prompt)
        logger.info(f"Routed intent: {intent} (confidence: {confidence}) for prompt: '{user_prompt}'")

        # 1. Desktop Actions (Open / Close applications)
        if intent == IntentCategory.DESKTOP_ACTION:
            if "close" in user_prompt.lower():
                app_name = user_prompt.lower().replace("close", "").strip()
                res = app_resolver.close_app(app_name)
            else:
                app_name = user_prompt
                for v in ["open", "launch", "start", "run", "execute"]:
                    app_name = app_name.lower().replace(v, "").strip()
                res = app_resolver.launch_app(app_name or user_prompt)

            return StandardToolResponse(
                success=res.get("success", False),
                action=res.get("action", "DESKTOP_ACTION"),
                target=res.get("target", user_prompt),
                message=res.get("message", str(res)),
                error=res.get("error", ""),
                recovery=res.get("recovery", "")
            )

        # 2. System Cleanup
        elif intent == IntentCategory.SYSTEM_CLEANUP:
            res = system_cleanup.clear_temp_files()
            return StandardToolResponse(
                success=res.get("success", True),
                action="CLEAR_TEMP_FILES",
                target="Temporary Directories",
                message=res.get("message", "Cleanup completed."),
                details=res
            )

        # 3. Simple Calculation
        elif intent == IntentCategory.SIMPLE_CALCULATION:
            expr = meta.get("expression", user_prompt)
            res = math_engine.evaluate_simple(expr)
            if not res.get("success", False):
                reason_res = real_world_reasoner.solve_problem(user_prompt)
                if reason_res.get("success"):
                    return StandardToolResponse(
                        success=True,
                        action="CALCULATE",
                        target=expr,
                        message=reason_res.get("formatted", str(reason_res.get("answer"))),
                        details=reason_res
                    )

            return StandardToolResponse(
                success=res.get("success", True),
                action="CALCULATE",
                target=expr,
                message=res.get("formatted", str(res.get("result", "Calculation processed."))),
                error=res.get("error", ""),
                recovery=res.get("recovery", "")
            )

        # 4. Advanced Mathematics
        elif intent == IntentCategory.ADVANCED_MATHEMATICS:
            res = math_engine.evaluate_advanced(user_prompt)
            if not res.get("success", False):
                reason_res = real_world_reasoner.solve_problem(user_prompt)
                if reason_res.get("success"):
                    return StandardToolResponse(
                        success=True,
                        action="ADVANCED_MATHEMATICS",
                        target=user_prompt,
                        message=reason_res.get("formatted", str(reason_res.get("answer"))),
                        details=reason_res
                    )

            return StandardToolResponse(
                success=res.get("success", True),
                action="ADVANCED_MATHEMATICS",
                target=user_prompt,
                message=res.get("formatted", str(res.get("result", "Advanced mathematical solution generated."))),
                error=res.get("error", ""),
                recovery=res.get("recovery", "")
            )

        # 5. Self Diagnostics
        elif intent == IntentCategory.SELF_DIAGNOSTIC:
            res = self_diagnostic.run_diagnostics()
            return StandardToolResponse(
                success=res.get("success", True),
                action="SELF_DIAGNOSTIC",
                target="Orian System Architecture",
                message=res.get("formatted", "Diagnostics complete."),
                details=res
            )

        # 6. Self Programming & Improvement
        elif intent == IntentCategory.SELF_PROGRAMMING:
            res = self_programmer.run_self_improvement(user_prompt)
            return StandardToolResponse(
                success=res.get("success", True),
                action="SELF_PROGRAMMING",
                target="Orian Core Source Code",
                message=res.get("formatted", "Self programming audit completed."),
                details=res
            )

        # 7. Real World Reasoning
        elif intent == IntentCategory.REAL_WORLD_REASONING:
            res = real_world_reasoner.solve_problem(user_prompt)
            return StandardToolResponse(
                success=res.get("success", True),
                action="REAL_WORLD_REASONING",
                target=user_prompt,
                message=res.get("formatted", "Real world analysis complete."),
                details=res
            )

        # 8. General LLM / Unhandled Fallback
        else:
            return StandardToolResponse(
                success=True,
                action="GENERAL_CONVERSATION",
                target="LLM Core",
                message=f"Processing query: '{user_prompt}' via Orian Neural Core."
            )

tool_router = OrianToolRouter()
