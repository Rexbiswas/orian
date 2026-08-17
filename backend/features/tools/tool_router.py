import sys
import os
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.planner.intent_detector import intent_detector, IntentCategory
from features.execution.app_resolver import app_resolver
from features.tools.system_cleanup import system_cleanup
from features.tools.math_engine import math_engine
from features.planner.real_world_reasoner import real_world_reasoner
from features.neural.self_diagnostic import self_diagnostic
from features.neural.self_programmer import self_programmer
from features.iot.iot_tool import iot_tool
from features.security.gateway import security_gateway
from features.security.models import User, Role, Permission
from features.security.auth_engine import auth_engine

logger = logging.getLogger("orian.tool_router")

class StandardToolResponse(BaseModel):
    success: bool
    action: str
    target: str = ""
    message: str
    error: str = ""
    recovery: str = ""
    details: Dict[str, Any] = Field(default_factory=dict)
    risk_level: Optional[str] = "LOW"
    confirmation_required: bool = False
    ticket_id: Optional[str] = None

class OrianToolRouter:
    """Central Orian Tool Router enforcing Security Gateway validation across desktop, math, cleanup, diagnostic, IoT, and self-programming engines."""

    def route_and_execute(
        self,
        user_prompt: str,
        user: Optional[User] = None,
        confirmation_ticket_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> StandardToolResponse:
        # Resolve active user if not explicitly passed
        current_user = user
        if not current_user:
            current_user = auth_engine.get_user_by_id("usr_bootstrap_owner")
            if not current_user:
                conn = auth_engine.db.get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM sec_users WHERE role = 'OWNER' LIMIT 1")
                row = cursor.fetchone()
                conn.close()
                if row:
                    current_user = auth_engine.get_user_by_id(row["id"])
                else:
                    current_user = User(id="usr_default", username="local_user", role=Role.OWNER)

        intent, confidence, meta = intent_detector.detect_intent(user_prompt)
        logger.info(f"Routed intent: {intent} (confidence: {confidence}) for prompt: '{user_prompt}' | User: {current_user.username}")

        try:
            # 1. Desktop Actions (Open / Close applications)
            if intent == IntentCategory.DESKTOP_ACTION:
                is_close = "close" in user_prompt.lower()
                app_name = user_prompt
                if is_close:
                    app_name = user_prompt.lower().replace("close", "").strip()
                    callable_fn = lambda **kw: app_resolver.close_app(kw.get("app_name"))
                    args = {"app_name": app_name}
                else:
                    for v in ["open", "launch", "start", "run", "execute"]:
                        app_name = app_name.lower().replace(v, "").strip()
                    callable_fn = lambda **kw: app_resolver.launch_app(kw.get("app_name") or user_prompt)
                    args = {"app_name": app_name or user_prompt}

                gateway_res = security_gateway.execute_secured(
                    user=current_user,
                    tool_name="desktop_action",
                    tool_callable=callable_fn,
                    arguments=args,
                    confirmation_ticket_id=confirmation_ticket_id,
                    session_id=session_id
                )

                if not gateway_res["success"]:
                    return StandardToolResponse(
                        success=False,
                        action="DESKTOP_ACTION",
                        target=app_name,
                        message=gateway_res.get("error", "Action blocked"),
                        error=gateway_res.get("error", "")
                    )

                res = gateway_res["result"]
                return StandardToolResponse(
                    success=res.get("success", False),
                    action=res.get("action", "DESKTOP_ACTION"),
                    target=res.get("target", user_prompt),
                    message=res.get("message", str(res)),
                    error=res.get("error", ""),
                    recovery=res.get("recovery", ""),
                    risk_level=gateway_res.get("risk_level", "MEDIUM")
                )

            # 2. System Cleanup
            elif intent == IntentCategory.SYSTEM_CLEANUP:
                gateway_res = security_gateway.execute_secured(
                    user=current_user,
                    tool_name="system_cleanup",
                    tool_callable=lambda **kw: system_cleanup.clear_temp_files(),
                    arguments={"target": "Temporary Directories", "command": user_prompt},
                    confirmation_ticket_id=confirmation_ticket_id,
                    session_id=session_id
                )

                if not gateway_res["success"]:
                    return StandardToolResponse(
                        success=False,
                        action="CLEAR_TEMP_FILES",
                        target="Temporary Directories",
                        message=gateway_res.get("error", "Cleanup blocked by security policy"),
                        error=gateway_res.get("error", "")
                    )

                res = gateway_res["result"]
                return StandardToolResponse(
                    success=res.get("success", True),
                    action="CLEAR_TEMP_FILES",
                    target="Temporary Directories",
                    message=res.get("message", "Cleanup completed."),
                    details=res,
                    risk_level="HIGH"
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
                            details=reason_res,
                            risk_level="LOW"
                        )

                return StandardToolResponse(
                    success=res.get("success", True),
                    action="CALCULATE",
                    target=expr,
                    message=res.get("formatted", str(res.get("result", "Calculation processed."))),
                    error=res.get("error", ""),
                    recovery=res.get("recovery", ""),
                    risk_level="LOW"
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
                            details=reason_res,
                            risk_level="LOW"
                        )

                return StandardToolResponse(
                    success=res.get("success", True),
                    action="ADVANCED_MATHEMATICS",
                    target=user_prompt,
                    message=res.get("formatted", str(res.get("result", "Advanced mathematical solution generated."))),
                    error=res.get("error", ""),
                    recovery=res.get("recovery", ""),
                    risk_level="LOW"
                )

            # 5. Self Diagnostics
            elif intent == IntentCategory.SELF_DIAGNOSTIC:
                res = self_diagnostic.run_diagnostics()
                return StandardToolResponse(
                    success=res.get("success", True),
                    action="SELF_DIAGNOSTIC",
                    target="Orian System Architecture",
                    message=res.get("formatted", "Diagnostics complete."),
                    details=res,
                    risk_level="LOW"
                )

            # 6. Self Programming & Improvement
            elif intent == IntentCategory.SELF_PROGRAMMING:
                gateway_res = security_gateway.execute_secured(
                    user=current_user,
                    tool_name="self_programming",
                    tool_callable=lambda **kw: self_programmer.run_self_improvement(kw.get("prompt")),
                    arguments={"prompt": user_prompt, "target": "Orian Core Source Code", "command": user_prompt},
                    confirmation_ticket_id=confirmation_ticket_id,
                    session_id=session_id
                )

                if not gateway_res["success"]:
                    return StandardToolResponse(
                        success=False,
                        action="SELF_PROGRAMMING",
                        target="Orian Core Source Code",
                        message=gateway_res.get("error", "Self-programming blocked by security gateway"),
                        error=gateway_res.get("error", "")
                    )

                res = gateway_res["result"]
                return StandardToolResponse(
                    success=res.get("success", True),
                    action="SELF_PROGRAMMING",
                    target="Orian Core Source Code",
                    message=res.get("formatted", "Self programming audit completed."),
                    details=res,
                    risk_level="HIGH"
                )

            # 7. Real World Reasoning
            elif intent == IntentCategory.REAL_WORLD_REASONING:
                res = real_world_reasoner.solve_problem(user_prompt)
                return StandardToolResponse(
                    success=res.get("success", True),
                    action="REAL_WORLD_REASONING",
                    target=user_prompt,
                    message=res.get("formatted", "Real world analysis complete."),
                    details=res,
                    risk_level="LOW"
                )

            # 8. Mobile IoT Hardware Control & Queries
            elif intent in [IntentCategory.IOT_CONTROL, IntentCategory.IOT_QUERY]:
                gateway_res = security_gateway.execute_secured(
                    user=current_user,
                    tool_name="iot_control" if intent == IntentCategory.IOT_CONTROL else "iot_read",
                    tool_callable=lambda **kw: iot_tool.execute_natural_command(kw.get("prompt")),
                    arguments={"prompt": user_prompt, "target": user_prompt, "command": user_prompt},
                    confirmation_ticket_id=confirmation_ticket_id,
                    session_id=session_id
                )

                if not gateway_res["success"]:
                    return StandardToolResponse(
                        success=False,
                        action="IOT_OPERATION",
                        target="IoT Device",
                        message=gateway_res.get("error", "IoT operation blocked"),
                        error=gateway_res.get("error", "")
                    )

                res = gateway_res["result"]
                return StandardToolResponse(
                    success=res.get("success", True),
                    action=res.get("action", "IOT_OPERATION"),
                    target=res.get("target", "IoT Device"),
                    message=res.get("message", "IoT command dispatched."),
                    error=res.get("error", ""),
                    recovery=res.get("recovery", ""),
                    details=res,
                    risk_level=gateway_res.get("risk_level", "MEDIUM")
                )

            # 9. General LLM / Unhandled Fallback
            else:
                return StandardToolResponse(
                    success=True,
                    action="GENERAL_CONVERSATION",
                    target="LLM Core",
                    message=f"Processing query: '{user_prompt}' via Orian Neural Core.",
                    risk_level="LOW"
                )

        except PermissionError as pe:
            return StandardToolResponse(
                success=False,
                action="SECURITY_GATEWAY_DENIAL",
                target=user_prompt,
                message=str(pe),
                error=str(pe),
                risk_level="CRITICAL"
            )
        except Exception as e:
            logger.error(f"Tool execution exception: {e}")
            return StandardToolResponse(
                success=False,
                action="TOOL_EXECUTION_FAULT",
                target=user_prompt,
                message=f"Execution fault: {str(e)}",
                error=str(e),
                risk_level="MEDIUM"
            )

tool_router = OrianToolRouter()
