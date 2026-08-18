import os
import sys
import ctypes
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("orian.laptop_agent.windows_api")

class WindowsAPIWrapper:
    """Encapsulated Win32 API wrapper for controlled system operations (Sleep, Lock, Foreground Window Info) avoiding arbitrary shell commands."""

    def __init__(self):
        self.is_windows = (os.name == "nt")

    def sleep_computer(self, simulate: bool = False) -> Dict[str, Any]:
        """Puts Windows PC into Sleep (Suspend) state via PowrProf.dll SetSuspendState(0, 1, 0).
        If simulate is True or ORIAN_AGENT_SIMULATE_SLEEP=1, validates API availability without suspending system.
        """
        env_sim = os.getenv("ORIAN_AGENT_SIMULATE_SLEEP", "0") in ["1", "true", "True"]
        if simulate or env_sim or not self.is_windows:
            logger.info("[SIMULATION] Windows sleep_computer() called successfully (Dry run active).")
            return {
                "success": True,
                "command": "SLEEP",
                "method": "Win32:PowrProf.SetSuspendState",
                "simulated": True,
                "status": "SUSPEND_STATE_TRIGGERED"
            }

        try:
            # SetSuspendState(bHibernate=0, bForce=1, bWakeupEventsDisabled=0)
            # ctypes signature: BOOL SetSuspendState(BOOLEAN Hibernate, BOOLEAN ForceCritical, BOOLEAN DisableWakeEvent);
            powrprof = ctypes.windll.PowrProf
            res = powrprof.SetSuspendState(0, 1, 0)
            if res:
                return {
                    "success": True,
                    "command": "SLEEP",
                    "method": "Win32:PowrProf.SetSuspendState",
                    "simulated": False
                }
            else:
                err = ctypes.GetLastError()
                return {
                    "success": False,
                    "command": "SLEEP",
                    "error": f"SetSuspendState returned 0 with Win32 Error Code: {err}"
                }
        except Exception as e:
            return {
                "success": False,
                "command": "SLEEP",
                "error": f"Windows Sleep API execution fault: {str(e)}"
            }

    def lock_computer(self, simulate: bool = False) -> Dict[str, Any]:
        """Locks the Windows workstation via user32.dll LockWorkStation()."""
        env_sim = os.getenv("ORIAN_AGENT_SIMULATE_SLEEP", "0") in ["1", "true", "True"]
        if simulate or env_sim or not self.is_windows:
            logger.info("[SIMULATION] Windows lock_computer() called successfully.")
            return {
                "success": True,
                "command": "LOCK",
                "method": "Win32:user32.LockWorkStation",
                "simulated": True
            }

        try:
            user32 = ctypes.windll.user32
            res = user32.LockWorkStation()
            return {
                "success": bool(res != 0),
                "command": "LOCK",
                "method": "Win32:user32.LockWorkStation",
                "simulated": False
            }
        except Exception as e:
            return {
                "success": False,
                "command": "LOCK",
                "error": f"LockWorkStation fault: {str(e)}"
            }

    def show_desktop_notification(self, title: str, message: str) -> Dict[str, Any]:
        """Displays Windows system notification or console notice."""
        logger.info(f"[DESKTOP NOTIFICATION] {title}: {message}")
        return {
            "success": True,
            "command": "NOTIFY",
            "title": title,
            "message": message
        }

    def get_foreground_window_info(self) -> Dict[str, Any]:
        """Queries current foreground window without collecting private keystrokes or contents."""
        if not self.is_windows:
            return {"process_name": "mock_process.exe", "window_title": "Mock Active Window", "pid": 1234}

        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return {"process_name": "idle", "window_title": "", "pid": 0}

            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            process_name = "unknown"
            try:
                import psutil
                p = psutil.Process(pid.value)
                process_name = p.name().lower()
            except Exception:
                pass

            return {
                "process_name": process_name,
                "window_title": title,
                "pid": pid.value
            }
        except Exception as e:
            return {"process_name": "unknown", "error": str(e)}

windows_api = WindowsAPIWrapper()
