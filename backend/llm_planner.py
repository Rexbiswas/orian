import sys
import os

# Ensure site-packages is in sys.path
for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

backend_dir = os.path.dirname(os.path.abspath(__file__))
features_dir = os.path.join(backend_dir, "features")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if features_dir not in sys.path:
    sys.path.insert(0, features_dir)

from features.planner.task_planner import task_planner, task_planner as planner, ExecutionPlan, SubTask

__all__ = ["task_planner", "planner", "ExecutionPlan", "SubTask"]
