# Orian AI — Threat Model & Security Controls

| Threat | Impact | Likelihood | Mitigation | Detection | Recovery |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Unauthorized API Access** | Data leakage, tool abuse | Medium | Bearer JWT with HMAC/Argon2id authentication, rate limits. | 401/403 logs in `sec_security_events`. | Invalidate JWT, revoke active session. |
| **Credential Stuffing / Brute-Force** | Account takeover | High | 5-attempt threshold triggers 5-minute lockout backoff. | `AUTH_LOGIN_FAILED` and `AUTH_ACCOUNT_LOCKED` events. | Wait for lockout expiry, owner password reset. |
| **Prompt Injection / Jailbreak** | Tool misuse | High | LLM is NOT the security authority. All actions must pass `OrianSecurityGateway`. | Gateway audit trail and parameter validation. | Reject unconfirmed/unauthorized action. |
| **Path Traversal (`../`)** | Arbitrary file read/write | Medium | `PathValidator` resolves symlinks and blocks access outside workspace. | `PERMISSION_DENIED` log on traversal attempts. | Operation rejected before disk access. |
| **Command Injection** | Remote code execution | High | Argument arrays without shell invocation, allowlists. | `ToolPolicyEngine` parameter sanitization. | Deny raw string execution. |
| **SSRF (Server-Side Request Forgery)** | Internal network probing | Medium | `SSRFValidator` blocks loopback (`127.0.0.1`) and cloud metadata (`169.254.169.254`). | `SSRFValidator` exception logged in audit. | Request blocked before socket connection. |
| **IoT Command Replay** | Unauthorized hardware trigger | Medium | HMAC signatures, unique nonces, 60s TTL timestamp window. | Invalid signature / expired timestamp warning. | Drop duplicate packet. |
| **Rogue / Spoofed ESP32** | Bogus telemetry data | Low | Unique per-device token in `sec_iot_credentials`. | `IOT_UNAUTHORIZED_DEVICE` security event. | Drop unauthenticated telemetry. |
| **Self-Programming Corruption** | System breakdown | Medium | Mandatory Git snapshot, AST static safety analysis, automated tests. | Test failure or health check score < 100%. | Automatic Git rollback (`git checkout -- .`). |
| **Database Tampering** | Privilege escalation | Low | Parameterized SQL queries, file permissions on `orian_core.db`. | SQLite syntax verification and integrity checks. | Restore from backup/snapshot. |
