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
