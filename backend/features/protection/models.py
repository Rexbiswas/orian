import time
from enum import Enum
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

# -----------------------------------------------------------------------------
# ENUMS
# -----------------------------------------------------------------------------
class DeviceStatus(str, Enum):
    UNREGISTERED = "UNREGISTERED"
    PAIRING = "PAIRING"
    OWNER_APPROVAL = "OWNER_APPROVAL"
    REGISTERED = "REGISTERED"
    AUTHORIZED = "AUTHORIZED"
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"

class ProductivityCategory(str, Enum):
    GAMING = "GAMING"
    STREAMING = "STREAMING"
    SOCIAL_MEDIA = "SOCIAL_MEDIA"
    BLOCKED_APPS = "BLOCKED_APPS"
    BLOCKED_DOMAINS = "BLOCKED_DOMAINS"
    TERMINAL = "TERMINAL"
    SENSITIVE_TOPICS = "SENSITIVE_TOPICS"
    FOCUS_MODE_BYPASS = "FOCUS_MODE_BYPASS"
    UNAUTHORIZED_APPS = "UNAUTHORIZED_APPS"

class SecurityCategory(str, Enum):
    MALWARE_ACTIVITY = "MALWARE_ACTIVITY"
    UNAUTHORIZED_HACKING = "UNAUTHORIZED_HACKING"
    ILLEGAL_ACTIVITY = "ILLEGAL_ACTIVITY"
    SECURITY_TAMPERING = "SECURITY_TAMPERING"
    PROTECTED_DATA_ACCESS = "PROTECTED_DATA_ACCESS"

class EnforcementAction(str, Enum):
    LOG = "LOG"
    NOTIFY = "NOTIFY"
    WARN = "WARN"
    BLOCK = "BLOCK"
    LOCK = "LOCK"
    SLEEP = "SLEEP"

class ProtectionRiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class FocusMode(str, Enum):
    OFF = "OFF"
    WORK = "WORK"
    STUDY = "STUDY"
    CUSTOM = "CUSTOM"

class RuleType(str, Enum):
    WHITELIST = "WHITELIST"
    BLACKLIST = "BLACKLIST"

class WhitelistCategory(str, Enum):
    ALWAYS_ALLOWED = "ALWAYS_ALLOWED"
    ALLOWED_DURING_FOCUS = "ALLOWED_DURING_FOCUS"
    AUTHORIZED_SECURITY_LAB = "AUTHORIZED_SECURITY_LAB"
    AUTHORIZED_DEVELOPMENT_TOOL = "AUTHORIZED_DEVELOPMENT_TOOL"

# -----------------------------------------------------------------------------
# CORE DOMAIN ENTITIES
# -----------------------------------------------------------------------------
class LaptopDevice(BaseModel):
    device_id: str
    device_name: str
    agent_version: str = "1.0.0"
    owner_id: str
    auth_token_hash: str
    status: DeviceStatus = DeviceStatus.PAIRING
    pairing_code: Optional[str] = None
    revoked: bool = False
    created_at: float = Field(default_factory=time.time)
    last_seen: float = Field(default_factory=time.time)
    metadata_json: Dict[str, Any] = Field(default_factory=dict)

class ProductivityPolicy(BaseModel):
    policy_id: str
    category: ProductivityCategory
    name: str
    description: str = ""
    enabled: bool = True
    focus_only: bool = True
    min_duration_seconds: int = 0
    max_violations_before_escalation: int = 3
    default_action: EnforcementAction = EnforcementAction.WARN
    escalation_action: EnforcementAction = EnforcementAction.SLEEP
    grace_period_seconds: int = 10
    risk_level: ProtectionRiskLevel = ProtectionRiskLevel.MEDIUM
    match_apps: List[str] = Field(default_factory=list)
    match_domains: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class SecurityPolicy(BaseModel):
    policy_id: str
    category: SecurityCategory
    name: str
    description: str = ""
    enabled: bool = True
    default_action: EnforcementAction = EnforcementAction.BLOCK
    risk_level: ProtectionRiskLevel = ProtectionRiskLevel.CRITICAL
    allow_labs_whitelist: bool = True
    rules_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: float = Field(default_factory=time.time)
    updated_at: float = Field(default_factory=time.time)

class ActivityRule(BaseModel):
    rule_id: str
    rule_type: RuleType
    category: str
    target: str
    description: str = ""
    created_at: float = Field(default_factory=time.time)

class FocusSession(BaseModel):
    session_id: str
    mode: FocusMode = FocusMode.WORK
    is_active: bool = True
    start_time: float = Field(default_factory=time.time)
    end_time: Optional[float] = None
    schedule_start: str = "09:00"
    schedule_end: str = "18:00"
    schedule_days: List[str] = Field(default_factory=lambda: ["mon", "tue", "wed", "thu", "fri"])
    created_by: str = "system"

class ActivityEvent(BaseModel):
    event_id: str
    device_id: str
    category: str
    application: str = ""
    process_name: str = ""
    window_title_sanitized: str = ""
    duration_seconds: float = 0.0
    timestamp: float = Field(default_factory=time.time)
    policy_id: Optional[str] = None
    risk_level: ProtectionRiskLevel = ProtectionRiskLevel.LOW
    action_taken: EnforcementAction = EnforcementAction.LOG
    matched_rule: Optional[str] = None

class PolicyViolation(BaseModel):
    violation_id: str
    event_id: Optional[str] = None
    device_id: str
    policy_id: str
    violation_count: int = 1
    risk_level: ProtectionRiskLevel
    action_enforced: EnforcementAction
    warning_issued_at: float = Field(default_factory=time.time)
    grace_period_expires_at: float
    overridden: bool = False
    overridden_by: Optional[str] = None
    status: str = "PENDING"  # PENDING, WARNED, OVERRIDDEN, ENFORCED, CANCELLED
    created_at: float = Field(default_factory=time.time)

class PolicyOverride(BaseModel):
    override_id: str
    violation_id: str
    user_id: str
    policy_id: str
    reason: str
    risk_level: ProtectionRiskLevel
    timestamp: float = Field(default_factory=time.time)

class LaptopCommand(BaseModel):
    request_id: str
    device_id: str
    command: str  # GET_STATUS, NOTIFY, LOCK, SLEEP
    policy_id: Optional[str] = None
    reason: str = "PRODUCTIVITY_POLICY"
    timestamp: float = Field(default_factory=time.time)
    expires_at: float
    signature: Optional[str] = None
    status: str = "ISSUED"  # ISSUED, ACKNOWLEDGED, EXECUTED, FAILED, EXPIRED, REJECTED
    result_json: Dict[str, Any] = Field(default_factory=dict)

class LaptopCommandResult(BaseModel):
    success: bool
    command: str
    device_id: str
    request_id: str
    message: Optional[str] = None
    error: Optional[str] = None
    timestamp: float = Field(default_factory=time.time)

# -----------------------------------------------------------------------------
# API REQUEST & RESPONSE SCHEMAS
# -----------------------------------------------------------------------------
class DeviceRegisterRequest(BaseModel):
    device_id: str
    device_name: str
    agent_version: str = "1.0.0"
    client_public_key: Optional[str] = None

class DeviceApproveRequest(BaseModel):
    device_id: str
    approved: bool
    owner_password_or_token: Optional[str] = None

class DeviceHeartbeatRequest(BaseModel):
    device_id: str
    agent_version: str = "1.0.0"
    active_app: Optional[str] = None
    status: str = "ACTIVE"

class DeviceRevokeRequest(BaseModel):
    device_id: str
    reason: str = "Owner manual revocation"

class ActivityReportRequest(BaseModel):
    device_id: str
    application: str
    process_name: str
    window_title: Optional[str] = None
    duration_seconds: float = 0.0
    domain: Optional[str] = None
    category_hint: Optional[str] = None
    security_signal: Optional[Dict[str, Any]] = None

class PolicyOverrideRequest(BaseModel):
    violation_id: str
    reason: str
    step_up_code: Optional[str] = None
    password: Optional[str] = None

class FocusConfigRequest(BaseModel):
    mode: FocusMode
    schedule_start: Optional[str] = "09:00"
    schedule_end: Optional[str] = "18:00"
    schedule_days: Optional[List[str]] = None

class EmergencyDisableRequest(BaseModel):
    disable_all_protection: Optional[bool] = False
    disable_automatic_sleep: Optional[bool] = False
    disable_policy_id: Optional[str] = None
    owner_verification: str
