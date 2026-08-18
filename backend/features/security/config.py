import os
import secrets
from typing import List
from pydantic import BaseModel, Field

class SecurityConfig(BaseModel):
    """Centralized Orian Security Configuration with secure-by-default parameters."""

    # 1. Master Security Toggles
    AUTH_ENABLED: bool = Field(default=True)
    MFA_ENABLED: bool = Field(default=True)
    AUDIT_LOGGING_ENABLED: bool = Field(default=True)
    
    # 2. Cryptographic Secrets
    # Generated securely if not provided in environment
    SECRET_KEY: str = Field(default_factory=lambda: os.getenv("ORIAN_SECRET_KEY", secrets.token_hex(32)))
    ENCRYPTION_KEY: str = Field(default_factory=lambda: os.getenv("ORIAN_ENCRYPTION_KEY", secrets.token_hex(32)))
    
    # 3. JWT & Session Expiration
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    SESSION_IDLE_TIMEOUT_MINUTES: int = 120
    
    # 4. Brute-Force & Rate Limiting
    MAX_FAILED_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_SECONDS: int = 300  # 5 minutes backoff
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = 120
    RATE_LIMIT_AUTH_PER_MINUTE: int = 10
    RATE_LIMIT_IOT_PER_MINUTE: int = 60
    
    # 5. Risk & Confirmation Gates
    REQUIRE_CONFIRMATION_FOR_MEDIUM_RISK: bool = False
    REQUIRE_CONFIRMATION_FOR_HIGH_RISK: bool = True
    REQUIRE_MFA_FOR_CRITICAL_RISK: bool = True
    CONFIRMATION_TICKET_TTL_SECONDS: int = 120
    
    # 6. IoT & Hardware Security
    IOT_REQUIRE_AUTHENTICATION: bool = True
    IOT_REPLAY_WINDOW_SECONDS: int = 60
    IOT_MAX_CLOCK_SKEW_SECONDS: int = 15
    IOT_TLS_REQUIRED_IN_PRODUCTION: bool = False
    
    # 7. Self-Programming & Code Integrity
    SELF_PROGRAMMING_ENABLED: bool = True
    SELF_PROGRAMMING_REQUIRES_OWNER: bool = True
    SELF_PROGRAMMING_MANDATORY_GIT_CHECKPOINT: bool = True
    SELF_PROGRAMMING_MANDATORY_TESTS: bool = True
    SELF_PROGRAMMING_AUTO_ROLLBACK: bool = True
    
    # 8. Protected System & Code Paths (Self-Programming Protection)
    PROTECTED_DIRECTORIES: List[str] = [
        "security",
        "auth",
        ".git",
        ".env",
        "orian_storage/orian_core.db",
        "backend/features/security",
        "backend/features/protection",
        "backend/laptop_agent",
        "protection",
        "laptop_agent",
    ]
    
    # 9. Allowed CORS Origins (Never wildcards in production)
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "capacitor://localhost",
        "http://localhost",
    ]

security_config = SecurityConfig()
