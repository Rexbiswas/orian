import sys
import os
import time
import uuid
import json
import logging
import threading
from typing import Dict, List, Any, Optional

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.iot.database import iot_db
from features.iot.mqtt_manager import mqtt_manager

logger = logging.getLogger("orian.iot.scheduler")

class IoTScheduler:
    """Persistent SQLite-backed task scheduler for delayed and periodic IoT automation."""

    def __init__(self):
        self._running = True
        self._thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self._thread.start()

    def schedule_command(
        self,
        device_id: str,
        command: str,
        delay_seconds: float = 0,
        specific_timestamp: Optional[float] = None,
        recurrence: str = "once",
        payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Schedules an IoT device action at a future timestamp."""
        sched_id = str(uuid.uuid4())
        target_time = specific_timestamp if specific_timestamp else (time.time() + max(0, delay_seconds))
        now = time.time()

        iot_db.execute("""
            INSERT INTO iot_schedules (id, device_id, command, payload_json, scheduled_time, recurrence, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'ACTIVE', ?)
        """, (sched_id, device_id, command, json.dumps(payload or {}), target_time, recurrence, now))

        time_str = time.strftime('%H:%M:%S', time.localtime(target_time))
        logger.info(f"Scheduled IoT Task [{sched_id}]: {command} on {device_id} at {time_str}")

        return {
            "schedule_id": sched_id,
            "device_id": device_id,
            "command": command,
            "scheduled_time": target_time,
            "formatted_time": time_str,
            "delay_seconds": round(max(0, target_time - now), 1)
        }

    def cancel_schedule(self, schedule_id: str) -> bool:
        """Cancels a scheduled task."""
        rowcount = iot_db.execute("UPDATE iot_schedules SET status = 'CANCELED' WHERE id = ?", (schedule_id,))
        return rowcount > 0

    def list_schedules(self, status: str = "ACTIVE") -> List[Dict[str, Any]]:
        """Lists schedules filtered by status."""
        rows = iot_db.fetch_all("SELECT * FROM iot_schedules WHERE status = ? ORDER BY scheduled_time ASC", (status,))
        return [dict(r) for r in rows]

    def _scheduler_loop(self):
        """Continuous background execution loop checking for due schedules."""
        while self._running:
            try:
                now = time.time()
                due_tasks = iot_db.fetch_all("""
                    SELECT * FROM iot_schedules
                    WHERE status = 'ACTIVE' AND scheduled_time <= ?
                """, (now,))

                for task in due_tasks:
                    sched_id = task["id"]
                    dev_id = task["device_id"]
                    cmd = task["command"]
                    payload = json.loads(task["payload_json"] or "{}")

                    logger.info(f"Executing Due IoT Scheduled Task: {cmd} on {dev_id}...")
                    res = mqtt_manager.send_command(dev_id, cmd, payload=payload)

                    if task["recurrence"] == "daily":
                        next_time = task["scheduled_time"] + 86400.0
                        iot_db.execute("UPDATE iot_schedules SET scheduled_time = ? WHERE id = ?", (next_time, sched_id))
                    else:
                        iot_db.execute("UPDATE iot_schedules SET status = 'COMPLETED' WHERE id = ?", (sched_id,))

            except Exception as e:
                logger.warning(f"IoT scheduler loop fault: {e}")

            time.sleep(1.0)

iot_scheduler = IoTScheduler()
