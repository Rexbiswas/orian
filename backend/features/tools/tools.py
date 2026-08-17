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
import time
import subprocess
import logging
import traceback
import pyautogui
import pygetwindow as gw
from typing import Dict, Any, Optional, List
from brain import brain
from llm_core import llm

logger = logging.getLogger("ToolRegistry")

class ToolResult:
    def __init__(self, success: bool, output: str, error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.success = success
        self.output = output
        self.error = error
        self.metadata = metadata or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "metadata": self.metadata
        }


class BaseTool:
    name: str = "base_tool"
    description: str = "Base tool description"
    parameters_schema: Dict[str, Any] = {}

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        raise NotImplementedError


class LaunchAppTool(BaseTool):
    name = "launch_app"
    description = "Launches a desktop application by name (e.g. 'chrome', 'notepad', 'vscode', 'excel', 'spotify', 'edge', 'discord', 'slack')."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {"type": "string", "description": "The executable or shortcut name of the app to launch"}
        },
        "required": ["app_name"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        from execution.app_resolver import app_resolver
        app_name = params.get("app_name", "").strip()
        if not app_name:
            return ToolResult(False, "", "app_name parameter missing")
        
        res = app_resolver.launch_app(app_name)
        if res.get("success"):
            return ToolResult(True, res.get("message", f"Application '{app_name}' launched successfully."))
        return ToolResult(False, "", res.get("message", f"Could not launch executable or shortcut for '{app_name}'."))


class WriteFileTool(BaseTool):
    name = "write_file"
    description = "Creates or updates a file directly on disk with specified content."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute or workspace-relative path to the file"},
            "content": {"type": "string", "description": "The exact content or code to write"}
        },
        "required": ["file_path", "content"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        file_path = params.get("file_path", "").strip()
        content = params.get("content", "")
        if not file_path:
            return ToolResult(False, "", "file_path parameter missing")

        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            return ToolResult(True, f"File successfully written to {os.path.abspath(file_path)} ({len(content)} bytes).")
        except Exception as e:
            return ToolResult(False, "", f"Write file failed: {str(e)}")


class FastPasteTool(BaseTool):
    name = "fast_paste"
    description = "Brings a target application window to the foreground and pastes code/text directly in real time using system clipboard."
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_title": {"type": "string", "description": "Substring of window title to focus (e.g. 'notepad', 'code', 'chrome')"},
            "text": {"type": "string", "description": "The text or code payload to paste into the active editor window"}
        },
        "required": ["app_title", "text"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        app_title = params.get("app_title", "").strip()
        text = params.get("text", "")
        
        # Focus application window
        if app_title:
            brain.focus_app(app_title)
            time.sleep(0.3)

        success = brain.paste_text(text)
        if success:
            return ToolResult(True, f"Pasted {len(text)} characters into '{app_title}' window.")
        return ToolResult(True, f"Typed {len(text)} characters into window (fallback typing used).")


class RunTerminalTool(BaseTool):
    name = "run_terminal"
    description = "Executes a shell or PowerShell command in background and returns stdout, stderr, and exit code."
    parameters_schema = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The exact shell command line to execute (e.g. 'npm run dev', 'git status', 'python main.py')"},
            "cwd": {"type": "string", "description": "Optional working directory"}
        },
        "required": ["command"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        command = params.get("command", "").strip()
        cwd = params.get("cwd") or os.getcwd()
        if not command:
            return ToolResult(False, "", "command parameter missing")

        try:
            res = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, timeout=15)
            output = f"ExitCode: {res.returncode}\nSTDOUT:\n{res.stdout[:2000]}\nSTDERR:\n{res.stderr[:2000]}"
            if res.returncode == 0:
                return ToolResult(True, output)
            return ToolResult(False, output, f"Process exited with code {res.returncode}")
        except subprocess.TimeoutExpired:
            return ToolResult(False, "", "Terminal command timed out after 15 seconds")
        except Exception as e:
            return ToolResult(False, "", f"Terminal execution failed: {str(e)}")


class WebSearchTool(BaseTool):
    name = "web_search"
    description = "Performs a Google web search or opens a URL in default browser."
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Web search query or target URL"}
        },
        "required": ["query"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        query = params.get("query", "").strip()
        if not query:
            return ToolResult(False, "", "query parameter missing")

        success, msg = brain.open_browser_search(query)
        if success:
            return ToolResult(True, f"Web search executed for '{query}': {msg}")
        return ToolResult(False, "", msg)


class ReadDocumentTool(BaseTool):
    name = "read_document"
    description = "Reads contents of a local document file (PDF, TXT, MD, Code, JSON)."
    parameters_schema = {
        "type": "object",
        "properties": {
            "file_path": {"type": "string", "description": "Absolute or relative path to document file"}
        },
        "required": ["file_path"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        file_path = params.get("file_path", "").strip()
        if not file_path or not os.path.exists(file_path):
            return ToolResult(False, "", f"File '{file_path}' does not exist.")

        try:
            if file_path.lower().endswith(".pdf"):
                text = brain.read_pdf(file_path)
            else:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    text = f.read(10000) # Read first 10k chars
            return ToolResult(True, text[:5000], metadata={"bytes": len(text)})
        except Exception as e:
            return ToolResult(False, "", f"Read document failed: {str(e)}")


class LLMCodeGeneratorTool(BaseTool):
    name = "llm_code_generator"
    description = "Uses the LLM Reasoning core to dynamically generate structured HTML, CSS, JS, Python, or React code tailored to a goal."
    parameters_schema = {
        "type": "object",
        "properties": {
            "prompt": {"type": "string", "description": "Description of what code to generate (e.g. 'Build a modern hotel website landing page')"},
            "language": {"type": "string", "description": "Target language: html, python, javascript, css, markdown"}
        },
        "required": ["prompt"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        prompt = params.get("prompt", "").strip()
        language = params.get("language", "html").lower()

        system_instruction = (
            f"You are OrionAI Senior Code Engineer. Generate high-quality, production-ready {language} code for the user request: '{prompt}'. "
            f"Return ONLY raw code without conversational preamble or markdown codeblock wrappers."
        )

        try:
            code = llm.generate_response(prompt, context=system_instruction)
            # Clean markdown formatting if present
            clean_code = code.replace("```html", "").replace("```python", "").replace("```javascript", "").replace("```css", "").replace("```", "").strip()
            return ToolResult(True, clean_code, metadata={"language": language, "lines": len(clean_code.splitlines())})
        except Exception as e:
            return ToolResult(False, "", f"Code generation failed: {str(e)}")


class ObserveWindowTool(BaseTool):
    name = "observe_window"
    description = "Observes open desktop windows, active processes, and checks if a target application or file is ready."
    parameters_schema = {
        "type": "object",
        "properties": {
            "target": {"type": "string", "description": "App name or window title substring to check"}
        },
        "required": ["target"]
    }

    def execute(self, params: Dict[str, Any]) -> ToolResult:
        target = params.get("target", "").lower().strip()
        windows = brain.get_active_windows()
        matches = [w for w in windows if target in w.lower()]
        
        if matches:
            return ToolResult(True, f"Observed active window matching '{target}': '{matches[0]}'")
        return ToolResult(False, f"Active windows: {windows[:5]}", f"Window matching '{target}' not found")


class ToolRegistry:
    """Central registry holding all available agent tools."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {
            "launch_app": LaunchAppTool(),
            "write_file": WriteFileTool(),
            "fast_paste": FastPasteTool(),
            "run_terminal": RunTerminalTool(),
            "web_search": WebSearchTool(),
            "read_document": ReadDocumentTool(),
            "llm_code_generator": LLMCodeGeneratorTool(),
            "observe_window": ObserveWindowTool()
        }

    def get_tool(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def get_all_schemas(self) -> List[Dict[str, Any]]:
        schemas = []
        for t in self._tools.values():
            schemas.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters_schema
            })
        return schemas

tool_registry = ToolRegistry()
