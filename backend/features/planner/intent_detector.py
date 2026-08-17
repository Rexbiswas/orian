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

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger("orian.intent_detector")

class IntentCategory:
    DESKTOP_ACTION = "DESKTOP_ACTION"
    SYSTEM_CLEANUP = "SYSTEM_CLEANUP"
    SIMPLE_CALCULATION = "SIMPLE_CALCULATION"
    ADVANCED_MATHEMATICS = "ADVANCED_MATHEMATICS"
    REAL_WORLD_REASONING = "REAL_WORLD_REASONING"
    SELF_DIAGNOSTIC = "SELF_DIAGNOSTIC"
    SELF_PROGRAMMING = "SELF_PROGRAMMING"
    FILE_SYSTEM_ACTION = "FILE_SYSTEM_ACTION"
    IOT_CONTROL = "IOT_CONTROL"
    IOT_QUERY = "IOT_QUERY"
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"

class IntentDetector:
    """Classifies user queries into discrete executable intents for deterministic tool routing."""

    CLEANUP_KEYWORDS = [
        "clear temp", "clean temp", "delete temp", "clear temporary", "clean temporary",
        "delete temporary", "free storage", "reclaim disk", "clean cache", "delete cache", "temp file"
    ]

    DIAGNOSTIC_KEYWORDS = [
        "check yourself", "check your code", "find your errors", "why did you fail",
        "debug yourself", "system health check", "diagnose", "check errors", "why failed"
    ]

    PROGRAMMING_KEYWORDS = [
        "fix yourself", "improve your code", "add a new capability", "fix this problem",
        "self program", "patch yourself", "improve application launcher", "optimize calculation engine",
        "create a new tool", "improve memory system"
    ]

    IOT_CONTROL_KEYWORDS = [
        "turn on", "turn off", "switch on", "switch off", "toggle", "turn everything off",
        "turn off all", "turn on all", "turn everything on", "all lights off", "all lights on",
        "turn on the light", "turn off the light", "turn on the fan", "turn off the fan",
        "turn on my room light", "turn off my room light", "turn on led", "turn off led",
        "toggle the bedroom light", "turn on the light for", "turn off the fan after"
    ]

    IOT_QUERY_KEYWORDS = [
        "room temperature", "what's the temperature", "what is the temperature", "what's the room temperature",
        "what is the room temperature", "is the door open", "is the light on", "is the fan on",
        "show my iot", "find my iot", "find my esp32", "is my esp32 online", "is esp32 online",
        "what devices are currently connected", "what devices are connected", "show my devices",
        "check my iot", "iot health", "iot system", "humidity"
    ]

    MATH_SIMPLE_PATTERN = re.compile(
        r'^\s*(?:what\s+is\s+|calculate\s+|solve\s+)?'
        r'[\d\.\s\+\-\*\/\%\^\(\)\,\{\}\[\]sqrtsincostanlogabs\:\=]+'
        r'(?:\s*[\+\-\*\/\^]\s*[\d\.\s]+)*\s*\??$', re.IGNORECASE
    )

    ADVANCED_MATH_KEYWORDS = [
        "derivative", "integral", "differentiate", "integrate", "matrix", "matrices",
        "solve equation", "quadratic", "eigenvalue", "probability", "differential equation",
        "limit of", "taylor series", "fourier", "laplace", "algebraic", "trigonometry"
    ]

    DESKTOP_APP_KEYWORDS = [
        "open notepad", "open calc", "open calculator", "open chrome", "open vscode", "open vs code",
        "open spotify", "open discord", "open file explorer", "open cmd", "open powershell",
        "open word", "open excel", "open powerpoint", "open access",
        "close notepad", "close calc", "close calculator", "close chrome", "close vscode"
    ]

    FILE_KEYWORDS = [
        "read file", "write file", "delete file", "search file", "find file", "open folder",
        "list directory", "create file"
    ]

    REAL_WORLD_KEYWORDS = [
        "laptop running slow", "electricity use", "device use", "structure project",
        "app crashing", "optimize algorithm", "storage require", "reduce response time"
    ]

    def detect_intent(self, user_prompt: str) -> Tuple[str, float, Dict[str, Any]]:
        p = user_prompt.strip().lower()

        # 1. IoT Hardware Control & Queries (High Priority to prevent desktop app misrouting)
        if any(k in p for k in ["room light", "bedroom light", "bedroom fan", "living room ac", "esp32", "room heater", "led", "fan on", "fan off", "light on", "light off", "climate sensor"]):
            if any(verb in p for verb in ["turn on", "turn off", "switch on", "switch off", "toggle", "start", "stop", "for ", "after ", "in "]):
                return IntentCategory.IOT_CONTROL, 0.98, {"raw_prompt": user_prompt}
            return IntentCategory.IOT_QUERY, 0.95, {"raw_prompt": user_prompt}

        if any(k in p for k in self.IOT_CONTROL_KEYWORDS):
            return IntentCategory.IOT_CONTROL, 0.95, {"raw_prompt": user_prompt}

        if any(k in p for k in self.IOT_QUERY_KEYWORDS):
            return IntentCategory.IOT_QUERY, 0.95, {"raw_prompt": user_prompt}

        # 2. Self-Programming
        if any(k in p for k in self.PROGRAMMING_KEYWORDS):
            return IntentCategory.SELF_PROGRAMMING, 0.95, {"raw_prompt": user_prompt}

        # 3. Self-Diagnostics
        if any(k in p for k in self.DIAGNOSTIC_KEYWORDS):
            return IntentCategory.SELF_DIAGNOSTIC, 0.95, {"raw_prompt": user_prompt}

        # 4. System Cleanup
        if any(k in p for k in self.CLEANUP_KEYWORDS):
            return IntentCategory.SYSTEM_CLEANUP, 0.98, {"raw_prompt": user_prompt}

        # 5. Simple Math Evaluation
        if self._is_simple_math(p):
            expr = self._extract_math_expression(user_prompt)
            return IntentCategory.SIMPLE_CALCULATION, 0.95, {"expression": expr}

        # 6. Advanced Math
        if any(k in p for k in self.ADVANCED_MATH_KEYWORDS):
            return IntentCategory.ADVANCED_MATHEMATICS, 0.90, {"raw_prompt": user_prompt}

        # 7. Desktop Control (OS Applications)
        if any(p.startswith(verb) for verb in ["open ", "launch ", "start ", "close ", "run "]) or \
           any(app in p for app in ["notepad", "calculator", "calc", "chrome", "vscode", "vs code", "spotify", "discord", "excel", "winword", "word", "powerpoint", "access"]):
            return IntentCategory.DESKTOP_ACTION, 0.92, {"raw_prompt": user_prompt}

        # 8. File System Actions
        if any(k in p for k in self.FILE_KEYWORDS):
            return IntentCategory.FILE_SYSTEM_ACTION, 0.88, {"raw_prompt": user_prompt}

        # 9. Real World Problem Solving
        if any(k in p for k in self.REAL_WORLD_KEYWORDS) or "how to" in p or "why is my" in p:
            return IntentCategory.REAL_WORLD_REASONING, 0.85, {"raw_prompt": user_prompt}

        return IntentCategory.GENERAL_CONVERSATION, 0.50, {"raw_prompt": user_prompt}

    def _is_simple_math(self, p: str) -> bool:
        if any(w in p for w in ["derivative", "integral", "matrix", "equation", "solve x"]):
            return False
        clean = re.sub(r'^(what\s+is|calculate|solve|compute|\% of)\s*', '', p).strip()
        if re.search(r'[\d]', clean) and re.search(r'[\+\-\*\/\^\%sqrt]', clean):
            return True
        return bool(self.MATH_SIMPLE_PATTERN.match(p))

    def _extract_math_expression(self, text: str) -> str:
        clean = re.sub(r'(?i)^(what\s+is|calculate|solve|compute|find|\=\?)\s*', '', text.strip())
        clean = clean.rstrip('?').strip()
        return clean

intent_detector = IntentDetector()
