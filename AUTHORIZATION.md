# Orian AI — Role-Based Access Control (RBAC) & Permission Matrix

## 1. Role Hierarchy

| Role | Level | Description |
| :--- | :--- | :--- |
| **OWNER** | 100 | Unrestricted system control, security governance, self-programming, and account management. |
| **ADMIN** | 80 | System configuration, diagnostics, user management, and high-level tool execution. |
| **TRUSTED_USER** | 60 | Interactive desktop tool control, IoT hardware dispatch, and file operations. |
| **USER** | 40 | Standard conversational LLM querying, basic calculations, and IoT telemetry read. |
| **GUEST** | 20 | Restricted read-only conversation and safe mathematical evaluation. |
| **DEVICE** | 10 | Machine-to-machine IoT communication. |

---

## 2. Granular Permission Matrix

| Permission | GUEST | USER | TRUSTED_USER | ADMIN | OWNER |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `chat` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `calculator` | ✓ | ✓ | ✓ | ✓ | ✓ |
| `read_memory` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `write_memory` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `open_application` | ✗ | ✗ | ✓ | ✓ | ✓ |
| `read_file` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `write_file` | ✗ | ✗ | ✓ | ✓ | ✓ |
| `delete_file` | ✗ | ✗ | ✗ | ✓ | ✓ |
| `execute_command`| ✗ | ✗ | ✗ | ✗ | ✓ |
| `iot_read` | ✗ | ✓ | ✓ | ✓ | ✓ |
| `iot_control` | ✗ | ✗ | ✓ | ✓ | ✓ |
| `system_control` | ✗ | ✗ | ✗ | ✓ | ✓ |
| `code_read` | ✗ | ✗ | ✗ | ✓ | ✓ |
| `code_modify` | ✗ | ✗ | ✗ | ✗ | ✓ |
| `self_diagnose` | ✗ | ✗ | ✓ | ✓ | ✓ |
| `self_program` | ✗ | ✗ | ✗ | ✗ | ✓ |
| `security_admin` | ✗ | ✗ | ✗ | ✗ | ✓ |
| `user_admin` | ✗ | ✗ | ✗ | ✓ | ✓ |

---

## 3. Dynamic Risk Engine & Confirmation Gates
Operations are assigned risk grades:
- **LOW**: No confirmation required.
- **MEDIUM**: Standard desktop & hardware control.
- **HIGH**: Irreversible file deletions, cleanup, or high-power appliances — requires explicit ephemeral confirmation ticket (`/api/security/confirm`).
- **CRITICAL**: Security modifications, administrative changes — requires OWNER confirmation and step-up MFA.
