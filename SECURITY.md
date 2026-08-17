# Orian AI — Security Architecture & Policy

## 1. Overview
Orian AI is designed as a secure personal AI operating system based on defense-in-depth security principles. Every sensitive action passes through the centralized `OrianSecurityGateway`, enforcing authentication, role-based authorization, operational risk assessment, cryptographic verification, and tamper-resistant audit logging.

```
                         ORIAN AI
                            │
                            ▼
                  ┌───────────────────┐
                  │ SECURITY GATEWAY  │
                  └─────────┬─────────┘
                            │
          ┌─────────────────┼─────────────────┐
          ▼                 ▼                 ▼
   Authentication     Authorization      Risk Engine
   (Argon2id/MFA)       (RBAC/ACL)       (Risk Levels)
          │                 │                 │
          └─────────────────┼─────────────────┘
                            ▼
                    Command Validator
                            │
                            ▼
                      Intent Engine
                            │
                            ▼
                       Tool Router
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
     Desktop             IoT Tool           Code Tool
     (Apps)               (ESP32)           (Sandbox)
        │                   │                   │
        ▼                   ▼                   ▼
     Windows            MQTT / TLS          Git Snapshot
                            │                   │
                            └─────────┬─────────┘
                                      ▼
                                 Verification
                                      │
                                      ▼
                                Audit Logger
                                      │
                                      ▼
                               SQLite Database
```

---

## 2. Core Security Guarantees
1. **Never Trust the LLM as a Security Authority**: The LLM suggests tools and understands natural language intent. The `OrianSecurityGateway` alone determines whether execution is permitted.
2. **Deny by Default**: Any unclassified tool, unknown device, missing permission, or expired token is unconditionally denied.
3. **Argon2id Password Hashing**: Passwords are never stored in plaintext or reversible formats; hashes are salted with 16 random bytes and hashed using Argon2id (with PBKDF2-HMAC-SHA256 fallback).
4. **AES-256-GCM AEAD Encryption**: Stored credentials, TOTP secrets, and sensitive tokens are encrypted using authenticated 256-bit AES-GCM.
5. **Replay-Protected IoT**: ESP32 hardware commands use nonces, timestamps, TTL expiry windows, and HMAC-SHA256 signatures.
6. **Sandboxed Self-Programming**: Autonomous codebase modifications require mandatory Git checkpoints, AST static security analysis, automated test suite execution, and automatic rollback on degradation.
7. **Tamper-Resistant Audit Logging**: All sensitive operations are recorded in SQLite `sec_audit_logs` and `sec_security_events` with credentials and keys automatically sanitized.

---

## 3. Vulnerability Reporting
If you discover a security vulnerability in Orian AI, please report it privately to the repository maintainer. Do not open public issues for unpatched security vulnerabilities.
