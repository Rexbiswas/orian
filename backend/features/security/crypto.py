import os
import hmac
import hashlib
import base64
import secrets
import logging
from typing import Optional

try:
    from argon2 import PasswordHasher
    from argon2.exceptions import VerifyMismatchError, InvalidHashError
    _has_argon2 = True
    _ph = PasswordHasher(
        time_cost=3,
        memory_cost=65536,  # 64 MB
        parallelism=4,
        hash_len=32,
        salt_len=16
    )
except ImportError:
    _has_argon2 = False
    _ph = None

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    _has_crypto = True
except ImportError:
    _has_crypto = False

from .config import security_config

logger = logging.getLogger("orian.security.crypto")

class CryptoEngine:
    """Enterprise Cryptographic Engine providing Argon2id password hashing, AES-256-GCM AEAD encryption, and secure token generators."""

    def __init__(self):
        self._master_key_bytes = self._derive_master_key(security_config.ENCRYPTION_KEY)

    def _derive_master_key(self, key_str: str) -> bytes:
        """Derives a 256-bit key using HKDF-SHA256 or SHA256."""
        raw = key_str.encode("utf-8")
        if _has_crypto:
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b"orian_security_salt_v1",
                info=b"orian_master_encryption_key",
            )
            return hkdf.derive(raw)
        else:
            return hashlib.sha256(raw + b"orian_security_salt_v1").digest()

    # -------------------------------------------------------------------------
    # 1. PASSWORD HASHING (Argon2id with PBKDF2 Fallback)
    # -------------------------------------------------------------------------
    def hash_password(self, password: str) -> str:
        """Hashes password using Argon2id (or PBKDF2-HMAC-SHA256 if Argon2 is unavailable)."""
        if not password:
            raise ValueError("Password cannot be empty")
        
        if _has_argon2 and _ph:
            return _ph.hash(password)
        else:
            # PBKDF2-HMAC-SHA256 with 600,000 iterations and 16-byte random salt
            salt = secrets.token_bytes(16)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600000)
            return f"pbkdf2_sha256$600000${base64.b64encode(salt).decode('utf-8')}${base64.b64encode(dk).decode('utf-8')}"

    def verify_password(self, password: str, hashed_password: str) -> bool:
        """Verifies password against hash in constant time."""
        if not password or not hashed_password:
            return False

        if hashed_password.startswith("$argon2"):
            if _has_argon2 and _ph:
                try:
                    return _ph.verify(hashed_password, password)
                except (VerifyMismatchError, InvalidHashError):
                    return False
                except Exception as e:
                    logger.error(f"Argon2 verification fault: {e}")
                    return False
            return False

        elif hashed_password.startswith("pbkdf2_sha256$"):
            try:
                parts = hashed_password.split("$")
                if len(parts) != 4:
                    return False
                iterations = int(parts[1])
                salt = base64.b64decode(parts[2].encode("utf-8"))
                stored_dk = base64.b64decode(parts[3].encode("utf-8"))
                computed_dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
                return hmac.compare_digest(stored_dk, computed_dk)
            except Exception as e:
                logger.error(f"PBKDF2 verification fault: {e}")
                return False

        return False

    # -------------------------------------------------------------------------
    # 2. DATA ENCRYPTION (AES-256-GCM AEAD Authenticated Encryption)
    # -------------------------------------------------------------------------
    def encrypt_data(self, plaintext: str, custom_key: Optional[bytes] = None) -> str:
        """Encrypts sensitive plaintext using AES-256-GCM authenticated encryption."""
        if not plaintext:
            return ""

        key = custom_key or self._master_key_bytes

        if _has_crypto:
            aesgcm = AESGCM(key)
            nonce = secrets.token_bytes(12)  # 96-bit nonce for AES-GCM
            ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
            combined = nonce + ciphertext
            return base64.urlsafe_b64encode(combined).decode("utf-8")
        else:
            # Fallback simple XOR-HMAC construct if cryptography missing
            salt = secrets.token_bytes(16)
            k = hashlib.pbkdf2_hmac("sha256", key, salt, 100000)
            data_bytes = plaintext.encode("utf-8")
            enc = bytes(b ^ k[i % len(k)] for i, b in enumerate(data_bytes))
            tag = hmac.new(k, enc, hashlib.sha256).digest()
            combined = salt + tag + enc
            return "raw_v1$" + base64.urlsafe_b64encode(combined).decode("utf-8")

    def decrypt_data(self, encrypted_b64: str, custom_key: Optional[bytes] = None) -> str:
        """Decrypts AES-256-GCM ciphertext and verifies AEAD integrity tag."""
        if not encrypted_b64:
            return ""

        key = custom_key or self._master_key_bytes

        try:
            if encrypted_b64.startswith("raw_v1$"):
                payload = base64.urlsafe_b64decode(encrypted_b64[7:].encode("utf-8"))
                salt = payload[:16]
                tag = payload[16:48]
                enc = payload[48:]
                k = hashlib.pbkdf2_hmac("sha256", key, salt, 100000)
                expected_tag = hmac.new(k, enc, hashlib.sha256).digest()
                if not hmac.compare_digest(tag, expected_tag):
                    raise ValueError("Integrity tag mismatch")
                dec = bytes(b ^ k[i % len(k)] for i, b in enumerate(enc))
                return dec.decode("utf-8")

            if _has_crypto:
                combined = base64.urlsafe_b64decode(encrypted_b64.encode("utf-8"))
                nonce = combined[:12]
                ciphertext = combined[12:]
                aesgcm = AESGCM(key)
                plaintext_bytes = aesgcm.decrypt(nonce, ciphertext, None)
                return plaintext_bytes.decode("utf-8")
            else:
                raise RuntimeError("Cryptography library required to decrypt AES-GCM data")
        except Exception as e:
            logger.error(f"Decryption fault: {e}")
            raise ValueError(f"Decryption failed: {e}")

    # -------------------------------------------------------------------------
    # 3. SECURE RANDOM GENERATORS & HASHER HELPERS
    # -------------------------------------------------------------------------
    def generate_token(self, length: int = 32) -> str:
        """Generates a cryptographically secure URL-safe random token."""
        return secrets.token_urlsafe(length)

    def generate_numeric_code(self, digits: int = 6) -> str:
        """Generates a cryptographically secure random numeric code (e.g. 6 digits)."""
        lower = 10 ** (digits - 1)
        upper = (10 ** digits) - 1
        return str(secrets.randbelow(upper - lower + 1) + lower)

    def hash_sha256(self, text: str) -> str:
        """Returns standard SHA-256 hex digest."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def hmac_sha256(self, key_str: str, message: str) -> str:
        """Returns HMAC-SHA256 hex digest for message authentication."""
        return hmac.new(key_str.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()

crypto_engine = CryptoEngine()
