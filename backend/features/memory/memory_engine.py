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
import logging
from typing import Dict, Any, List, Optional
from brain_manager import brain_manager

logger = logging.getLogger("MemoryEngine")

class MemoryEngine:
    """Facade wrapping Memory Operations to route through BrainManager."""

    def record_project(self, name: str, path: str, tech_stack: str = "React/Node"):
        brain_manager.cerebrum.store_project(name, path, tech_stack)

    def get_last_active_project(self) -> Dict[str, Any]:
        return brain_manager.cerebrum.get_last_project()

    def set_preference(self, key: str, value: str):
        brain_manager.cerebrum.set_preference(key, value)

    def get_context_summary(self) -> str:
        return brain_manager.get_cognitive_context()

memory_engine = MemoryEngine()
