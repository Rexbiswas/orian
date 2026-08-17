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
import time
import json
from typing import Dict, Any, List, Optional
from database.sqlite_db import db
from config import settings

logger = logging.getLogger("orian.learning_security_agent")

class LearningSecurityAgent:
    """Agent 6 — Learning & Security Agent: Combines safety checks, prompt injection defense, audit logging, system telemetry, and habit learning."""

    def __init__(self):
        self.agent_id = "LearningSecurityAgent"

    def check_security_and_permission(
        self,
        actor: str,
        action: str,
        tool_name: str,
        params: dict,
        risk_level: str
    ) -> Dict[str, Any]:
        """Evaluates command safety, prompt injection risks, and permission policies."""
        
        # 1. Prompt Injection & Dangerous Command Defense
        param_str = json.dumps(params).lower()
        dangerous_patterns = ["rm -rf /", "format c:", "drop database", "sudo rm", ":(){ :|:& };:"]
        for p in dangerous_patterns:
            if p in param_str:
                logger.critical(f"[{self.agent_id}] SECURITY BLOCK: Dangerous command pattern detected '{p}'")
                return {
                    "allowed": False,
                    "reason": f"Security violation: Dangerous pattern detected '{p}'",
                    "requires_confirmation": False
                }

        # 2. Risk Level Evaluation
        if risk_level == "HIGH" and settings.REQUIRE_CONFIRMATION_FOR_HIGH_RISK:
            return {
                "allowed": False,
                "requires_confirmation": True,
                "reason": f"High risk action '{tool_name}' requires explicit user confirmation"
            }
        elif risk_level == "MEDIUM" and settings.REQUIRE_CONFIRMATION_FOR_MEDIUM_RISK and settings.DEFAULT_RISK_POLICY == "strict":
            return {
                "allowed": False,
                "requires_confirmation": True,
                "reason": f"Medium risk action '{tool_name}' requires confirmation under strict policy"
            }

        return {"allowed": True, "requires_confirmation": False, "reason": "Operation permitted"}

    def record_audit(
        self,
        request_id: str,
        actor: str,
        action: str,
        target: str,
        risk_level: str,
        result: str
    ):
        now = time.time()
        db.execute(
            "INSERT INTO audit_trail (request_id, actor, action, target, risk_level, result, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (request_id, actor, action, target, risk_level, result, now)
        )
        logger.info(f"[{self.agent_id}] AUDIT LOG: {actor} -> {action} ({risk_level}) : {result}")

    def record_learning_feedback(self, task_id: str, success: bool, user_rating: Optional[int] = None, feedback_notes: Optional[str] = None):
        """Records task execution performance signal for future workflow optimization."""
        status_str = "SUCCESS" if success else "FAILURE"
        logger.info(f"[{self.agent_id}] LEARNING FEEDBACK: Task {task_id} marked as {status_str}")

learning_security_agent = LearningSecurityAgent()
