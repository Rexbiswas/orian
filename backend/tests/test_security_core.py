import sys
import os
import unittest
import time

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, ".."))
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.security.crypto import crypto_engine
from features.security.auth_engine import auth_engine
from features.security.mfa_engine import mfa_engine
from features.security.models import Role, User
import pyotp

class TestSecurityCore(unittest.TestCase):

    def test_01_argon2id_password_hashing(self):
        """Tests that Argon2id creates unique salted hashes and verifies accurately."""
        password = "MasterKeySecure2026!#"
        hash1 = crypto_engine.hash_password(password)
        hash2 = crypto_engine.hash_password(password)

        # Hashes must be unique due to random salting
        self.assertNotEqual(hash1, hash2)
        self.assertTrue(crypto_engine.verify_password(password, hash1))
        self.assertTrue(crypto_engine.verify_password(password, hash2))
        self.assertFalse(crypto_engine.verify_password("WrongPassword!", hash1))

    def test_02_aes_gcm_aead_encryption(self):
        """Tests AES-256-GCM AEAD encryption, decryption, and integrity verification."""
        secret_payload = "confidential_api_token_value_987654321"
        encrypted = crypto_engine.encrypt_data(secret_payload)
        
        self.assertNotEqual(secret_payload, encrypted)
        decrypted = crypto_engine.decrypt_data(encrypted)
        self.assertEqual(secret_payload, decrypted)

        # Tampered ciphertext must fail decryption
        tampered = encrypted[:-4] + "AAAA"
        with self.assertRaises(ValueError):
            crypto_engine.decrypt_data(tampered)

    def test_03_totp_mfa_flow(self):
        """Tests TOTP secret generation, QR provisioning, and token validation."""
        test_user = auth_engine.register_user(
            username=f"mfa_user_{int(time.time()*1000)}",
            password="SecurePassword2026!"
        )

        setup_res = mfa_engine.generate_mfa_setup(test_user.id, test_user.username)
        self.assertTrue(len(setup_res.secret) >= 16)
        self.assertTrue(setup_res.provisioning_uri.startswith("otpauth://totp/"))

        # Generate valid TOTP token
        totp = pyotp.TOTP(setup_res.secret)
        current_code = totp.now()

        # Enable MFA
        enabled = mfa_engine.enable_mfa(test_user.id, current_code)
        self.assertTrue(enabled)

        # Verify active user TOTP
        self.assertTrue(mfa_engine.verify_user_totp(test_user.id, current_code))
        self.assertFalse(mfa_engine.verify_user_totp(test_user.id, "000000"))

    def test_04_auth_login_and_lockout_backoff(self):
        """Tests authentication flow and automatic lockout protection after 5 failed attempts."""
        uname = f"lockout_user_{int(time.time()*1000)}"
        pwd = "ValidPassword123!"
        user = auth_engine.register_user(username=uname, password=pwd)

        # 1. Successful authentication
        token_res = auth_engine.authenticate_user(uname, pwd)
        self.assertTrue(len(token_res.access_token) > 20)
        self.assertEqual(token_res.username, uname)

        # 2. Validate session token
        u, s = auth_engine.validate_token(token_res.access_token)
        self.assertEqual(u.id, user.id)
        self.assertTrue(s.is_active)

        # 3. Simulate 5 failed login attempts
        for i in range(5):
            try:
                auth_engine.authenticate_user(uname, "BadPassword!")
            except (ValueError, PermissionError):
                pass

        # 6th attempt must be rejected with account lockout PermissionError
        with self.assertRaises(PermissionError):
            auth_engine.authenticate_user(uname, pwd)

if __name__ == "__main__":
    unittest.main()
