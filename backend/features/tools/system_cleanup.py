import sys
import os

for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

import tempfile
import shutil
import logging
from typing import Dict, Any

logger = logging.getLogger("orian.system_cleanup")

class SystemCleanupEngine:
    """Detects, scans, and safely cleans Windows temporary files, browser caches, and log artifacts."""

    TEMP_DIRECTORIES = [
        tempfile.gettempdir(),
        r"C:\Windows\Temp",
        os.path.expanduser(r"~\AppData\Local\Temp"),
        os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\INetCache"),
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Cache")
    ]

    def clear_temp_files(self) -> Dict[str, Any]:
        files_scanned = 0
        files_removed = 0
        files_skipped = 0
        bytes_recovered = 0

        target_dirs = [d for d in self.TEMP_DIRECTORIES if os.path.exists(d)]

        for target_dir in target_dirs:
            for root, dirs, files in os.walk(target_dir):
                for f in files:
                    files_scanned += 1
                    file_path = os.path.join(root, f)
                    
                    # Avoid system-critical files
                    if any(critical in file_path.lower() for critical in ["system32", "boot", "ntuser"]):
                        files_skipped += 1
                        continue

                    try:
                        size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_removed += 1
                        bytes_recovered += size
                    except Exception:
                        files_skipped += 1
                        continue

        mb_recovered = round(bytes_recovered / (1024 * 1024), 2)
        gb_recovered = round(bytes_recovered / (1024 * 1024 * 1024), 2)
        space_str = f"{gb_recovered} GB" if gb_recovered >= 1.0 else f"{mb_recovered} MB"

        summary_msg = (
            f"Temporary File Cleanup Complete\n"
            f"Files scanned: {files_scanned:,}\n"
            f"Files removed: {files_removed:,}\n"
            f"Skipped/in use: {files_skipped:,}\n"
            f"Space recovered: {space_str}"
        )

        return {
            "success": True,
            "action": "CLEAR_TEMP_FILES",
            "files_scanned": files_scanned,
            "files_removed": files_removed,
            "files_skipped": files_skipped,
            "bytes_recovered": bytes_recovered,
            "space_recovered": space_str,
            "message": summary_msg
        }

system_cleanup = SystemCleanupEngine()
