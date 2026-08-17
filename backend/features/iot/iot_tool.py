import sys
import os
import re
import time
import json
import logging
from typing import Dict, Any, List, Optional

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

from features.iot.device_manager import device_manager
from features.iot.mqtt_manager import mqtt_manager
from features.iot.scheduler import iot_scheduler
from features.iot.telemetry import iot_telemetry
from features.iot.health_check import iot_health_check

logger = logging.getLogger("orian.iot.tool")

class IoTTool:
    """Central IoT Tool executing structured & natural-language IoT operations, verification, and safety checks."""

    # 1. Atomic Operations
    def turn_on(self, device_identifier: str) -> Dict[str, Any]:
        """Turns on a specified IoT device with execution verification."""
        dev = device_manager.find_device_by_natural_name(device_identifier) or device_manager.get_device(device_identifier)
        if not dev:
            return {
                "success": False,
                "action": "IOT_CONTROL",
                "target": device_identifier,
                "error": f"Could not locate IoT device matching '{device_identifier}'."
            }

        # Safety Check for dangerous appliances
        if dev.get("is_safety_critical") and not dev.get("user_confirmed"):
            return {
                "success": True,
                "action": "IOT_SAFETY_CONFIRMATION_REQUIRED",
                "target": dev["device_name"],
                "message": f"Safety Notice: {dev['device_name']} is a high-power physical appliance. Please confirm: 'Yes, turn on {dev['device_name']}'."
            }

        res = mqtt_manager.send_command(dev["device_id"], "turn_on")
        if res.get("success"):
            return {
                "success": True,
                "action": "IOT_CONTROL",
                "target": dev["device_name"],
                "device_id": dev["device_id"],
                "state": "ON",
                "verified": res.get("verified", True),
                "message": f"{dev['device_name']} is now ON."
            }
        else:
            return {
                "success": False,
                "action": "IOT_CONTROL",
                "target": dev["device_name"],
                "error": res.get("error", f"Failed to turn on {dev['device_name']}."),
                "recovery": "Verify ESP32 power and Wi-Fi connection."
            }

    def turn_off(self, device_identifier: str) -> Dict[str, Any]:
        """Turns off a specified IoT device with execution verification."""
        dev = device_manager.find_device_by_natural_name(device_identifier) or device_manager.get_device(device_identifier)
        if not dev:
            return {
                "success": False,
                "action": "IOT_CONTROL",
                "target": device_identifier,
                "error": f"Could not locate IoT device matching '{device_identifier}'."
            }

        res = mqtt_manager.send_command(dev["device_id"], "turn_off")
        if res.get("success"):
            return {
                "success": True,
                "action": "IOT_CONTROL",
                "target": dev["device_name"],
                "device_id": dev["device_id"],
                "state": "OFF",
                "verified": res.get("verified", True),
                "message": f"{dev['device_name']} is now OFF."
            }
        else:
            return {
                "success": False,
                "action": "IOT_CONTROL",
                "target": dev["device_name"],
                "error": res.get("error", f"Failed to turn off {dev['device_name']}."),
                "recovery": "Check device power and MQTT connection."
            }

    def toggle(self, device_identifier: str) -> Dict[str, Any]:
        """Toggles an IoT device between ON and OFF states."""
        dev = device_manager.find_device_by_natural_name(device_identifier) or device_manager.get_device(device_identifier)
        if not dev:
            return {
                "success": False,
                "action": "IOT_CONTROL",
                "target": device_identifier,
                "error": f"Could not locate IoT device matching '{device_identifier}'."
            }

        target_action = "turn_off" if dev.get("state") == "ON" else "turn_on"
        if target_action == "turn_on":
            return self.turn_on(dev["device_id"])
        else:
            return self.turn_off(dev["device_id"])

    def turn_all(self, state: str = "OFF") -> Dict[str, Any]:
        """Turns all manageable household devices ON or OFF."""
        devices = device_manager.list_all_devices()
        controllable = [d for d in devices if d["device_type"] in ["light", "fan", "relay", "ac", "heater"]]
        results = []

        action_fn = self.turn_on if state.upper() == "ON" else self.turn_off
        for d in controllable:
            res = action_fn(d["device_id"])
            results.append({"name": d["device_name"], "success": res.get("success")})

        count = len(results)
        return {
            "success": True,
            "action": "IOT_BULK_CONTROL",
            "target": f"All Devices ({count})",
            "state": state.upper(),
            "message": f"Successfully turned {state.upper()} all {count} connected IoT devices.",
            "details": results
        }

    # 2. Query & Telemetry Operations
    def get_temperature(self) -> Dict[str, Any]:
        """Returns current temperature reading."""
        climate = iot_telemetry.get_latest_climate()
        temp = climate["temperature"]
        return {
            "success": True,
            "action": "IOT_QUERY",
            "target": "Temperature",
            "value": temp,
            "unit": "°C",
            "message": f"Current room temperature is {temp}°C."
        }

    def get_humidity(self) -> Dict[str, Any]:
        """Returns current humidity reading."""
        climate = iot_telemetry.get_latest_climate()
        hum = climate["humidity"]
        return {
            "success": True,
            "action": "IOT_QUERY",
            "target": "Humidity",
            "value": hum,
            "unit": "%",
            "message": f"Current room humidity is {hum}%."
        }

    def get_device_status(self, device_identifier: Optional[str] = None) -> Dict[str, Any]:
        """Returns status of one or all registered devices."""
        if device_identifier:
            dev = device_manager.find_device_by_natural_name(device_identifier) or device_manager.get_device(device_identifier)
            if dev:
                last_seen_sec = round(time.time() - dev.get("last_seen", 0), 1)
                return {
                    "success": True,
                    "action": "IOT_QUERY",
                    "target": dev["device_name"],
                    "device": dev,
                    "message": f"{dev['device_name']} is {dev.get('status', 'ONLINE')} and currently {dev.get('state', 'OFF')}."
                }
            return {
                "success": False,
                "action": "IOT_QUERY",
                "error": f"Device '{device_identifier}' not found."
            }

        devices = device_manager.list_all_devices()
        online_count = sum(1 for d in devices if d.get("status") == "ONLINE")
        summary_lines = [f"✓ {d['device_name']} — {d.get('status')} ({d.get('state')})" for d in devices]

        return {
            "success": True,
            "action": "IOT_QUERY",
            "devices_total": len(devices),
            "devices_online": online_count,
            "message": f"Connected IoT Devices ({online_count}/{len(devices)} online):\n" + "\n".join(summary_lines),
            "devices": devices
        }

    def discover_devices(self) -> Dict[str, Any]:
        """Scans and lists available IoT devices."""
        return self.get_device_status()

    def run_health_check(self) -> Dict[str, Any]:
        """Runs complete IoT system diagnostic inspection."""
        diag = iot_health_check.run_health_check()
        return {
            "success": True,
            "action": "IOT_HEALTH_CHECK",
            "message": diag.get("formatted", "Health check completed."),
            "details": diag
        }

    # 3. Scheduling Operations
    def schedule_action(self, device_identifier: str, command: str, minutes_delay: float) -> Dict[str, Any]:
        """Schedules a future IoT command."""
        dev = device_manager.find_device_by_natural_name(device_identifier) or device_manager.get_device(device_identifier)
        if not dev:
            return {
                "success": False,
                "error": f"Could not locate device '{device_identifier}' for scheduling."
            }

        delay_seconds = minutes_delay * 60.0
        sched = iot_scheduler.schedule_command(dev["device_id"], command, delay_seconds=delay_seconds)
        return {
            "success": True,
            "action": "IOT_SCHEDULE",
            "target": dev["device_name"],
            "message": f"Scheduled {dev['device_name']} to {command.replace('_', ' ')} in {minutes_delay:g} minute(s) (at {sched['formatted_time']}).",
            "schedule": sched
        }

    # 4. Natural Language Execution Engine
    def execute_natural_command(self, user_prompt: str) -> Dict[str, Any]:
        """Parses natural language prompt and executes corresponding IoT operation with verification."""
        p = user_prompt.lower().strip()

        # 1. Health Check
        if any(k in p for k in ["check my iot", "iot health", "iot system", "is esp32 online", "is my esp32 online"]):
            return self.run_health_check()

        # 2. Discovery / List Devices
        if any(k in p for k in ["show my iot", "find my iot", "list devices", "what devices", "find my esp32", "discover device"]):
            return self.discover_devices()

        # 3. Climate Queries
        if "temperature" in p or "how hot" in p or "how cold" in p:
            return self.get_temperature()
        if "humidity" in p:
            return self.get_humidity()

        # 4. Bulk All Off / All On
        if ("turn off all" in p or "turn everything off" in p or "switch off everything" in p or "all lights off" in p):
            return self.turn_all("OFF")
        if ("turn on all" in p or "turn everything on" in p or "switch on everything" in p or "all lights on" in p):
            return self.turn_all("ON")

        # 5. Delayed Scheduling (e.g. "turn on light in 10 minutes", "turn off fan after 5 minutes")
        sched_match = re.search(r'(?:in|after|for)\s+(\d+)\s+(?:min|minute|minutes)', p)
        if sched_match:
            mins = float(sched_match.group(1))
            cmd = "turn_on" if any(k in p for k in ["turn on", "switch on", "start"]) else "turn_off"
            dev = device_manager.find_device_by_natural_name(p)
            dev_id = dev["device_id"] if dev else "room_light"
            return self.schedule_action(dev_id, cmd, minutes_delay=mins)

        # 6. Specific Device Control
        if any(k in p for k in ["turn on", "switch on", "enable", "start"]):
            dev = device_manager.find_device_by_natural_name(p)
            if dev:
                return self.turn_on(dev["device_id"])
            return self.turn_on("room_light")

        elif any(k in p for k in ["turn off", "switch off", "disable", "stop", "kill"]):
            dev = device_manager.find_device_by_natural_name(p)
            if dev:
                return self.turn_off(dev["device_id"])
            return self.turn_off("room_light")

        elif any(k in p for k in ["toggle", "flip"]):
            dev = device_manager.find_device_by_natural_name(p)
            if dev:
                return self.toggle(dev["device_id"])
            return self.toggle("room_light")

        elif any(k in p for k in ["status of", "is the", "is my"]):
            dev = device_manager.find_device_by_natural_name(p)
            if dev:
                return self.get_device_status(dev["device_id"])
            return self.get_device_status()

        # Fallback default: discover devices
        return self.discover_devices()

iot_tool = IoTTool()
