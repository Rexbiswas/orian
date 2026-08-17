import json
import logging
import requests
from typing import Dict, Any, Optional
from models.base_provider import LLMProvider
from config import settings

logger = logging.getLogger("orian.huggingface_provider")

class HuggingFaceProvider(LLMProvider):
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.HUGGINGFACE_API_KEY
        self.model = model or settings.HUGGINGFACE_MODEL

    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        if not self.api_key:
            raise ValueError("Hugging Face API Key not configured")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        ctx_str = f"Context: {json.dumps(context)}\n" if context else ""
        sys_str = system_prompt or "You are Orian AI."
        full_input = f"<s>[INST] <<SYS>>\n{sys_str}\n<</SYS>>\n\n{ctx_str}{prompt} [/INST]"

        url = f"https://api-inference.huggingface.co/models/{self.model}"
        payload = {"inputs": full_input, "parameters": {"max_new_tokens": 512, "temperature": 0.7}}

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        res = resp.json()
        if isinstance(res, list) and len(res) > 0 and "generated_text" in res[0]:
            return res[0]["generated_text"]
        return str(res)

    def generate_json(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        sys = (system_prompt or "") + " Output ONLY valid JSON."
        text = self.generate_response(prompt, context=context, system_prompt=sys)
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            return json.loads(text[start:end+1])
        return {"raw_output": text}
