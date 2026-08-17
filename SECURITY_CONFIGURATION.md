# Orian AI — Centralized Security Configuration Guide

## 1. Security Configuration Parameters (`SecurityConfig`)

All security parameters are centralized in [`features.security.config.SecurityConfig`](file:///f:/major%20project/orionAI/backend/features/security/config.py):

| Setting | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `AUTH_ENABLED` | bool | `true` | Enables/disables global authentication requirement. |
| `MFA_ENABLED` | bool | `true` | Enables TOTP multi-factor authentication support. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `60` | JWT Access Token lifetime in minutes. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | `30` | JWT Refresh Token lifetime in days. |
| `MAX_FAILED_LOGIN_ATTEMPTS` | int | `5` | Maximum failed attempts before temporary lockout. |
| `LOCKOUT_DURATION_SECONDS` | int | `300` | Account lockout period (5 minutes). |
| `RATE_LIMIT_GLOBAL_PER_MINUTE` | int | `120` | Maximum API requests per IP per minute. |
| `RATE_LIMIT_AUTH_PER_MINUTE` | int | `10` | Maximum login/registration attempts per minute. |
| `REQUIRE_CONFIRMATION_FOR_HIGH_RISK` | bool | `true` | Requires explicit confirmation ticket for high-risk operations. |
| `REQUIRE_MFA_FOR_CRITICAL_RISK` | bool | `true` | Requires step-up TOTP verification for critical-risk operations. |
| `IOT_REQUIRE_AUTHENTICATION` | bool | `true` | Rejects unauthenticated/unpaired ESP32 devices. |
| `IOT_REPLAY_WINDOW_SECONDS` | int | `60` | Replay protection TTL window for hardware commands. |
| `SELF_PROGRAMMING_ENABLED` | bool | `true` | Enables controlled self-programming and self-repair. |
| `SELF_PROGRAMMING_REQUIRES_OWNER`| bool | `true` | Restricts self-programming strictly to OWNER role. |
| `AUDIT_LOGGING_ENABLED` | bool | `true` | Records all operations in `sec_audit_logs`. |

---

## 2. Setting Environment Variables
To override configuration defaults in production, create a `.env` file (based on `.env.example`):
```bash
ORIAN_SECRET_KEY=e6f8b1c4...
ORIAN_ENCRYPTION_KEY=a7d2c9e1...
AUTH_ENABLED=true
MFA_ENABLED=true
REQUIRE_CONFIRMATION_FOR_HIGH_RISK=true
```
