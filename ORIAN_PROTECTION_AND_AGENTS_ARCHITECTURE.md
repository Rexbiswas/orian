# ORIAN AI: Secure Windows Laptop Protection & Autonomous Agents Architecture

**Document Version:** 1.0.0  
**Classification:** Enterprise Technical Architecture & Engineering Brief  
**Author:** Orian AI Engineering & DeepMind Antigravity Systems  
**Date:** August 18, 2026  

---

## Executive Summary

This document provides a comprehensive technical architecture overview of the **Orian AI Secure Windows Laptop Protection Subsystem**, the **Autonomous Agent Ecosystem**, and a structured record of engineering developments implemented today.

Orian AI incorporates an enterprise-grade, deterministic policy engine, privacy-preserving activity monitor, cryptographic command gateway, and a dedicated Windows client agent. The architecture strictly enforces the principle of least privilege, eliminates unauthorized shell command execution, prevents arbitrary code injection, and protects system integrity via cryptographic nonces and time-to-live (TTL) validation.

```
                                  ┌────────────────────────────────┐
                                  │      ORIAN DIGITAL BRAIN       │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │     ORIAN SECURITY GATEWAY     │
                                  └───────────────┬────────────────┘
                                                  │
                   ┌──────────────────────────────┴──────────────────────────────┐
                   │                                                             │
                   ▼                                                             ▼
    ┌─────────────────────────────┐                               ┌─────────────────────────────┐
    │  PRIVACY-PRESERVING MONITOR │                               │    FOCUS MODE & POLICIES    │
    └──────────────┬──────────────┘                               └──────────────┬──────────────┘
                   │                                                             │
                   └──────────────────────────────┬──────────────────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │  DETERMINISTIC POLICY ENGINE   │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │ PROTECTION RISK & ESCALATION   │
                                  └───────────────┬────────────────┘
                                                  │
                                  ┌───────────────┴───────────────┐
                                  │                               │
                                  ▼                               ▼
                      ┌───────────────────────┐       ┌───────────────────────┐
                      │    WARN / 10s GRACE   │       │   IMMEDIATE BLOCK     │
                      └───────────┬───────────┘       └───────────┬───────────┘
                                  │                               │
                      ┌───────────┴───────────┐                   │
                      │                       │                   │
                      ▼                       ▼                   │
             [OWNER OVERRIDE?]       [ACTIVITY STOPPED?]          │
               /            \         /                \          │
             YES             NO      YES                NO        │
              │               │       │                  │        │
              ▼               └───────┼──────────────────┘        │
         [CANCELLED]                  │                           │
                                      └─────────────┬─────────────┘
                                                    │
                                                    ▼
                                  ┌────────────────────────────────┐
                                  │    LAPTOP COMMAND GATEWAY      │
                                  │  (HMAC-SHA256 + 15s Replay)   │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │      WINDOWS LAPTOP AGENT      │
                                  │ (Strict Permitted Operations)  │
                                  └───────────────┬────────────────┘
                                                  │
                                                  ▼
                                  ┌────────────────────────────────┐
                                  │       CONTROLLED WIN32 API     │
                                  │  (PowrProf.SetSuspendState)    │
                                  └────────────────────────────────┘
```

---

## 1. Secure Laptop Protection Subsystem

### 1.1 Privacy-Preserving Activity Monitor
* **Module:** `backend/features/protection/activity_monitor.py`
* **Zero-Surveillance Standard:**
  * Collects only active foreground window metadata (`process_name`, `application`, sanitized `window_title`, `focus_duration`).
  * **Strictly Prohibited & Excluded:** No keylogging, no keystroke interceptors, no credential scraping, no webcam/audio recording, no screen capture, no clipboard reading.
* **Sampling Architecture:** Non-blocking 2.0-second polling using native Win32 API calls (`GetForegroundWindow`, `GetWindowThreadProcessId`).

### 1.2 Deterministic Policy Engine
* **Module:** `backend/features/protection/policy_engine.py`
* **Evaluation Pipeline:**
  1. **Master Toggle Verification:** Validates if system protection and auto-sleep are globally active.
  2. **Security Signal Analysis:** High-confidence detections for malware, system tampering, and unauthorized data access.
  3. **Whitelist Evaluation (Highest Precedence):** `ALWAYS_ALLOWED` developer tools and `AUTHORIZED_SECURITY_LAB` environments bypass restrictions.
  4. **Blacklist Enforcement:** Explicit blacklisted applications and domains are blocked.
  5. **Focus Mode Context:** Evaluates time window restrictions and category limits.
  6. **Duration Damping & Escalation:** Applies threshold filters to eliminate false positives on brief process transitions.

### 1.3 Whitelist & Security Lab Exemption Framework
* **Module:** `backend/features/protection/whitelist.py`
* **Always Allowed Developer Tools:**
  * `code.exe` (VS Code), `python.exe`, `pythonw.exe`, `git.exe`, `node.exe`, `studio64.exe` (Android Studio), `notepad.exe`, `docker.exe`.
* **Authorized Security Lab Exemption:**
  * Network destinations (`localhost`, `127.0.0.1`, `::1`, `10.0.0.0/8`, `192.168.0.0/16`, `testlab.local`) are exempt from hacking/malware blocking to support cybersecurity education and security research.

### 1.4 Protection Risk Engine & Escalation Matrix
* **Module:** `backend/features/protection/risk_engine.py`
* **Duration Damping:**
  * `< 30 seconds`: Process switches are ignored (transient navigation).
  * `30 – 120 seconds`: Activity is logged for telemetry without enforcement.
  * `> 120 seconds`: Full policy rules and enforcement triggers apply.
* **Violation Escalation Ladder:**
  * **1st Incident:** `WARN` (10-second grace period).
  * **2nd Incident:** `WARN` (10-second grace period with elevated warning).
  * **3rd Incident:** `BLOCK` (Task termination).
  * **4th Incident:** `SLEEP` (Cryptographically authorized system suspension).

### 1.5 Warning System, Grace Period & Owner Override
* **Module:** `backend/features/protection/laptop_service.py`
* **Grace Period Countdown:** 10-second timer dispatched on policy violation.
* **Cancellation Triggers:**
  * User switches away or terminates offending process during countdown -> Violation automatically marked `CANCELLED`.
  * Owner submits authenticated override -> Violation marked `OVERRIDDEN`.
* **Step-Up Authentication:** Overriding `HIGH` or `CRITICAL` violations requires Argon2id password verification or RFC 6238 TOTP MFA validation.

### 1.6 Cryptographic Command Gateway & Replay Protection
* **Module:** `backend/features/protection/command_gateway.py`
* **Security Validation Matrix:**
  * **Nonce Uniqueness:** UUIDv4 `request_id` checked against SQLite execution history to eliminate replay attacks.
  * **Clock Skew Threshold:** Strict 15-second timestamp drift limit (`|now - timestamp| <= 15.0s`).
  * **Time-to-Live (TTL):** Commands expire after 15 seconds.
  * **HMAC-SHA256 Signature:** Computed over `request_id:device_id:command:policy_id:timestamp:expires_at` using device shared secret.
  * **Revocation Check:** Revoked devices are permanently blocked from generating or executing commands.

---

## 2. Windows Laptop Agent

### 2.1 Standalone Agent Architecture
* **Module:** `backend/laptop_agent/agent.py`
* **Permitted Operations:**
  * `GET_STATUS`: Returns agent health, version, uptime, and active foreground window.
  * `NOTIFY`: Dispatches system desktop notification.
  * `LOCK`: Calls `user32.dll` `LockWorkStation()`.
  * `SLEEP`: Calls `PowrProf.dll` `SetSuspendState(0, 1, 0)`.
* **Prohibited Operations (Strictly Blocked):**
  * `EXECUTE_COMMAND`, `RUN_SHELL`, `RUN_POWERSHELL`, `EXECUTE_ARBITRARY_PROGRAM`, `DELETE_FILE`, `DOWNLOAD_FILE`.

### 2.2 Device Pairing & Lifecycle State Machine
* **Module:** `backend/features/protection/device_manager.py`
* **Lifecycle States:**
  1. `UNREGISTERED`: Device has no credentials.
  2. `PAIRING`: Device initiates handshake (`/api/laptop/register`), receiving a 6-digit pairing code and shared secret.
  3. `OWNER APPROVAL`: Pending administrator/owner confirmation (`/api/laptop/approve`).
  4. `ACTIVE`: Fully authenticated and authorized for cryptographic command execution.
  5. `REVOKED`: Permanently decommissioned; all commands immediately rejected.

---

## 3. Autonomous Agents Ecosystem

```
                                  ┌────────────────────────────────┐
                                  │      ORIAN DIGITAL BRAIN       │
                                  └───────────────┬────────────────┘
                                                  │
                 ┌────────────────────────────────┼────────────────────────────────┐
                 │                                │                                │
                 ▼                                ▼                                ▼
   ┌───────────────────────────┐    ┌───────────────────────────┐    ┌───────────────────────────┐
   │     SECURITY GATEWAY      │    │    TASK ORCHESTRATOR      │    │     IOT & HARDWARE        │
   │  • RBAC & Rate Limiting   │    │  • Multi-Step Reasoning   │    │  • ESP32 Hardware Link    │
   │  • MFA & Confirmation     │    │  • Real-Time Automations  │    │  • Telemetry Ingestion    │
   │  • Audit Logging          │    │  • SQLite Job Scheduling  │    │  • Safety Gate Controls   │
   └───────────────────────────┘    └───────────────────────────┘    └───────────────────────────┘
```

1. **Security Gateway Agent (`backend/features/security/gateway.py`):**
   * Serves as the authoritative barrier for all system tools and API endpoints.
   * Enforces role-based access control (`OWNER`, `ADMIN`, `USER`, `GUEST`).
   * Evaluates operational risk for dangerous actions and enforces interactive confirmation gates.
2. **Self-Programming Guard Agent (`backend/features/security/self_programming_guard.py`):**
   * Protects the codebase against unauthorized autonomous modifications.
   * `PROTECTED_DIRECTORIES` prevents self-programming agents from altering security configurations, protection modules, or the laptop agent.
3. **IoT & Hardware Agent (`backend/features/iot/`):**
   * Manages communication with ESP32 controllers, ambient sensors, and smart switches.
   * Enforces safety gates before toggling high-voltage hardware appliances.
4. **Task Orchestrator Agent (`backend/features/tasks/`):**
   * Coordinates background task queues, memory timelines, and persistent cron schedules.

---

## 4. Engineering Accomplishments Completed Today

### 4.1 Backend Architecture Implementation
* Implemented the entire **Protection Subsystem** across 11 modular files:
  * Pydantic schemas & enums (`models.py`)
  * SQLite persistence layer with 9 dedicated tables (`database.py`)
  * Activity whitelist & security lab subnets (`whitelist.py`)
  * Focus Mode scheduler (`focus_manager.py`)
  * Risk evaluation & duration damping (`risk_engine.py`)
  * Deterministic policy pipeline (`policy_engine.py`)
  * Device pairing & revocation (`device_manager.py`)
  * Cryptographic HMAC command gateway (`command_gateway.py`)
  * Master protection service with grace period timers (`laptop_service.py`)
  * Privacy-preserving Win32 sampler (`activity_monitor.py`)
  * Package export interface (`__init__.py`)

### 4.2 Windows Laptop Agent & API Integration
* Built standalone client in `backend/laptop_agent/`:
  * Win32 `PowrProf` and `user32` API bindings (`windows_api.py`)
  * Device configuration and credential persistence (`config.py`)
  * 10-point cryptographic security verification process (`agent.py`)
* Registered 19 REST and WebSocket endpoints in `backend/main.py`:
  * `/api/laptop/*` (register, approve, heartbeat, status, revoke, command, command/ack)
  * `/api/protection/*` (policies, activity, rules, override, dashboard, emergency-disable)
  * `/api/focus/*` (status, start, stop)
  * `/ws/protection` (real-time telemetry and alerts)

### 4.3 Security Hardening & Self-Programming Safeguards
* Updated `backend/features/security/config.py` to add `backend/features/protection` and `backend/laptop_agent` to `PROTECTED_DIRECTORIES`.
* Prevented autonomous agents from modifying protection policy files or security gateway code.

### 4.4 Automated Testing & Quality Assurance
* Developed 3 comprehensive test suites:
  * `backend/tests/test_laptop_protection.py` (11 unit & integration tests)
  * `backend/tests/test_protection_security.py` (11 security & attack vector tests)
  * `backend/tests/test_laptop_api.py` (FastAPI REST integration tests)
* **Test Results:** **60 / 60 tests passed with 100% success rate**.

---

## 5. REST & WebSocket API Specification

| HTTP Method | Endpoint | Description | Authorization |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/laptop/register` | Initiates device pairing handshake | None (Initial Setup) |
| `POST` | `/api/laptop/approve` | Administrator approves pending device | `Bearer Token` (Admin/Owner) |
| `POST` | `/api/laptop/heartbeat` | Agent telemetry and keepalive receiver | None |
| `GET` | `/api/laptop/status` | Queries device identity and agent health | None |
| `POST` | `/api/laptop/revoke` | Revokes privileged device access | `Bearer Token` (Admin/Owner) |
| `POST` | `/api/laptop/command` | Dispatches signed command to laptop | `Bearer Token` (Owner) |
| `POST` | `/api/laptop/command/ack` | Ingests execution result from agent | None |
| `POST` | `/api/protection/activity` | Ingests activity report for evaluation | None |
| `GET` | `/api/protection/policies` | Lists active productivity/security policies | None |
| `POST` | `/api/protection/policies` | Updates or creates a protection policy | `Bearer Token` (Admin/Owner) |
| `POST` | `/api/protection/override` | Submits owner override for violation | `Bearer Token` (Admin/Owner) |
| `GET` | `/api/protection/rules` | Queries whitelist and blacklist rules | None |
| `POST` | `/api/protection/rules` | Adds whitelist or blacklist rule | `Bearer Token` (Admin/Owner) |
| `DELETE` | `/api/protection/rules/{id}` | Deletes whitelist or blacklist rule | `Bearer Token` (Admin/Owner) |
| `GET` | `/api/protection/dashboard` | Queries daily metrics and focus state | None |
| `POST` | `/api/protection/emergency-disable` | Emergency killswitch for protection/sleep | `Bearer Token` (Owner) |
| `GET` | `/api/focus/status` | Queries active focus mode and schedules | None |
| `POST` | `/api/focus/start` | Initiates active focus session | `Bearer Token` (Admin/Owner) |
| `POST` | `/api/focus/stop` | Terminates active focus session | `Bearer Token` (Admin/Owner) |
| `WS` | `/ws/protection` | Real-time WebSocket stream for telemetry | None |

---

## 6. Operational Quickstart

### 6.1 Starting the Orian Backend
```powershell
cd "f:\major project\orionAI\backend"
python main.py
```

### 6.2 Starting the Laptop Protection Agent
```powershell
cd "f:\major project\orionAI\backend"
python -m laptop_agent.agent
```

### 6.3 Registering and Approving a Device (PowerShell)
```powershell
# 1. Device Handshake
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/laptop/register" -Method Post -ContentType "application/json" -Body '{"device_id": "laptop-main-001", "device_name": "Primary Workstation"}'

# 2. Administrator Authentication
$auth = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/auth/login" -Method Post -ContentType "application/json" -Body '{"username": "orian_admin", "password": "OrianSecureMasterKey2026!"}'

# 3. Device Approval
Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/laptop/approve" -Method Post -Headers @{Authorization="Bearer $($auth.access_token)"} -ContentType "application/json" -Body '{"device_id": "laptop-main-001", "approved": true}'
```

---

*Orian AI Architecture Document — Internal Engineering Reference.*
