import time
import logging
from typing import Callable, Any, Dict, Optional
from .models import User, RiskAssessment, RiskLevel
from .rbac import rbac_engine
from .risk_engine import risk_engine
from .tool_policy import tool_policy_engine
from .audit_logger import audit_logger

logger = logging.getLogger("orian.security.gateway")

class SecurityGateway:
    """Master Orian Security Gateway: The single authority enforcing authentication, RBAC authorization, risk evaluation, confirmation tickets, and audit logging."""

    def __init__(self):
        self.tool_policy = tool_policy_engine
        self.audit = audit_logger
        self.risk = risk_engine
        self.rbac = rbac_engine

    def execute_secured(
        self,
        user: User,
        tool_name: str,
        tool_callable: Callable[..., Any],
        arguments: Optional[Dict[str, Any]] = None,
        confirmation_ticket_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: str = "",
        ip_address: str = "127.0.0.1"
    ) -> Dict[str, Any]:
        """Executes a tool within complete Security Gateway governance."""
        args = arguments or {}
        target_str = str(args.get("target") or args.get("device_id") or args.get("path") or tool_name)
        start_time = time.time()

        try:
            # 1. Validate permissions, path safety, and confirmation ticket
            assessment = self.tool_policy.validate_execution(
                user=user,
                tool_name=tool_name,
                arguments=args,
                confirmation_ticket_id=confirmation_ticket_id
            )

            # 2. Execute underlying tool function
            result = tool_callable(**args)
            execution_time = time.time() - start_time

            # 3. Record successful execution audit log
            self.audit.log_audit(
                action=f"TOOL_EXECUTE:{tool_name}",
                tool=tool_name,
                target=target_str,
                risk=assessment.risk_level,
                result="SUCCESS",
                user_id=user.id,
                session_id=session_id,
                ip_address=ip_address,
                request_id=request_id,
                details={
                    "arguments": args,
                    "execution_time_sec": execution_time,
                    "risk_score": assessment.score
                }
            )

            return {
                "success": True,
                "result": result,
                "tool": tool_name,
                "risk_level": assessment.risk_level.value,
                "execution_time": execution_time
            }

        except PermissionError as pe:
            err_msg = str(pe)
            self.audit.log_audit(
                action=f"TOOL_DENIED:{tool_name}",
                tool=tool_name,
                target=target_str,
                risk=RiskLevel.HIGH,
                result="DENIED",
                error_message=err_msg,
                user_id=user.id,
                session_id=session_id,
                ip_address=ip_address,
                request_id=request_id,
                details={"arguments": args}
            )
            return {
                "success": False,
                "error": err_msg,
                "tool": tool_name,
                "permission_denied": True
            }

        except Exception as e:
            err_msg = str(e)
            self.audit.log_audit(
                action=f"TOOL_FAULT:{tool_name}",
                tool=tool_name,
                target=target_str,
                risk=RiskLevel.MEDIUM,
                result="FAILED",
                error_message=err_msg,
                user_id=user.id,
                session_id=session_id,
                ip_address=ip_address,
                request_id=request_id,
                details={"arguments": args}
            )
            return {
                "success": False,
                "error": f"Tool execution fault: {err_msg}",
                "tool": tool_name
            }

security_gateway = SecurityGateway()
