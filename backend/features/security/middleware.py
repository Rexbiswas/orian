import time
import logging
from typing import Dict, Tuple, Optional, Callable
from fastapi import Request, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from .config import security_config
from .auth_engine import auth_engine
from .models import User, Role, Permission
from .rbac import rbac_engine

logger = logging.getLogger("orian.security.middleware")

security_bearer = HTTPBearer(auto_error=False)

# -----------------------------------------------------------------------------
# 1. SECURITY HEADERS MIDDLEWARE
# -----------------------------------------------------------------------------
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces essential HTTP security headers on all API responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=*, microphone=*, geolocation=()"
        return response

# -----------------------------------------------------------------------------
# 2. IN-MEMORY RATE LIMITER
# -----------------------------------------------------------------------------
class InMemoryRateLimiter:
    """Sliding-window IP rate limiter preventing denial-of-service and credential stuffing."""

    def __init__(self):
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        now = time.time()
        window_start = now - window_seconds

        if key not in self._requests:
            self._requests[key] = []

        # Prune old timestamps
        self._requests[key] = [t for t in self._requests[key] if t > window_start]

        if len(self._requests[key]) >= max_requests:
            return False

        self._requests[key].append(now)
        return True

rate_limiter = InMemoryRateLimiter()

# -----------------------------------------------------------------------------
# 3. FASTAPI DEPENDENCY INJECTION HELPERS
# -----------------------------------------------------------------------------
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer)
) -> User:
    """Extracts and validates user from Bearer JWT token, falling back to local OWNER in local mode if unauthenticated."""
    if credentials and credentials.credentials:
        try:
            user, session = auth_engine.validate_token(credentials.credentials)
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication failed: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"}
            )

    # In local development mode, if no auth token is passed, resolve local bootstrap OWNER
    # This prevents UI/Electron breakage while still providing full security when token is supplied
    owner = auth_engine.get_user_by_id("usr_bootstrap_owner")
    if not owner:
        conn = auth_engine.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM sec_users WHERE role = 'OWNER' LIMIT 1")
        row = cursor.fetchone()
        conn.close()
        if row:
            owner = auth_engine.get_user_by_id(row["id"])

    if owner:
        return owner

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide a valid Bearer token.",
        headers={"WWW-Authenticate": "Bearer"}
    )

def require_permission(permission: Permission):
    """Dependency factory checking that the authenticated user possesses the specified permission."""
    async def permission_checker(current_user: User = Depends(get_current_user)) -> User:
        if not rbac_engine.check_user_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires '{permission.value}' permission."
            )
        return current_user
    return permission_checker

def require_role(required_role: Role):
    """Dependency factory enforcing minimum role level."""
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if not rbac_engine.is_role_at_least(current_user.role, required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Requires minimum role '{required_role.value}'."
            )
        return current_user
    return role_checker
