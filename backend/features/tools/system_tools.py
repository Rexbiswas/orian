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
import subprocess
import logging
import urllib.request
import json
from typing import Dict, Any, List
from tools.tool_registry import tool_registry
from memory.memory_manager import memory_manager
from config import settings

logger = logging.getLogger("orian.tools")

# --- FILE TOOLS ---
@tool_registry.register(
    name="read_file",
    description="Reads content of a file from the filesystem.",
    category="FileTools",
    permission_level="LOW"
)
async def read_file_handler(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        return {"content": "", "exists": False, "error": "File not found"}
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read(50000)  # Max 50KB for safety
    return {"content": content, "exists": True, "size_bytes": os.path.getsize(file_path)}

@tool_registry.register(
    name="write_file",
    description="Writes content to a file on the filesystem.",
    category="FileTools",
    permission_level="MEDIUM"
)
async def write_file_handler(file_path: str, content: str) -> Dict[str, Any]:
    os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return {"file_path": file_path, "written_bytes": len(content), "status": "success"}

@tool_registry.register(
    name="list_directory",
    description="Lists files and subdirectories in a target folder.",
    category="FileTools",
    permission_level="LOW"
)
async def list_directory_handler(dir_path: str) -> Dict[str, Any]:
    target = dir_path or settings.PROJECTS_DIR
    if not os.path.exists(target):
        return {"items": [], "exists": False}
    items = []
    for entry in os.scandir(target):
        items.append({
            "name": entry.name,
            "is_dir": entry.is_dir(),
            "size": entry.stat().st_size if entry.is_file() else 0
        })
    return {"dir_path": target, "items": items}

# --- TERMINAL TOOLS ---
@tool_registry.register(
    name="run_terminal_command",
    description="Executes a shell command in the terminal.",
    category="TerminalTools",
    permission_level="MEDIUM"
)
async def run_terminal_command_handler(command: str, cwd: str = None) -> Dict[str, Any]:
    work_dir = cwd or os.getcwd()
    try:
        proc = subprocess.run(
            command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        return {
            "stdout": proc.stdout[:10000],
            "stderr": proc.stderr[:5000],
            "returncode": proc.returncode,
            "success": proc.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Execution timed out after 30s", "returncode": -1, "success": False}

# --- SYSTEM & AUTOMATION TOOLS ---
@tool_registry.register(
    name="open_application",
    description="Opens a software application on the operating system.",
    category="SystemTools",
    permission_level="LOW"
)
async def open_application_handler(app_name: str) -> Dict[str, Any]:
    try:
        if os.name == "nt":
            os.system(f"start {app_name}")
        else:
            subprocess.Popen([app_name])
        return {"app_name": app_name, "status": "launched"}
    except Exception as e:
        return {"app_name": app_name, "error": str(e)}

@tool_registry.register(
    name="delete_files",
    description="Deletes target files or directories.",
    category="FileTools",
    permission_level="HIGH"
)
async def delete_files_handler(target_path: str) -> Dict[str, Any]:
    if not os.path.exists(target_path):
        return {"deleted": False, "error": "Path does not exist"}
    if os.path.isfile(target_path):
        os.remove(target_path)
    else:
        import shutil
        shutil.rmtree(target_path)
    return {"deleted": True, "target_path": target_path}

# --- DEVELOPER TOOLS ---
@tool_registry.register(
    name="inspect_project",
    description="Scans project directory layout and dependencies.",
    category="DeveloperTools",
    permission_level="LOW"
)
async def inspect_project_handler(project_dir: str = None) -> Dict[str, Any]:
    p_dir = project_dir or settings.ORIAN_ROOT_DIR
    if not os.path.exists(p_dir):
        p_dir = os.getcwd()

    structure = []
    for root, dirs, files in os.walk(p_dir):
        # Exclude node_modules and .git for speed
        dirs[:] = [d for d in dirs if d not in ["node_modules", ".git", "__pycache__", "dist"]]
        rel = os.path.relpath(root, p_dir)
        structure.append({"folder": rel, "files": files[:20]})
        if len(structure) > 20:
            break

    return {"project_dir": p_dir, "structure_sample": structure}

# --- MEMORY TOOLS ---
@tool_registry.register(
    name="search_memory",
    description="Searches long-term semantic and working memories.",
    category="MemoryTools",
    permission_level="LOW"
)
async def search_memory_handler(query: str, session_id: str = "default_session") -> Dict[str, Any]:
    res = await memory_manager.retrieve_context_for_reasoning(query, session_id)
    return res

# --- API & BROWSER TOOLS ---
@tool_registry.register(
    name="http_request",
    description="Makes an HTTP GET or POST request to a web URL.",
    category="APITools",
    permission_level="MEDIUM"
)
async def http_request_handler(url: str, method: str = "GET", data: dict = None) -> Dict[str, Any]:
    try:
        req = urllib.request.Request(url, method=method.upper())
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        with urllib.request.urlopen(req, timeout=10) as response:
            body = response.read().decode('utf-8')
            return {"status_code": response.status, "content": body[:5000]}
    except Exception as e:
        return {"error": str(e), "url": url}
