# Orian AI — Authentication & Session Management

## 1. Authentication Architecture
Orian AI implements multi-tier identity verification:
1. **Password Hashing**: Argon2id (`time_cost=3, memory_cost=65536, parallelism=4, hash_len=32, salt_len=16`).
2. **Brute-Force & Credential Stuffing Protection**: Failed logins increment a counter; reaching 5 consecutive failures triggers an automatic 5-minute lockout backoff (`sec_users.locked_until`).
3. **Session Tokens**: JWT Bearer Access Tokens (60-minute expiry) with Refresh Tokens (30-day expiry).
4. **Session Tracking**: Active sessions are persisted in SQLite `sec_sessions` with IP address, user-agent, creation, and idle timestamps.

---

## 2. Multi-Factor Authentication (MFA / TOTP)
- Standard RFC 6238 Time-based One-Time Passwords (TOTP).
- Setup generates a 32-character base32 secret and provisioning URI (`otpauth://totp/Orian%20AI%20Enterprise:...`).
- TOTP secrets are encrypted in the database using AES-256-GCM AEAD (`sec_users.mfa_secret_encrypted`).
- Supports step-up MFA challenge for `CRITICAL` risk operations.

---

## 3. Endpoints

| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user | No (or Admin) |
| `POST` | `/api/auth/login` | Authenticate with username, password, & optional TOTP | No |
| `POST` | `/api/auth/logout` | Revoke the active session | Bearer Token |
| `GET` | `/api/auth/me` | Fetch authenticated profile and permissions | Bearer Token |
| `POST` | `/api/auth/mfa/setup` | Generate TOTP secret and QR provisioning URI | Bearer Token |
| `POST` | `/api/auth/mfa/verify` | Verify token and activate MFA | Bearer Token |
| `POST` | `/api/auth/mfa/disable` | Verify token and disable MFA | Bearer Token |

---

## 4. Bootstrap Default Owner
On initial installation, if no users exist in `sec_users`, Orian AI boots an initial `OWNER` account (`orian_admin` / `OrianSecureMasterKey2026!`). The owner should immediately change this password and enroll in TOTP MFA.
