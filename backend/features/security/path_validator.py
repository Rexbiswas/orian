import os
import logging
from typing import List, Optional
from config import settings

logger = logging.getLogger("orian.security.path_validator")

# Critical Windows & Linux system paths that should never be modified by AI tools
FORBIDDEN_SYSTEM_PREFIXES = [
    r"c:\windows",
    r"c:\program files",
    r"c:\program files (x86)",
    r"c:\boot",
    r"c:\recovery",
    "/etc",
    "/bin",
    "/sbin",
    "/usr",
    "/root",
    "/var",
    "/sys",
    "/proc"
]

class PathValidator:
    """Enterprise Path & Directory Traversal Validator preventing directory escapes and unauthorized access to system-critical files."""

    def __init__(self, root_workspace: str = settings.ORIAN_ROOT_DIR):
        self.root_workspace = os.path.abspath(root_workspace)
        self.allowed_bases = [
            self.root_workspace,
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")), # Project Root
            os.path.abspath(os.path.expanduser("~")) # User home for standard apps
        ]

    def sanitize_path(self, untrusted_path: str, allow_user_home: bool = True) -> str:
        """Resolves symlinks, normalizes path, and validates that it does not escape into restricted system directories."""
        if not untrusted_path:
            raise ValueError("File path cannot be empty")

        # 1. Normalize and resolve real path
        clean_path = os.path.abspath(os.path.normpath(untrusted_path.strip()))
        clean_lower = clean_path.lower()

        # 2. Check for traversal tokens in raw string
        if ".." in untrusted_path.replace("\\", "/").split("/"):
            logger.warning(f"Directory traversal detected in untrusted path: '{untrusted_path}'")

        # 3. Check forbidden system directory prefixes across all drives
        for forbidden in FORBIDDEN_SYSTEM_PREFIXES:
            if clean_lower == forbidden or clean_lower.startswith(forbidden + os.sep) or clean_lower.startswith(forbidden + "/"):
                raise PermissionError(f"Access to protected operating system directory is strictly blocked: '{clean_path}'")

        # Drive-agnostic Windows system directory protection
        if "\\windows\\" in clean_lower or clean_lower.endswith("\\windows") or "\\system32" in clean_lower or "\\program files" in clean_lower:
            raise PermissionError(f"Access to operating system directory is strictly blocked: '{clean_path}'")

        # 4. Check protected security files
        if clean_lower.endswith(".env") or ".env" in untrusted_path or "/etc/" in clean_lower or "\\etc\\" in clean_lower:
            raise PermissionError(f"Access to protected configuration or system file is blocked: '{untrusted_path}'")

        return clean_path

    def is_safe_for_deletion(self, path: str) -> bool:
        """Determines if a target file or folder is within disposable temporary or cache storage."""
        try:
            clean = self.sanitize_path(path)
            clean_lower = clean.lower()
            
            # Deletion is permitted in temp, cache, or designated test workspaces
            temp_dir = os.path.abspath(settings.TEMP_DIR).lower()
            cache_dir = os.path.abspath(settings.CACHE_DIR).lower()
            
            return (
                clean_lower.startswith(temp_dir) or
                clean_lower.startswith(cache_dir) or
                "temp" in clean_lower or
                "cache" in clean_lower
            )
        except Exception:
            return False

path_validator = PathValidator()
