import time
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class Role(str, Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    TRUSTED_USER = "TRUSTED_USER"
    USER = "USER"
    GUEST = "GUEST"
    DEVICE = "DEVICE"

class Permission(str, Enum):
    CHAT = "chat"
    CALCULATOR = "calculator"
    READ_MEMORY = "read_memory"
    WRITE_MEMORY = "write_memory"
    OPEN_APPLICATION = "open_application"
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_COMMAND = "execute_command"
    IOT_READ = "iot_read"
    IOT_CONTROL = "iot_control"
    SYSTEM_CONTROL = "system_control"
    CODE_READ = "code_read"
    CODE_MODIFY = "code_modify"
    SELF_DIAGNOSE = "self_diagnose"
    SELF_PROGRAM = "self_program"
    SECURITY_ADMIN = "security_admin"
    USER_ADMIN = "user_admin"

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class SecurityEventSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

# -----------------------------------------------------------------------------
# CORE DOMAIN ENTITIES
# -----------------------------------------------------------------------------
class User(BaseModel):
    id: str
    username: str
    display_name: str = ""
    email: Optional[str] = None
    role: Role = Role.USER
    is_active: bool = True
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None  # Encrypted in DB
    failed_login_attempts: int = 0
    locked_until: Optional[float] = None
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class Session(BaseModel):
    id: str
    user_id: str
    role: Role
    token_hash: str
    ip_address: str = "127.0.0.1"
    user_agent: str = "Unknown"
    is_mfa_verified: bool = False
    is_active: bool = True
    created_at: float = Field(default_factory=time.time)
    last_active: float = Field(default_factory=time.time)
    expires_at: float

class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    score: int  # 0 to 100
    reason: str
    requires_confirmation: bool = False
    requires_mfa: bool = False
    target: str = ""
    action: str = ""
    impact_details: Dict[str, Any] = Field(default_factory=dict)

class ConfirmationTicket(BaseModel):
    ticket_id: str
    user_id: str
    action: str
    target: str
    risk_level: RiskLevel
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    expires_at: float
    confirmed: bool = False
    confirmed_at: Optional[float] = None

class ToolPolicy(BaseModel):
    tool_name: str
    risk_level: RiskLevel
    required_permission: Permission
    requires_confirmation: bool = False
    requires_mfa: bool = False
    allow_sandbox_dry_run: bool = True
    allowed_arguments: List[str] = Field(default_factory=list)
    description: str = ""

class AuditLogEntry(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    user_id: str = "anonymous"
    session_id: Optional[str] = None
    action: str
    tool: str = "System"
    target: str = ""
    risk: RiskLevel = RiskLevel.LOW
    result: str = "SUCCESS"  # SUCCESS, FAILED, DENIED, CONFIRMED, ROLLED_BACK
    error_message: Optional[str] = None
    ip_address: str = "127.0.0.1"
    device: str = "Desktop"
    request_id: str = ""
    details_json: str = "{}"

class SecurityEvent(BaseModel):
    id: str
    timestamp: float = Field(default_factory=time.time)
    event_type: str  # AUTH_LOGIN_SUCCESS, PERMISSION_DENIED, etc.
    severity: SecurityEventSeverity = SecurityEventSeverity.INFO
    user_id: Optional[str] = None
    ip_address: str = "127.0.0.1"
    message: str
    details_json: str = "{}"

# -----------------------------------------------------------------------------
# API SCHEMAS
# -----------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    username: str
    password: str
    display_name: Optional[str] = None
    email: Optional[str] = None
    initial_role: Optional[Role] = Role.USER

class LoginRequest(BaseModel):
    username: str
    password: str
    totp_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_id: str
    username: str
    role: str
    mfa_required: bool = False
    mfa_enrolled: bool = False

class MFASetupResponse(BaseModel):
    secret: str
    provisioning_uri: str
    qr_svg: Optional[str] = None

class MFAVerifyRequest(BaseModel):
    code: str

class ConfirmationSubmitRequest(BaseModel):
    ticket_id: str
    approved: bool
    step_up_code: Optional[str] = None
