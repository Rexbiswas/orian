import sys
import os

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from .config import security_config, SecurityConfig
from .crypto import crypto_engine, CryptoEngine
from .models import (
    User, Role, Permission, Session, RiskLevel, RiskAssessment,
    ConfirmationTicket, SecurityEvent, AuditLogEntry, ToolPolicy,
    RegisterRequest, LoginRequest, TokenResponse, MFASetupResponse,
    MFAVerifyRequest, ConfirmationSubmitRequest
)
from .database import security_db, SecurityDatabase
from .auth_engine import auth_engine, AuthEngine
from .mfa_engine import mfa_engine, MFAEngine
from .rbac import rbac_engine, RBACEngine
from .risk_engine import risk_engine, RiskEngine
from .confirmation_engine import confirmation_engine, ConfirmationEngine
from .path_validator import path_validator, PathValidator
from .ssrf_validator import ssrf_validator, SSRFValidator
from .tool_policy import tool_policy_engine, ToolPolicyEngine
from .audit_logger import audit_logger, AuditLogger
from .self_programming_guard import self_programming_guard, SelfProgrammingGuard
from .gateway import security_gateway, SecurityGateway

__all__ = [
    "security_config",
    "SecurityConfig",
    "crypto_engine",
    "CryptoEngine",
    "User",
    "Role",
    "Permission",
    "Session",
    "RiskLevel",
    "RiskAssessment",
    "ConfirmationTicket",
    "SecurityEvent",
    "AuditLogEntry",
    "ToolPolicy",
    "security_db",
    "SecurityDatabase",
    "auth_engine",
    "AuthEngine",
    "mfa_engine",
    "MFAEngine",
    "rbac_engine",
    "RBACEngine",
    "risk_engine",
    "RiskEngine",
    "confirmation_engine",
    "ConfirmationEngine",
    "path_validator",
    "PathValidator",
    "ssrf_validator",
    "SSRFValidator",
    "tool_policy_engine",
    "ToolPolicyEngine",
    "audit_logger",
    "AuditLogger",
    "self_programming_guard",
    "SelfProgrammingGuard",
    "security_gateway",
    "SecurityGateway",
]
