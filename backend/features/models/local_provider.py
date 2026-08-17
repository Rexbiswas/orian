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
from typing import Dict, Any, Optional
from models.base_provider import LLMProvider

logger = logging.getLogger("orian.local_provider")

class LocalProvider(LLMProvider):
    """Local cognitive heuristics model provider for zero-key local operation."""

    def generate_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        prompt_lower = prompt.lower()
        
        # Analyze intent using local rules
        if any(w in prompt_lower for w in ["react", "portfolio", "create", "build", "app"]):
            return (
                f"Orian Local Brain Analysis:\n"
                f"I have received your request to build/create: '{prompt}'.\n"
                f"I am initializing the Developer Agent and Task Planner to inspect project requirements, "
                f"create structure, and generate components."
            )
        elif any(w in prompt_lower for w in ["open", "browser", "close", "system"]):
            return f"Orian Local Brain Analysis:\nPreparing automation task for: '{prompt}'."
        else:
            return (
                f"Orian Brain Response:\n"
                f"Processed request: '{prompt}'.\n"
                f"Working memory and cognitive context evaluated successfully."
            )

    def generate_json(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        
        # Heuristic task breakdown for planning
        if "react" in prompt_lower or "portfolio" in prompt_lower or "create" in prompt_lower:
            return {
                "thought": "Decomposing web project request into executable subtasks.",
                "plan": [
                    {
                        "task_id": "subtask-1",
                        "title": "Inspect & Analyze Requirements",
                        "tool": "inspect_project",
                        "risk_level": "LOW",
                        "params": {"project_name": "portfolio"}
                    },
                    {
                        "task_id": "subtask-2",
                        "title": "Generate React Architecture & Files",
                        "tool": "generate_code_files",
                        "risk_level": "MEDIUM",
                        "params": {"target": "src/App.jsx"}
                    },
                    {
                        "task_id": "subtask-3",
                        "title": "Run Dev Server & Verification Tests",
                        "tool": "run_terminal_command",
                        "risk_level": "MEDIUM",
                        "params": {"command": "npm test"}
                    }
                ]
            }
        
        return {
            "thought": "Standard cognitive processing.",
            "plan": [
                {
                    "task_id": "subtask-1",
                    "title": f"Execute action: {prompt[:30]}...",
                    "tool": "general_processor",
                    "risk_level": "LOW",
                    "params": {"query": prompt}
                }
            ]
        }
