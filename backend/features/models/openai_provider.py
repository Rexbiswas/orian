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

import json
import logging
import requests
from typing import Dict, Any, Optional
from models.base_provider import LLMProvider
from config import settings

logger = logging.getLogger("orian.openai_provider")

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL

    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        if not self.api_key:
            raise ValueError("OpenAI API Key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        ctx_str = f"Context:\n{json.dumps(context, indent=2)}\n\n" if context else ""
        sys_msg = system_prompt or "You are Orian AI, an advanced human-brain-inspired personal AI assistant."
        full_user = f"{ctx_str}User Request: {prompt}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": sys_msg},
                {"role": "user", "content": full_user}
            ],
            "temperature": 0.7
        }

        resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def generate_json(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        sys = (system_prompt or "") + "\nRespond strictly in valid JSON format."
        text = self.generate_response(prompt, context=context, system_prompt=sys)
        try:
            return json.loads(text)
        except Exception:
            # Simple fallback JSON extraction
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1:
                return json.loads(text[start:end+1])
            raise ValueError(f"Could not parse valid JSON from OpenAI output: {text}")
