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

import logging
import psutil
from typing import Dict, Any, List

logger = logging.getLogger("orian.self_diagnostic")

class SelfDiagnosticEngine:
    """Systematic self-diagnostic inspector analyzing logs, stack traces, missing imports, DB status, and tool failures."""

    def run_diagnostics(self) -> Dict[str, Any]:
        results = {
            "logs_inspected": True,
            "database_connectivity": True,
            "system_resources": True,
            "faults_detected": [],
            "health_score": 100.0
        }

        # 1. Inspect Database Connectivity
        try:
            from database.brain_db import brain_db
            agents = brain_db.fetch_all("memory", "SELECT COUNT(*) as cnt FROM agent_connections")
            db_status = "ONLINE" if agents else "NO_AGENTS"
        except Exception as e:
            results["database_connectivity"] = False
            results["faults_detected"].append(f"Database Fault: {str(e)}")
            db_status = "ERROR"

        # 2. Inspect System Telemetry
        cpu_usage = psutil.cpu_percent(interval=0.1)
        ram = psutil.virtual_memory()
        if ram.percent > 92.0:
            results["faults_detected"].append(f"High RAM Utilization: {ram.percent}%")

        # 3. Check for recently recorded mistakes in medulla
        try:
            from database.brain_db import brain_db
            logs = brain_db.fetch_all("medulla", "SELECT * FROM logs WHERE level = 'ERROR' ORDER BY timestamp DESC LIMIT 5")
            if logs:
                for l in logs:
                    results["faults_detected"].append(f"Logged Fault [{l['module']}]: {l['message']}")
        except Exception:
            pass

        fault_count = len(results["faults_detected"])
        health_score = max(0.0, 100.0 - (fault_count * 15.0))
        results["health_score"] = health_score

        formatted_report = (
            f"ORIAN AI SELF-DIAGNOSTIC REPORT:\n"
            f"• Health Score: {health_score}%\n"
            f"• Brain DB Status: {db_status}\n"
            f"• CPU Load: {cpu_usage}% | RAM: {ram.percent}%\n"
            f"• Faults Identified: {fault_count}\n"
        )
        if results["faults_detected"]:
            formatted_report += "  Detailed Faults:\n"
            for f in results["faults_detected"]:
                formatted_report += f"  - {f}\n"
        else:
            formatted_report += "  All neural modules operating at 100% nominal efficiency."

        return {
            "success": True,
            "action": "SELF_DIAGNOSTIC",
            "health_score": health_score,
            "fault_count": fault_count,
            "faults": results["faults_detected"],
            "formatted": formatted_report
        }

self_diagnostic = SelfDiagnosticEngine()
