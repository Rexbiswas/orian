import os
import logging
from typing import Dict, Any, Optional
from .models import RiskLevel, RiskAssessment
from .config import security_config

logger = logging.getLogger("orian.security.risk_engine")

class RiskEngine:
    """Enterprise Risk Classification Engine assessing operational impact and enforcing confirmation and MFA thresholds."""

    def __init__(self):
        self.config = security_config

    def assess_risk(
        self,
        action: str,
        target: str = "",
        command: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> RiskAssessment:
        """Evaluates operation risk dynamically based on action type, target path, command payload, and safety criticality."""
        meta = metadata or {}
        action_lower = action.lower()
        target_lower = target.lower()
        cmd_lower = command.lower()

        # ---------------------------------------------------------------------
        # 1. CRITICAL RISK ACTIONS
        # ---------------------------------------------------------------------
        # Security changes, self-modifying security layer, user elevation
        critical_keywords = [
            "security_admin", "modify_security", "disable_auth", "disable_security",
            "grant_admin", "user_admin", "change_password", "bypass_gateway",
            "modify_gateway", "delete_database", "drop_table"
        ]

        if any(kw in action_lower or kw in cmd_lower for kw in critical_keywords):
            return RiskAssessment(
                risk_level=RiskLevel.CRITICAL,
                score=95,
                reason="Operation modifies core security governance, authorization matrices, or administrative credentials.",
                requires_confirmation=True,
                requires_mfa=self.config.REQUIRE_MFA_FOR_CRITICAL_RISK,
                target=target,
                action=action
            )

        # Modifying protected files in security directory
        if "self_program" in action_lower or "code_modify" in action_lower:
            for protected in self.config.PROTECTED_DIRECTORIES:
                if protected in target_lower or protected in cmd_lower:
                    return RiskAssessment(
                        risk_level=RiskLevel.CRITICAL,
                        score=90,
                        reason=f"Self-programming modification targeted at protected system file/directory: '{protected}'",
                        requires_confirmation=True,
                        requires_mfa=self.config.REQUIRE_MFA_FOR_CRITICAL_RISK,
                        target=target,
                        action=action
                    )

        # ---------------------------------------------------------------------
        # 2. HIGH RISK ACTIONS
        # ---------------------------------------------------------------------
        # File deletion, shell command execution, high-power appliances, self-programming
        high_risk_actions = [
            "delete_file", "execute_command", "shell_execution", "system_cleanup",
            "clear_temp_files", "self_program", "code_modify", "factory_reset"
        ]

        if any(h in action_lower for h in high_risk_actions) or meta.get("is_safety_critical") or "delete" in cmd_lower or "rmdir" in cmd_lower or "format" in cmd_lower:
            requires_conf = self.config.REQUIRE_CONFIRMATION_FOR_HIGH_RISK
            return RiskAssessment(
                risk_level=RiskLevel.HIGH,
                score=75,
                reason=f"Operation involves potentially irreversible system actions, code modification, or safety-critical hardware: {action}",
                requires_confirmation=requires_conf,
                requires_mfa=False,
                target=target,
                action=action
            )

        # High-power IoT appliances (AC, Heater, Geyser)
        if "iot" in action_lower:
            high_power_devices = ["ac", "living_room_ac", "heater", "geyser", "oven"]
            if any(dev in target_lower for dev in high_power_devices):
                return RiskAssessment(
                    risk_level=RiskLevel.HIGH,
                    score=70,
                    reason=f"IoT control action targeted at high-power electrical appliance: {target}",
                    requires_confirmation=True,
                    requires_mfa=False,
                    target=target,
                    action=action
                )

        # ---------------------------------------------------------------------
        # 3. MEDIUM RISK ACTIONS
        # ---------------------------------------------------------------------
        # Launching desktop apps, writing new files, toggling standard IoT lights/fans
        medium_risk_actions = [
            "open_application", "launch_app", "write_file", "iot_control", "system_setting",
            "desktop_action", "desktop"
        ]

        if any(m in action_lower for m in medium_risk_actions):
            requires_conf = self.config.REQUIRE_CONFIRMATION_FOR_MEDIUM_RISK
            return RiskAssessment(
                risk_level=RiskLevel.MEDIUM,
                score=45,
                reason=f"Standard interactive desktop or hardware control operation: {action}",
                requires_confirmation=requires_conf,
                requires_mfa=False,
                target=target,
                action=action
            )

        # ---------------------------------------------------------------------
        # 4. LOW RISK ACTIONS
        # ---------------------------------------------------------------------
        return RiskAssessment(
            risk_level=RiskLevel.LOW,
            score=15,
            reason="Read-only query, calculation, sensory processing, or conversational response.",
            requires_confirmation=False,
            requires_mfa=False,
            target=target,
            action=action
        )

risk_engine = RiskEngine()
