import time
import datetime
import logging
from typing import Optional, List, Dict, Any
from .models import FocusMode, FocusSession
from .database import protection_db

logger = logging.getLogger("orian.protection.focus_manager")

DAY_MAP = {
    0: "mon",
    1: "tue",
    2: "wed",
    3: "thu",
    4: "fri",
    5: "sat",
    6: "sun"
}

class FocusModeManager:
    """Enterprise Focus Mode Engine orchestrating active schedules (WORK, STUDY, CUSTOM) and session policies."""

    def __init__(self):
        self.db = protection_db
        self.active_session: Optional[FocusSession] = self.db.get_active_focus_session()

    def reload(self):
        self.active_session = self.db.get_active_focus_session()

    def get_status(self) -> Dict[str, Any]:
        self.reload()
        session = self.active_session
        if not session or not session.is_active or session.mode == FocusMode.OFF:
            return {
                "active": False,
                "mode": FocusMode.OFF.value,
                "schedule_active": False,
                "schedule": "None",
                "session_id": None
            }

        is_scheduled = self.is_schedule_active_now(session)
        return {
            "active": session.is_active,
            "mode": session.mode.value,
            "schedule_active": is_scheduled,
            "schedule_start": session.schedule_start,
            "schedule_end": session.schedule_end,
            "schedule_days": session.schedule_days,
            "session_id": session.session_id,
            "start_time": session.start_time
        }

    def is_schedule_active_now(self, session: Optional[FocusSession] = None) -> bool:
        """Determines if the current local system time is within the configured schedule window."""
        s = session or self.active_session
        if not s or not s.is_active or s.mode == FocusMode.OFF:
            return False

        now = datetime.datetime.now()
        current_day_str = DAY_MAP.get(now.weekday(), "").lower()

        # Check Day of week
        if s.schedule_days and current_day_str not in [d.lower() for d in s.schedule_days]:
            return False

        # Check Time Range (HH:MM)
        try:
            start_parts = [int(p) for p in s.schedule_start.split(":")]
            end_parts = [int(p) for p in s.schedule_end.split(":")]

            current_minutes = now.hour * 60 + now.minute
            start_minutes = start_parts[0] * 60 + start_parts[1]
            end_minutes = end_parts[0] * 60 + end_parts[1]

            if start_minutes <= end_minutes:
                return start_minutes <= current_minutes <= end_minutes
            else:
                # Overnight schedule (e.g. 22:00 to 06:00)
                return current_minutes >= start_minutes or current_minutes <= end_minutes
        except Exception as e:
            logger.warning(f"Error parsing focus schedule times: {e}")
            return True

    def is_focus_active_now(self) -> bool:
        """Returns True if Focus Mode is currently active and within schedule window."""
        self.reload()
        if not self.active_session or not self.active_session.is_active:
            return False
        if self.active_session.mode == FocusMode.OFF:
            return False
        return self.is_schedule_active_now(self.active_session)

    def start_focus(self, mode: FocusMode = FocusMode.WORK, schedule_start: str = "09:00", schedule_end: str = "18:00", schedule_days: Optional[List[str]] = None, user_id: str = "system") -> FocusSession:
        days = schedule_days or ["mon", "tue", "wed", "thu", "fri"]
        new_session = FocusSession(
            session_id=f"focus_{int(time.time()*1000)}",
            mode=mode,
            is_active=True,
            start_time=time.time(),
            schedule_start=schedule_start,
            schedule_end=schedule_end,
            schedule_days=days,
            created_by=user_id
        )
        self.db.set_focus_session(new_session)
        self.active_session = new_session
        logger.info(f"Started focus session '{new_session.session_id}' in mode {mode.value} ({schedule_start}-{schedule_end})")
        return new_session

    def stop_focus(self, user_id: str = "system") -> bool:
        off_session = FocusSession(
            session_id=f"focus_off_{int(time.time()*1000)}",
            mode=FocusMode.OFF,
            is_active=False,
            start_time=time.time(),
            end_time=time.time(),
            created_by=user_id
        )
        self.db.set_focus_session(off_session)
        self.active_session = off_session
        logger.info("Focus mode deactivated (OFF).")
        return True

focus_manager = FocusModeManager()
