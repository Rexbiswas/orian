# Orian AI — Controlled Self-Programming & Sandboxing Security

## 1. Core Principle
Orian AI never executes arbitrary, unvetted self-generated code in production. Autonomous codebase modifications must undergo strict multi-stage security validation.

```
USER / LLM
    │
    ▼
Problem Analysis & Security Review
    │
    ▼
Protected Files Check (Rejects security/auth/db changes)
    │
    ▼
Mandatory Git Checkpoint Creation (`git stash create`)
    │
    ▼
AST Syntax & Static Analysis (Blocks eval, exec, dangerous calls)
    │
    ▼
Isolated Sandboxed Execution
    │
    ▼
Automated Test Suite Validation (`unittest discover`)
    │
    ▼
Human Owner Confirmation (for High/Critical modifications)
    │
    ▼
Apply Patch
    │
    ▼
Post-Patch Health & Integrity Check
    │
    ├── SUCCESS ──► Keep Patch & Log in `sec_code_changes`
    │
    └── FAILURE ──► Automatic Rollback (`git checkout -- .`)
```

---

## 2. Protected Files Policy
The self-programming engine cannot autonomously rewrite:
- `backend/features/security/` (Security Gateway, Auth Engine, Crypto, RBAC)
- `.env` (Environment variables and secrets)
- `.git/` (Version control metadata)
- `orian_storage/orian_core.db` (Core system database)

Any attempt to modify these files is immediately blocked and logged as a `PROTECTED_FILE_MODIFICATION_BLOCKED` security event.

---

## 3. AST Static Code Analysis
Before writing or executing any patch, the AST parser inspects the syntax tree to ensure:
- No calls to `eval()`, `exec()`, `__import__()`, or `compile()`.
- No raw string concatenations in `os.system()` or `subprocess.Popen()`.
- Valid Python syntax with 100% parse accuracy.
