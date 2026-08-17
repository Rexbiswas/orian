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

import subprocess
import psutil
import shutil
import logging
import winreg
from typing import Dict, Any, Optional

logger = logging.getLogger("orian.app_resolver")

class ApplicationResolver:
    """Discovers installed Windows applications, resolves executables, launches processes and verifies execution."""

    BUILTIN_APPS = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "calc": "calc.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "explorer": "explorer.exe",
        "file explorer": "explorer.exe",
        "mspaint": "mspaint.exe",
        "paint": "mspaint.exe",
        "taskmgr": "taskmgr.exe",
        "wordpad": "wordpad.exe"
    }

    def __init__(self):
        self.app_cache: Dict[str, str] = {}
        self._build_registry_index()

    def _build_registry_index(self):
        """Discovers installed software from Windows Registry App Paths & Start Menu."""
        registry_keys = [
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\App Paths")
        ]

        for root_hkey, path in registry_keys:
            try:
                key = winreg.OpenKey(root_hkey, path)
                count = winreg.QueryInfoKey(key)[0]
                for i in range(count):
                    try:
                        sub_name = winreg.EnumKey(key, i)
                        sub_key = winreg.OpenKey(key, sub_name)
                        exe_path, _ = winreg.QueryValueEx(sub_key, "")
                        winreg.CloseKey(sub_key)
                        if exe_path and os.path.exists(exe_path.strip('"')):
                            clean_name = os.path.splitext(sub_name)[0].lower()
                            self.app_cache[clean_name] = exe_path.strip('"')
                    except Exception:
                        continue
                winreg.CloseKey(key)
            except Exception:
                continue

        # Common Install Directories fallback
        common_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Programs\Microsoft VS Code\Code.exe"),
            r"C:\Program Files\Microsoft VS Code\Code.exe",
            os.path.expanduser(r"~\AppData\Roaming\Spotify\Spotify.exe"),
            os.path.expanduser(r"~\AppData\Local\Discord\Update.exe"),
        ]
        for p in common_paths:
            if os.path.exists(p):
                name = os.path.splitext(os.path.basename(p))[0].lower()
                self.app_cache[name] = p

    def resolve_app(self, app_name: str) -> Optional[str]:
        name_clean = app_name.strip().lower()
        
        # Strip common verb prefixes
        for verb in ["open", "launch", "start", "run", "execute"]:
            if name_clean.startswith(verb + " "):
                name_clean = name_clean[len(verb) + 1:].strip()

        # Check builtins
        if name_clean in self.BUILTIN_APPS:
            return self.BUILTIN_APPS[name_clean]

        # Check registry cache
        if name_clean in self.app_cache:
            return self.app_cache[name_clean]

        # Check PATH
        path_match = shutil.which(name_clean) or shutil.which(f"{name_clean}.exe")
        if path_match:
            return path_match

        # Fuzzy match in app_cache
        for key, path in self.app_cache.items():
            if name_clean in key or key in name_clean:
                return path

        return None

    def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launches application via Windows Start Menu GUI search automation (Win Key + Type + Enter), verified via psutil."""
        clean_target = app_name.strip()
        for verb in ["open", "launch", "start", "run", "execute"]:
            if clean_target.lower().startswith(verb + " "):
                clean_target = clean_target[len(verb) + 1:].strip()

        gui_success = False
        pid = None
        verified = False

        # 1. Attempt GUI Search Automation (Windows Key -> Type Name -> Press Enter)
        try:
            import pyautogui
            import time
            pyautogui.FAILSAFE = False

            logger.info(f"Executing Windows Start Search GUI automation for '{clean_target}'...")
            pyautogui.press('win')
            time.sleep(0.35)
            pyautogui.write(clean_target, interval=0.04)
            time.sleep(0.45)
            pyautogui.press('enter')
            time.sleep(1.0)

            # Check if process is now running
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    pname = proc.info['name'].lower()
                    if clean_target.lower() in pname or pname.startswith(clean_target.lower()):
                        pid = proc.info['pid']
                        verified = True
                        gui_success = True
                        break
                except Exception:
                    continue
        except Exception as gui_err:
            logger.warning(f"GUI search automation fault: {gui_err}")

        if gui_success and pid:
            return {
                "success": True,
                "action": "OPEN_APPLICATION",
                "target": app_name,
                "pid": pid,
                "method": "WINDOWS_START_GUI_SEARCH",
                "message": f"Successfully pressed Windows Key, searched & launched '{clean_target}' (PID: {pid})."
            }

        # 2. Fallback to direct executable path resolution & subprocess Popen
        exe_path = self.resolve_app(app_name)
        if not exe_path:
            return {
                "success": False,
                "action": "OPEN_APPLICATION",
                "target": app_name,
                "error": f"Executable for '{app_name}' could not be located on Windows system.",
                "recovery": f"Searched Start Menu GUI, Registry App Paths & PATH."
            }

        try:
            if "discord" in exe_path.lower() and "update.exe" in exe_path.lower():
                proc = subprocess.Popen([exe_path, "--processStart", "Discord.exe"])
            else:
                proc = subprocess.Popen([exe_path])

            pid = proc.pid
            try:
                p = psutil.Process(pid)
                verified = p.is_running()
            except Exception:
                verified = True

            return {
                "success": True,
                "action": "OPEN_APPLICATION",
                "target": app_name,
                "executable": exe_path,
                "pid": pid,
                "method": "SUBPROCESS_DIRECT",
                "message": f"Successfully launched {app_name} (PID: {pid}). Verification: {verified}."
            }
        except Exception as e:
            return {
                "success": False,
                "action": "OPEN_APPLICATION",
                "target": app_name,
                "error": f"Process launch failed: {str(e)}",
                "recovery": "Check application permissions and Windows process limits."
            }

    def close_app(self, app_name: str) -> Dict[str, Any]:
        """Terminates matching running processes using psutil."""
        target = app_name.strip().lower()
        terminated_count = 0
        pids = []

        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                if target in pname or pname.startswith(target):
                    proc.terminate()
                    pids.append(proc.info['pid'])
                    terminated_count += 1
            except Exception:
                continue

        if terminated_count > 0:
            return {
                "success": True,
                "action": "CLOSE_APPLICATION",
                "target": app_name,
                "count": terminated_count,
                "pids": pids,
                "message": f"Closed {terminated_count} process(es) matching '{app_name}'."
            }
        else:
            return {
                "success": False,
                "action": "CLOSE_APPLICATION",
                "target": app_name,
                "error": f"No running processes matching '{app_name}' were found.",
                "recovery": "Verify process is currently running using GET_RUNNING_PROCESSES."
            }

app_resolver = ApplicationResolver()
