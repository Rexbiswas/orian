import logging
from typing import List, Set, Dict
from .models import Role, Permission, User, SecurityEventSeverity
from .database import security_db

logger = logging.getLogger("orian.security.rbac")

ROLE_HIERARCHY = {
    Role.OWNER: 100,
    Role.ADMIN: 80,
    Role.TRUSTED_USER: 60,
    Role.USER: 40,
    Role.GUEST: 20,
    Role.DEVICE: 10,
}

class RBACEngine:
    """Enterprise Role-Based Access Control (RBAC) Engine enforcing granular permissions and role hierarchy."""

    def __init__(self):
        self.db = security_db
        self._permission_cache: Dict[str, Set[str]] = {}
        self._load_matrix()

    def _load_matrix(self):
        """Loads permissions per role from SQLite into memory for sub-millisecond lookup."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT role_name, permission_name FROM sec_role_permissions")
        rows = cursor.fetchall()
        conn.close()

        cache: Dict[str, Set[str]] = {}
        for r in rows:
            role = r["role_name"]
            perm = r["permission_name"]
            if role not in cache:
                cache[role] = set()
            cache[role].add(perm)

        self._permission_cache = cache

    def reload(self):
        self._load_matrix()

    def has_permission(self, role: Role, permission: Permission) -> bool:
        """Checks if a role possesses the specified permission."""
        role_str = role.value if isinstance(role, Role) else str(role)
        perm_str = permission.value if isinstance(permission, Permission) else str(permission)

        # OWNER always has full permissions
        if role_str == Role.OWNER.value:
            return True

        role_perms = self._permission_cache.get(role_str, set())
        return perm_str in role_perms

    def check_user_permission(self, user: User, permission: Permission) -> bool:
        """Evaluates whether an active user has permission."""
        if not user or not user.is_active:
            return False
        return self.has_permission(user.role, permission)

    def enforce_permission(self, user: User, permission: Permission, action_desc: str = ""):
        """Raises PermissionError if the user lacks the required permission and logs security violation."""
        if not self.check_user_permission(user, permission):
            perm_val = permission.value if isinstance(permission, Permission) else str(permission)
            user_role = user.role.value if isinstance(user.role, Role) else str(user.role)
            from .audit_logger import audit_logger
            audit_logger.log_security_event(
                event_type="PERMISSION_DENIED",
                severity=SecurityEventSeverity.WARNING,
                user_id=user.id,
                message=f"Access denied for user '{user.username}' ({user_role}): Missing required permission '{perm_val}' for action '{action_desc}'"
            )
            raise PermissionError(f"Permission denied: Action requires '{perm_val}' permission. Your role '{user_role}' is not authorized.")

    def is_role_at_least(self, user_role: Role, required_role: Role) -> bool:
        """Checks if user_role level is greater than or equal to required_role level."""
        u_lvl = ROLE_HIERARCHY.get(user_role, 0)
        r_lvl = ROLE_HIERARCHY.get(required_role, 0)
        return u_lvl >= r_lvl

    def get_role_permissions(self, role: Role) -> List[str]:
        """Returns all permissions granted to a role."""
        role_str = role.value if isinstance(role, Role) else str(role)
        if role_str == Role.OWNER.value:
            return [p.value for p in Permission]
        return sorted(list(self._permission_cache.get(role_str, set())))

rbac_engine = RBACEngine()
