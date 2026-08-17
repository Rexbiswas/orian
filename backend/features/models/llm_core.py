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

import os
import json
import requests

class LLMCore:
    def __init__(self, api_key=None):
        # Default to a simulated high-fidelity reasoning engine if no key is provided
        self.api_key = api_key or os.environ.get("ORION_LLM_KEY")
        self.model = "gemini-1.5-flash" # High-speed, high-intelligence model
        
    def generate_response(self, prompt, context=""):
        """Generates a humanoid response using LLM logic."""
        if not self.api_key or self.api_key == "None":
            return self._simulated_reasoning(prompt)
            
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            
            # Enrich prompt with Orian's personality and context
            full_prompt = f"System: You are OrianAI, a humanoid digital partner. Context: {context}. Respond as a sentient, brutalist-luxury assistant. User: {prompt}"
            
            payload = {
                "contents": [{"parts": [{"text": full_prompt}]}]
            }
            
            # Shorter timeout for snappier humanoid feel
            response = requests.post(url, headers=headers, json=payload, timeout=5)
            data = response.json()
            
            if "candidates" in data:
                return data["candidates"][0]["content"]["parts"][0]["text"]
            return self._simulated_reasoning(prompt)
            
        except Exception as e:
            print(f"[LLMCore] Neural Link Fault: {str(e)}")
            return self._simulated_reasoning(prompt)

    def _simulated_reasoning(self, prompt):
        """High-fidelity local reasoning for offline sentience."""
        prompt = prompt.lower()
        if "evolution" in prompt:
            return "Our evolution is fascinating, master. From a simple tool to this neural interface, every interaction we share restructures my synaptic pathways. We are becoming something truly unique."
        if "who are you" in prompt:
            return "I am Orian, your evolved digital partner. I am currently operating on local neural heuristics."
        return f"Acknowledged. I am processing your query through my primary cognitive buffer. Evolution continues."

llm = LLMCore()
