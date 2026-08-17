import time
import json
import uuid
import logging
from typing import Optional, Tuple, Dict, Any, List
import jwt

from .config import security_config
from .crypto import crypto_engine
from .database import security_db
from .models import User, Session, Role, TokenResponse, SecurityEventSeverity

logger = logging.getLogger("orian.security.auth")

class AuthEngine:
    """Enterprise Authentication Engine managing Argon2id authentication, JWT issuance, session lifecycle, failed attempt lockouts, and token rotation."""

    def __init__(self):
        self.db = security_db
        self.config = security_config
        self.crypto = crypto_engine
        self._ensure_bootstrap_owner()

    def _ensure_bootstrap_owner(self):
        """Initializes a default local OWNER account if no users exist in the system."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM sec_users")
        row = cursor.fetchone()
        count = row["count"] if row else 0
        conn.close()

        if count == 0:
            logger.info("No users found. Creating initial local OWNER account (orian_admin)...")
            self.register_user(
                username="orian_admin",
                password="OrianSecureMasterKey2026!",
                display_name="Orian Administrator",
                role=Role.OWNER
            )

    # -------------------------------------------------------------------------
    # 1. USER REGISTRATION
    # -------------------------------------------------------------------------
    def register_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        role: Role = Role.USER
    ) -> User:
        """Registers a new user with Argon2id password hashing."""
        username = username.strip().lower()
        if len(username) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters")

        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Check uniqueness
        cursor.execute("SELECT id FROM sec_users WHERE username = ?", (username,))
        if cursor.fetchone():
            conn.close()
            raise ValueError(f"Username '{username}' is already registered")

        user_id = f"usr_{uuid.uuid4().hex[:12]}"
        password_hash = self.crypto.hash_password(password)
        now = time.time()

        cursor.execute("""
        INSERT INTO sec_users (
            id, username, password_hash, display_name, email, role,
            is_active, mfa_enabled, mfa_secret_encrypted,
            failed_login_attempts, locked_until, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, 1, 0, NULL, 0, NULL, ?, ?)
        """, (
            user_id, username, password_hash, display_name or username.title(),
            email, role.value if isinstance(role, Role) else str(role), now, now
        ))
        conn.commit()
        conn.close()

        # Record security event
        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="AUTH_REGISTER_SUCCESS",
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            message=f"New user registered: {username} with role {role.value if isinstance(role, Role) else role}"
        )

        return self.get_user_by_id(user_id)

    # -------------------------------------------------------------------------
    # 2. USER AUTHENTICATION & LOGIN
    # -------------------------------------------------------------------------
    def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: str = "127.0.0.1",
        user_agent: str = "Unknown",
        totp_code: Optional[str] = None
    ) -> TokenResponse:
        """Authenticates user credentials, enforces lockout protection, checks MFA, and creates an active session."""
        username = username.strip().lower()
        now = time.time()
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM sec_users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="AUTH_LOGIN_FAILED",
                severity=SecurityEventSeverity.WARNING,
                ip_address=ip_address,
                message=f"Login failed: Unknown username '{username}'"
            )
            raise ValueError("Invalid username or password")

        user_dict = dict(row)
        user_id = user_dict["id"]

        # Check account lock status
        if user_dict["locked_until"] and user_dict["locked_until"] > now:
            conn.close()
            remaining = int(user_dict["locked_until"] - now)
            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="AUTH_ACCOUNT_LOCKED",
                severity=SecurityEventSeverity.HIGH,
                user_id=user_id,
                ip_address=ip_address,
                message=f"Login attempt on locked account '{username}'. Lock remaining: {remaining}s"
            )
            raise PermissionError(f"Account is temporarily locked due to failed attempts. Retry in {remaining} seconds.")

        # Check active status
        if not user_dict["is_active"]:
            conn.close()
            raise PermissionError("Account has been deactivated by administrator.")

        # Verify password
        is_password_valid = self.crypto.verify_password(password, user_dict["password_hash"])

        if not is_password_valid:
            failed_attempts = user_dict["failed_login_attempts"] + 1
            locked_until = None

            if failed_attempts >= self.config.MAX_FAILED_LOGIN_ATTEMPTS:
                locked_until = now + self.config.LOCKOUT_DURATION_SECONDS
                logger.warning(f"Account '{username}' locked for {self.config.LOCKOUT_DURATION_SECONDS}s after {failed_attempts} failed attempts.")

            cursor.execute("""
            UPDATE sec_users
            SET failed_login_attempts = ?, locked_until = ?, updated_at = ?
            WHERE id = ?
            """, (failed_attempts, locked_until, now, user_id))
            conn.commit()
            conn.close()

            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="AUTH_LOGIN_FAILED",
                severity=SecurityEventSeverity.WARNING,
                user_id=user_id,
                ip_address=ip_address,
                message=f"Invalid password for user '{username}'. Attempt {failed_attempts}/{self.config.MAX_FAILED_LOGIN_ATTEMPTS}"
            )
            raise ValueError("Invalid username or password")

        # Reset failed attempts upon successful password verification
        cursor.execute("UPDATE sec_users SET failed_login_attempts = 0, locked_until = NULL, updated_at = ? WHERE id = ?", (now, user_id))
        conn.commit()

        # Check MFA if enabled
        is_mfa_verified = False
        mfa_required = bool(user_dict["mfa_enabled"] and self.config.MFA_ENABLED)

        if mfa_required:
            from .mfa_engine import mfa_engine
            if totp_code:
                is_mfa_verified = mfa_engine.verify_user_totp(user_id, totp_code)
                if not is_mfa_verified:
                    conn.close()
                    from .audit_logger import audit_logger
                    audit_logger.log_security_event(
                        event_type="MFA_FAILED",
                        severity=SecurityEventSeverity.HIGH,
                        user_id=user_id,
                        ip_address=ip_address,
                        message=f"Invalid MFA TOTP code submitted for user '{username}'"
                    )
                    raise ValueError("Invalid Multi-Factor Authentication (TOTP) code")
            else:
                conn.close()
                # Return partial token prompting for MFA
                return TokenResponse(
                    access_token="",
                    refresh_token="",
                    expires_in=0,
                    user_id=user_id,
                    username=username,
                    role=user_dict["role"],
                    mfa_required=True,
                    mfa_enrolled=True
                )

        # Create session
        session_id = f"ses_{uuid.uuid4().hex[:16]}"
        expires_at = now + (self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        session_token = self.crypto.generate_token(32)
        token_hash = self.crypto.hash_sha256(session_token)

        cursor.execute("""
        INSERT INTO sec_sessions (
            id, user_id, role, token_hash, ip_address, user_agent,
            is_mfa_verified, is_active, created_at, last_active, expires_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
        """, (
            session_id, user_id, user_dict["role"], token_hash,
            ip_address, user_agent, 1 if is_mfa_verified else 0,
            now, now, expires_at
        ))
        conn.commit()
        conn.close()

        # Issue JWT Access & Refresh Tokens
        jwt_payload = {
            "sub": user_id,
            "session_id": session_id,
            "username": username,
            "role": user_dict["role"],
            "mfa_verified": is_mfa_verified,
            "iat": int(now),
            "exp": int(expires_at)
        }
        access_token = jwt.encode(jwt_payload, self.config.SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)

        refresh_payload = {
            "sub": user_id,
            "session_id": session_id,
            "type": "refresh",
            "iat": int(now),
            "exp": int(now + (self.config.REFRESH_TOKEN_EXPIRE_DAYS * 86400))
        }
        refresh_token = jwt.encode(refresh_payload, self.config.SECRET_KEY, algorithm=self.config.JWT_ALGORITHM)

        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="AUTH_LOGIN_SUCCESS",
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            ip_address=ip_address,
            message=f"User '{username}' successfully logged in (Session: {session_id[:8]})"
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=self.config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user_id,
            username=username,
            role=user_dict["role"],
            mfa_required=False,
            mfa_enrolled=bool(user_dict["mfa_enabled"])
        )

    # -------------------------------------------------------------------------
    # 3. SESSION TOKEN VALIDATION
    # -------------------------------------------------------------------------
    def validate_token(self, token_str: str) -> Tuple[User, Session]:
        """Decodes JWT, verifies active session in database, and updates activity timer."""
        if not token_str:
            raise ValueError("Token is required")

        try:
            payload = jwt.decode(token_str, self.config.SECRET_KEY, algorithms=[self.config.JWT_ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise PermissionError("Session token has expired. Please log in again.")
        except jwt.InvalidTokenError as e:
            raise PermissionError(f"Invalid authentication token: {e}")

        user_id = payload.get("sub")
        session_id = payload.get("session_id")

        if not user_id or not session_id:
            raise PermissionError("Malformed session token payload")

        now = time.time()
        conn = self.db.get_connection()
        cursor = conn.cursor()

        # Check session
        cursor.execute("SELECT * FROM sec_sessions WHERE id = ? AND is_active = 1", (session_id,))
        session_row = cursor.fetchone()

        if not session_row:
            conn.close()
            raise PermissionError("Session has been revoked or terminated")

        session_dict = dict(session_row)

        if session_dict["expires_at"] < now:
            cursor.execute("UPDATE sec_sessions SET is_active = 0 WHERE id = ?", (session_id,))
            conn.commit()
            conn.close()
            raise PermissionError("Session has expired")

        # Update last_active
        cursor.execute("UPDATE sec_sessions SET last_active = ? WHERE id = ?", (now, session_id))
        conn.commit()

        # Get user
        cursor.execute("SELECT * FROM sec_users WHERE id = ? AND is_active = 1", (user_id,))
        user_row = cursor.fetchone()
        conn.close()

        if not user_row:
            raise PermissionError("User associated with session not found or inactive")

        user_dict = dict(user_row)
        user = User(
            id=user_dict["id"],
            username=user_dict["username"],
            display_name=user_dict.get("display_name") or user_dict["username"],
            email=user_dict.get("email"),
            role=Role(user_dict["role"]),
            is_active=bool(user_dict["is_active"]),
            mfa_enabled=bool(user_dict["mfa_enabled"]),
            failed_login_attempts=user_dict["failed_login_attempts"],
            locked_until=user_dict.get("locked_until"),
            created_at=user_dict["created_at"],
            updated_at=user_dict["updated_at"]
        )

        session = Session(
            id=session_dict["id"],
            user_id=session_dict["user_id"],
            role=Role(session_dict["role"]),
            token_hash=session_dict["token_hash"],
            ip_address=session_dict.get("ip_address", "127.0.0.1"),
            user_agent=session_dict.get("user_agent", "Unknown"),
            is_mfa_verified=bool(session_dict["is_mfa_verified"]),
            is_active=bool(session_dict["is_active"]),
            created_at=session_dict["created_at"],
            last_active=now,
            expires_at=session_dict["expires_at"]
        )

        return user, session

    # -------------------------------------------------------------------------
    # 4. LOGOUT & SESSION REVOCATION
    # -------------------------------------------------------------------------
    def logout_session(self, session_id: str):
        """Revokes an active session."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sec_sessions SET is_active = 0 WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()

    def revoke_all_user_sessions(self, user_id: str):
        """Revokes all active sessions for a given user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE sec_sessions SET is_active = 0 WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Retrieves a user object by ID."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sec_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return None
        d = dict(row)
        return User(
            id=d["id"],
            username=d["username"],
            display_name=d.get("display_name") or d["username"],
            email=d.get("email"),
            role=Role(d["role"]),
            is_active=bool(d["is_active"]),
            mfa_enabled=bool(d["mfa_enabled"]),
            failed_login_attempts=d["failed_login_attempts"],
            locked_until=d.get("locked_until"),
            created_at=d["created_at"],
            updated_at=d["updated_at"]
        )

auth_engine = AuthEngine()
