import os
import sys
import time
import ctypes
import threading
import logging
from typing import Dict, Any, Optional, Callable
from .laptop_service import laptop_protection_service

logger = logging.getLogger("orian.protection.activity_monitor")

class OrianActivityMonitor:
    """Privacy-Preserving Activity Monitor detecting foreground process activity and duration without keystroke or content surveillance."""

    def __init__(self, device_id: str = "laptop-main-001", sample_interval: float = 2.0):
        self.device_id = device_id
        self.sample_interval = sample_interval
        self.is_running = False
        self.current_process = ""
        self.current_app = ""
        self.current_start_time = time.time()
        self._thread: Optional[threading.Thread] = None
        self.service = laptop_protection_service

    def start_monitoring(self):
        """Starts background non-intrusive sampling thread."""
        if self.is_running:
            return
        self.is_running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        logger.info(f"OrianActivityMonitor started for device '{self.device_id}' (interval: {self.sample_interval}s)")

    def stop_monitoring(self):
        """Stops the sampling thread."""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=2.0)
        logger.info("OrianActivityMonitor stopped.")

    def _get_active_window_process_windows(self) -> Tuple[str, str]:
        """Native Windows API to retrieve active foreground window process name and title."""
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "unknown", "unknown"

            # Get Window Title
            length = user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

            # Get Process PID
            pid = ctypes.c_ulong()
            user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))

            # Query Process Name via psutil if available or toolhelp/kernel32
            try:
                import psutil
                p = psutil.Process(pid.value)
                return p.name().lower(), title
            except Exception:
                # Fallback simple title extraction
                return "active_app", title

        except Exception as e:
            return "unknown", ""

    def _monitor_loop(self):
        """Main sampling loop."""
        while self.is_running:
            try:
                if os.name == "nt":
                    proc_name, title = self._get_active_window_process_windows()
                else:
                    proc_name, title = "test_process", "Test Window"

                now = time.time()
                if proc_name != self.current_process:
                    # Application switched - reset duration
                    self.current_process = proc_name
                    self.current_app = proc_name
                    self.current_start_time = now
                    duration = 0.0
                else:
                    duration = now - self.current_start_time

                # Ingest sample into protection service
                if proc_name and proc_name != "unknown":
                    self.service.process_activity_report(
                        device_id=self.device_id,
                        application=self.current_app,
                        process_name=self.current_process,
                        duration_seconds=duration,
                        window_title=title
                    )

            except Exception as e:
                logger.debug(f"Activity monitor sampling loop warning: {e}")

            time.sleep(self.sample_interval)

orian_activity_monitor = OrianActivityMonitor()
