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

import asyncio
import logging
import time
from typing import Callable, Dict, Any, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("orian.tool_registry")

class ToolResult:
    def __init__(self, success: bool, output: str = "", error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
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

class ToolDefinition(BaseModel):
    name: str
    description: str
    category: str
    permission_level: str = "LOW"  # LOW, MEDIUM, HIGH
    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 30.0
    handler: Optional[Callable[..., Any]] = Field(default=None, exclude=True)

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}

    def register(
        self,
        name: str,
        description: str,
        category: str,
        permission_level: str = "LOW",
        input_schema: Dict[str, Any] = None,
        output_schema: Dict[str, Any] = None,
        timeout_seconds: float = 30.0
    ):
        def decorator(func: Callable):
            tool_def = ToolDefinition(
                name=name,
                description=description,
                category=category,
                permission_level=permission_level,
                input_schema=input_schema or {},
                output_schema=output_schema or {},
                timeout_seconds=timeout_seconds,
                handler=func
            )
            self._tools[name] = tool_def
            logger.info(f"Registered tool: [{permission_level}] {name} ({category})")
            return func
        return decorator

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        tools = []
        for t in self._tools.values():
            if category and t.category != category:
                continue
            tools.append(t.model_dump())
        return tools

    async def execute_tool(self, name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        tool = self.get_tool(name)
        if not tool or not tool.handler:
            return {"success": False, "error": f"Tool '{name}' not found in ToolRegistry"}

        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(tool.handler):
                result = await asyncio.wait_for(tool.handler(**params), timeout=tool.timeout_seconds)
            else:
                result = tool.handler(**params)
            duration = time.time() - start_time
            return {
                "success": True,
                "tool_name": name,
                "duration_seconds": round(duration, 3),
                "result": result
            }
        except asyncio.TimeoutError:
            return {"success": False, "tool_name": name, "error": f"Tool execution timed out after {tool.timeout_seconds}s"}
        except Exception as e:
            logger.error(f"Error executing tool '{name}': {e}", exc_info=True)
            return {"success": False, "tool_name": name, "error": str(e)}

tool_registry = ToolRegistry()
