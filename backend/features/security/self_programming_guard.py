import os
import ast
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from .models import User, Role, Permission, RiskLevel, SecurityEventSeverity
from .config import security_config
from .rbac import rbac_engine
from .database import security_db

logger = logging.getLogger("orian.security.self_programming_guard")

DANGEROUS_AST_CALLS = ["eval", "exec", "__import__", "compile"]

class SelfProgrammingGuard:
    """Security Guard for Self-Programming & Code Modifications enforcing OWNER role verification, protected file boundaries, and AST static security analysis."""

    def __init__(self):
        self.config = security_config
        self.db = security_db

    def is_protected_file(self, file_path: str) -> bool:
        """Checks if a target file falls within the protected security and core governance paths."""
        norm = os.path.normpath(file_path).lower().replace("\\", "/")
        for protected in self.config.PROTECTED_DIRECTORIES:
            p_clean = protected.lower().replace("\\", "/")
            if p_clean in norm or norm.endswith(p_clean):
                return True
        return False

    def validate_code_safety(self, code_str: str) -> Tuple[bool, Optional[str]]:
        """Performs AST static analysis to ensure self-generated code does not contain unconstrained execution vulnerabilities."""
        try:
            tree = ast.parse(code_str)
        except Exception as e:
            return False, f"AST Syntax Parsing Error: {e}"

        for node in ast.walk(tree):
            # Check for direct calls to eval, exec, __import__
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in DANGEROUS_AST_CALLS:
                    return False, f"Static analysis violation: Prohibited dynamic execution call '{node.func.id}()' detected."
                
                # Check for os.system or subprocess.Popen with dangerous patterns
                if isinstance(node.func, ast.Attribute):
                    if node.func.attr in ["system", "popen"] and isinstance(node.func.value, ast.Name) and node.func.value.id in ["os", "subprocess"]:
                        return False, f"Static analysis violation: Unsafe direct shell invocation '{node.func.value.id}.{node.func.attr}()' detected."

        return True, None

    def validate_modification_request(
        self,
        user: User,
        target_files: List[str],
        patch_code: Optional[str] = None
    ):
        """Authorizes code modification requests against permissions, roles, protected directories, and static code safety."""
        if not self.config.SELF_PROGRAMMING_ENABLED:
            raise PermissionError("Self-programming subsystem is currently disabled in security configuration.")

        # Enforce permission and role
        rbac_engine.enforce_permission(user, Permission.SELF_PROGRAM, "Self-Programming Code Modification")

        if self.config.SELF_PROGRAMMING_REQUIRES_OWNER and user.role != Role.OWNER:
            raise PermissionError("Self-programming requires OWNER administrative role.")

        # Check protected files
        for f in target_files:
            if self.is_protected_file(f):
                from .audit_logger import audit_logger
                audit_logger.log_security_event(
                    event_type="PROTECTED_FILE_MODIFICATION_BLOCKED",
                    severity=SecurityEventSeverity.CRITICAL,
                    user_id=user.id,
                    message=f"Blocked attempt to modify protected security subsystem file: '{f}'"
                )
                raise PermissionError(f"File '{f}' is a protected security component and cannot be modified by autonomous self-programming.")

        # Validate code AST if patch provided
        if patch_code:
            safe, err = self.validate_code_safety(patch_code)
            if not safe:
                from .audit_logger import audit_logger
                audit_logger.log_security_event(
                    event_type="UNSAFE_CODE_PATCH_REJECTED",
                    severity=SecurityEventSeverity.HIGH,
                    user_id=user.id,
                    message=f"Self-programming patch rejected: {err}"
                )
                raise ValueError(f"Self-programming patch failed security static analysis: {err}")

    def record_change(
        self,
        change_id: str,
        user_id: str,
        component: str,
        change_type: str,
        patch_content: str,
        snapshot_id: str,
        reason: str,
        tests_passed: bool = True,
        health_score: float = 100.0
    ):
        """Records an approved code change in SQLite audit table."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute("""
        INSERT INTO sec_code_changes (
            change_id, user_id, component, change_type, patch_content,
            snapshot_id, status, reason, tests_passed, health_score,
            created_at, applied_at, rolled_back_at
        ) VALUES (?, ?, ?, ?, ?, ?, 'APPLIED', ?, ?, ?, ?, ?, NULL)
        """, (
            change_id, user_id, component, change_type, patch_content,
            snapshot_id, reason, 1 if tests_passed else 0, health_score, now, now
        ))
        conn.commit()
        conn.close()

    def record_rollback(self, change_id: str, reason: str):
        """Updates code change status to ROLLED_BACK upon health check or test failure."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        now = time.time()
        cursor.execute("""
        UPDATE sec_code_changes
        SET status = 'ROLLED_BACK', reason = reason || ' | Rollback: ' || ?, rolled_back_at = ?
        WHERE change_id = ?
        """, (reason, now, change_id))
        conn.commit()
        conn.close()

self_programming_guard = SelfProgrammingGuard()
