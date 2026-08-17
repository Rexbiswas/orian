import io
import time
import logging
from typing import Optional, Tuple, Dict, Any
import pyotp
import qrcode
import qrcode.image.svg

from .config import security_config
from .crypto import crypto_engine
from .database import security_db
from .models import MFASetupResponse, SecurityEventSeverity

logger = logging.getLogger("orian.security.mfa")

class MFAEngine:
    """Enterprise Multi-Factor Authentication (MFA) Engine managing TOTP enrollment, secret encryption, QR generation, and step-up verification."""

    def __init__(self):
        self.db = security_db
        self.crypto = crypto_engine
        self.config = security_config

    # -------------------------------------------------------------------------
    # 1. MFA ENROLLMENT & SECRET GENERATION
    # -------------------------------------------------------------------------
    def generate_mfa_setup(self, user_id: str, username: str) -> MFASetupResponse:
        """Generates a new TOTP secret, encrypts it in DB, and returns provisioning URI with QR code."""
        secret = pyotp.random_base32()
        encrypted_secret = self.crypto.encrypt_data(secret)

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE sec_users
        SET mfa_secret_encrypted = ?, updated_at = ?
        WHERE id = ?
        """, (encrypted_secret, time.time(), user_id))
        conn.commit()
        conn.close()

        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(name=username, issuer_name="Orian AI Enterprise")

        # Generate QR Code in SVG format
        qr_svg = None
        try:
            factory = qrcode.image.svg.SvgPathImage
            img = qrcode.make(provisioning_uri, image_factory=factory)
            stream = io.BytesIO()
            img.save(stream)
            qr_svg = stream.getvalue().decode("utf-8")
        except Exception as e:
            logger.warning(f"Failed to generate QR SVG: {e}")

        return MFASetupResponse(
            secret=secret,
            provisioning_uri=provisioning_uri,
            qr_svg=qr_svg
        )

    # -------------------------------------------------------------------------
    # 2. MFA ENABLING & CONFIRMATION
    # -------------------------------------------------------------------------
    def enable_mfa(self, user_id: str, code: str) -> bool:
        """Verifies enrollment code and enables MFA for the user."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT mfa_secret_encrypted, username FROM sec_users WHERE id = ?", (user_id,))
        row = cursor.fetchone()

        if not row or not row["mfa_secret_encrypted"]:
            conn.close()
            raise ValueError("MFA setup has not been initiated for this account")

        raw_encrypted = row["mfa_secret_encrypted"]
        username = row["username"]
        secret = self.crypto.decrypt_data(raw_encrypted)

        totp = pyotp.TOTP(secret)
        if not totp.verify(code, valid_window=1):
            conn.close()
            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="MFA_ENROLL_FAILED",
                severity=SecurityEventSeverity.WARNING,
                user_id=user_id,
                message=f"Invalid TOTP confirmation code submitted during enrollment for user '{username}'"
            )
            return False

        cursor.execute("UPDATE sec_users SET mfa_enabled = 1, updated_at = ? WHERE id = ?", (time.time(), user_id))
        conn.commit()
        conn.close()

        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="MFA_ENROLLED",
            severity=SecurityEventSeverity.INFO,
            user_id=user_id,
            message=f"MFA successfully enabled for user '{username}'"
        )
        return True

    # -------------------------------------------------------------------------
    # 3. VERIFY TOTP CODE
    # -------------------------------------------------------------------------
    def verify_user_totp(self, user_id: str, code: str) -> bool:
        """Verifies a user's submitted TOTP token."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT mfa_secret_encrypted FROM sec_users WHERE id = ? AND mfa_enabled = 1", (user_id,))
        row = cursor.fetchone()
        conn.close()

        if not row or not row["mfa_secret_encrypted"]:
            return False

        secret = self.crypto.decrypt_data(row["mfa_secret_encrypted"])
        totp = pyotp.TOTP(secret)
        return bool(totp.verify(code, valid_window=1))

    # -------------------------------------------------------------------------
    # 4. DISABLE MFA
    # -------------------------------------------------------------------------
    def disable_mfa(self, user_id: str, code: str) -> bool:
        """Disables MFA for an account after verifying a valid TOTP code."""
        if not self.verify_user_totp(user_id, code):
            raise PermissionError("Invalid TOTP verification code required to disable MFA")

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE sec_users
        SET mfa_enabled = 0, mfa_secret_encrypted = NULL, updated_at = ?
        WHERE id = ?
        """, (time.time(), user_id))
        conn.commit()
        conn.close()

        from .audit_logger import audit_logger
        audit_logger.log_security_event(
            event_type="MFA_DISABLED",
            severity=SecurityEventSeverity.HIGH,
            user_id=user_id,
            message="MFA disabled for user account"
        )
        return True

mfa_engine = MFAEngine()
