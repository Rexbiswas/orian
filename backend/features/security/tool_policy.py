import logging
from typing import Dict, Any, Optional
from .models import ToolPolicy, RiskLevel, Permission, User, RiskAssessment
from .rbac import rbac_engine
from .risk_engine import risk_engine
from .confirmation_engine import confirmation_engine
from .path_validator import path_validator
from .ssrf_validator import ssrf_validator

logger = logging.getLogger("orian.security.tool_policy")

DEFAULT_TOOL_POLICIES = {
    "desktop_action": ToolPolicy(
        tool_name="desktop_action",
        risk_level=RiskLevel.MEDIUM,
        required_permission=Permission.OPEN_APPLICATION,
        requires_confirmation=False,
        description="Launch and interact with local desktop applications."
    ),
    "system_cleanup": ToolPolicy(
        tool_name="system_cleanup",
        risk_level=RiskLevel.HIGH,
        required_permission=Permission.SYSTEM_CONTROL,
        requires_confirmation=True,
        description="Scans and removes temporary, log, and cache files."
    ),
    "math_engine": ToolPolicy(
        tool_name="math_engine",
        risk_level=RiskLevel.LOW,
        required_permission=Permission.CALCULATOR,
        requires_confirmation=False,
        description="Evaluates simple and advanced mathematical expressions."
    ),
    "self_diagnostic": ToolPolicy(
        tool_name="self_diagnostic",
        risk_level=RiskLevel.LOW,
        required_permission=Permission.SELF_DIAGNOSE,
        requires_confirmation=False,
        description="Audits system health, sensor streams, and database integrity."
    ),
    "self_programming": ToolPolicy(
        tool_name="self_programming",
        risk_level=RiskLevel.HIGH,
        required_permission=Permission.SELF_PROGRAM,
        requires_confirmation=True,
        description="Performs controlled self-repair, AST syntax checks, and codebase upgrades."
    ),
    "iot_control": ToolPolicy(
        tool_name="iot_control",
        risk_level=RiskLevel.MEDIUM,
        required_permission=Permission.IOT_CONTROL,
        requires_confirmation=False,
        description="Sends hardware control commands to ESP32 and IoT devices."
    ),
    "iot_read": ToolPolicy(
        tool_name="iot_read",
        risk_level=RiskLevel.LOW,
        required_permission=Permission.IOT_READ,
        requires_confirmation=False,
        description="Queries telemetry feeds and status of registered IoT devices."
    ),
    "delete_file": ToolPolicy(
        tool_name="delete_file",
        risk_level=RiskLevel.HIGH,
        required_permission=Permission.DELETE_FILE,
        requires_confirmation=True,
        description="Deletes files from the workspace."
    ),
    "chat": ToolPolicy(
        tool_name="chat",
        risk_level=RiskLevel.LOW,
        required_permission=Permission.CHAT,
        requires_confirmation=False,
        description="Conversational reasoning and information synthesis."
    )
}

class ToolPolicyEngine:
    """Central Tool Policy Engine binding tools to granular permissions, operational risk, path sanitization, and confirmation gates."""

    def __init__(self):
        self.policies: Dict[str, ToolPolicy] = DEFAULT_TOOL_POLICIES.copy()

    def get_policy(self, tool_name: str) -> ToolPolicy:
        """Retrieves policy for a given tool name, defaulting to restrictive policy for unknown tools."""
        key = tool_name.lower().strip()
        if key in self.policies:
            return self.policies[key]

        # Secure default: unknown tools are treated as HIGH risk requiring OWNER permission
        return ToolPolicy(
            tool_name=tool_name,
            risk_level=RiskLevel.HIGH,
            required_permission=Permission.SYSTEM_CONTROL,
            requires_confirmation=True,
            description="Unregistered or custom dynamic tool."
        )

    def validate_execution(
        self,
        user: User,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        confirmation_ticket_id: Optional[str] = None
    ) -> RiskAssessment:
        """Validates permission, determines risk, checks path and network arguments, and verifies confirmation ticket."""
        args = arguments or {}
        policy = self.get_policy(tool_name)

        # 1. Enforce RBAC permission
        rbac_engine.enforce_permission(user, policy.required_permission, f"Execute tool '{tool_name}'")

        # 2. Assess Risk dynamically
        target_str = str(args.get("target") or args.get("device_id") or args.get("path") or "")
        cmd_str = str(args.get("command") or args.get("action") or "")
        assessment = risk_engine.assess_risk(tool_name, target=target_str, command=cmd_str, metadata=args)

        # 3. Path Security Validation if file argument is present
        file_path = args.get("file_path") or args.get("path") or args.get("target_path")
        if file_path and isinstance(file_path, str):
            path_validator.sanitize_path(file_path)

        # 4. SSRF Validation if URL argument is present
        url_target = args.get("url") or args.get("target_url")
        if url_target and isinstance(url_target, str):
            ssrf_validator.validate_url(url_target, allow_private=("iot" in tool_name.lower()))

        # 5. Confirmation Verification for High/Critical Risk actions
        if assessment.requires_confirmation:
            if not confirmation_ticket_id:
                # Generate new ticket for user
                ticket = confirmation_engine.create_ticket(
                    user_id=user.id,
                    action=tool_name,
                    target=target_str,
                    risk_level=assessment.risk_level,
                    command=cmd_str,
                    parameters=args
                )
                assessment.impact_details["confirmation_required"] = True
                assessment.impact_details["ticket_id"] = ticket.ticket_id
                assessment.impact_details["message"] = f"HIGH-RISK OPERATION: Action '{tool_name}' requires explicit confirmation. Ticket ID: {ticket.ticket_id}"
                raise PermissionError(f"Confirmation required for action '{tool_name}' (Risk: {assessment.risk_level}). Ticket generated: {ticket.ticket_id}")

            ticket = confirmation_engine.get_ticket(confirmation_ticket_id)
            if not ticket or not ticket.confirmed:
                raise PermissionError(f"Confirmation ticket '{confirmation_ticket_id}' is invalid or unconfirmed.")

        return assessment

tool_policy_engine = ToolPolicyEngine()
