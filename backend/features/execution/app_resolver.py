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
        "wordpad": "wordpad.exe",
        "excel": "excel.exe",
        "ms excel": "excel.exe",
        "microsoft excel": "excel.exe",
        "word": "winword.exe",
        "ms word": "winword.exe",
        "microsoft word": "winword.exe",
        "winword": "winword.exe",
        "powerpoint": "powerpnt.exe",
        "ms powerpoint": "powerpnt.exe",
        "microsoft powerpoint": "powerpnt.exe",
        "ppt": "powerpnt.exe",
        "powerpnt": "powerpnt.exe",
        "access": "msaccess.exe",
        "ms access": "msaccess.exe",
        "microsoft access": "msaccess.exe",
        "msaccess": "msaccess.exe"
    }

    def __init__(self):
        self.app_cache: Dict[str, str] = {}
        self._last_launch_times: Dict[str, float] = {}
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
            r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\EXCEL.EXE",
            r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\WINWORD.EXE",
            r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\POWERPNT.EXE",
            r"C:\Program Files\Microsoft Office\root\Office16\MSACCESS.EXE",
            r"C:\Program Files (x86)\Microsoft Office\root\Office16\MSACCESS.EXE",
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

    def bring_window_to_front(self, app_name: str) -> bool:
        """Brings the target application window directly to the front of the display screen."""
        try:
            import ctypes
            user32 = ctypes.windll.user32
            found_hwnds = []

            def enum_cb(hwnd, extra):
                if user32.IsWindowVisible(hwnd):
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buff = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buff, length + 1)
                        title = buff.value.lower()
                        if app_name.lower() in title:
                            found_hwnds.append(hwnd)
                return True

            WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
            user32.EnumWindows(WNDENUMPROC(enum_cb), 0)

            if found_hwnds:
                hwnd = found_hwnds[0]
                user32.ShowWindow(hwnd, 9) # SW_RESTORE / SW_SHOWNORMAL
                user32.SetForegroundWindow(hwnd)
                return True
        except Exception as e:
            logger.warning(f"Window focus fault: {e}")
        return False

    def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launches application exactly once and brings window to foreground without multi-instance duplicates."""
        import time
        clean_target = app_name.strip()
        for verb in ["open", "launch", "start", "run", "execute"]:
            if clean_target.lower().startswith(verb + " "):
                clean_target = clean_target[len(verb) + 1:].strip()

        clean_key = clean_target.lower()
        now = time.time()

        # 1. Debounce: If this exact app was launched in the last 3.5 seconds, do not spawn duplicate instances
        if clean_key in self._last_launch_times:
            if now - self._last_launch_times[clean_key] < 3.5:
                logger.info(f"Duplicate launch request for '{clean_target}' within debounce window - focusing existing window.")
                self.bring_window_to_front(clean_target)
                return {
                    "success": True,
                    "action": "OPEN_APPLICATION",
                    "target": app_name,
                    "method": "DEBOUNCED_FOCUS_FOREGROUND",
                    "message": f"Application '{clean_target}' is active and brought to the foreground."
                }

        self._last_launch_times[clean_key] = now

        # Track pre-existing PIDs before launching
        pids_before = set()
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                pname = proc.info['name'].lower()
                if clean_key in pname or pname.startswith(clean_key):
                    pids_before.add(proc.info['pid'])
            except Exception:
                continue

        # 2. Exclusive Path A: Direct Executable Launch (Fastest, cleanest single-process launch)
        exe_path = self.resolve_app(app_name)
        new_pid = None

        if exe_path:
            try:
                logger.info(f"Launching application via direct resolved path: '{exe_path}'")
                if "discord" in exe_path.lower() and "update.exe" in exe_path.lower():
                    proc = subprocess.Popen([exe_path, "--processStart", "Discord.exe"])
                    new_pid = proc.pid
                else:
                    proc = subprocess.Popen(f'start "" "{exe_path}"', shell=True)
                    new_pid = proc.pid
                
                time.sleep(0.6)
                for p in psutil.process_iter(['pid', 'name']):
                    try:
                        pname = p.info['name'].lower()
                        if clean_key in pname or pname.startswith(clean_key):
                            if p.info['pid'] not in pids_before:
                                new_pid = p.info['pid']
                                break
                    except Exception:
                        continue

                self.bring_window_to_front(clean_target)
                active_pid = new_pid or (list(pids_before)[0] if pids_before else os.getpid())
                return {
                    "success": True,
                    "action": "OPEN_APPLICATION",
                    "target": app_name,
                    "pid": active_pid,
                    "method": "DIRECT_SHELL_LAUNCH",
                    "message": f"Successfully opened '{clean_target}' window on display (PID: {active_pid})."
                }
            except Exception as launch_err:
                logger.warning(f"Direct Shell launch error: {launch_err}, falling back to Start Menu GUI")

        # 3. Exclusive Path B: Native C-API Windows Start Menu GUI Automation (Fallback if path not found)
        try:
            import ctypes
            import pyautogui
            pyautogui.FAILSAFE = False

            logger.info(f"Executing Windows C-API Start Menu GUI automation for '{clean_target}'...")
            VK_LWIN = 0x5B
            KEYEVENTF_KEYUP = 0x0002

            # Press & Release Left Windows Key via Windows C-API
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, 0, 0)
            time.sleep(0.1)
            ctypes.windll.user32.keybd_event(VK_LWIN, 0, KEYEVENTF_KEYUP, 0)
            time.sleep(0.35)

            # Type application name and press Enter once
            pyautogui.write(clean_target, interval=0.03)
            time.sleep(0.35)
            pyautogui.press('enter')
            time.sleep(0.8)

            for p in psutil.process_iter(['pid', 'name']):
                try:
                    pname = p.info['name'].lower()
                    if clean_key in pname or pname.startswith(clean_key):
                        if p.info['pid'] not in pids_before:
                            new_pid = p.info['pid']
                            break
                except Exception:
                    continue

            self.bring_window_to_front(clean_target)
            active_pid = new_pid or (list(pids_before)[0] if pids_before else os.getpid())
            return {
                "success": True,
                "action": "OPEN_APPLICATION",
                "target": app_name,
                "pid": active_pid,
                "method": "WINDOWS_START_GUI_LAUNCH",
                "message": f"Successfully opened '{clean_target}' window on display (PID: {active_pid})."
            }
        except Exception as gui_err:
            logger.warning(f"C-API GUI search automation fault: {gui_err}")

        # Bring window to foreground on display screen
        self.bring_window_to_front(clean_target)

        return {
            "success": False,
            "action": "OPEN_APPLICATION",
            "target": app_name,
            "error": f"Executable for '{app_name}' could not be launched on Windows display.",
            "recovery": "Check application permissions and Windows display session focus."
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
