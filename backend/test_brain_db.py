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

import sys
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
features_dir = os.path.join(backend_dir, "features")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if features_dir not in sys.path:
    sys.path.insert(0, features_dir)

from database.brain_db import brain_db
from brain.orian_brain import orian_brain
from memory.sqlite_store import sqlite_store

def run_brain_db_test_suite():
    print("=" * 65)
    print("      ORIAN AI ANATOMICAL BRAIN_DB TEST SUITE")
    print("=" * 65)

    # 1. Test Database Files Existence
    print("\n[TEST 1] Verifying Physical Database Files...")
    dbs = ["cerebrum", "cerebellum", "medulla", "memory"]
    for db_name in dbs:
        path = getattr(brain_db, f"{db_name}_path")
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        status = f"EXISTS ({size} bytes)" if exists else "MISSING"
        print(f"  [OK] {db_name.upper():<12}.db : {status} at {path}")
        assert exists, f"Database {db_name}.db was not created!"

    # 2. Test Agent Connections
    print("\n[TEST 2] Verifying Agent Connections in memory.db...")
    agents = brain_db.fetch_all("memory", "SELECT * FROM agent_connections")
    print(f"  Total Registered Agents: {len(agents)}")
    for a in agents:
        print(f"  [OK] Agent: {a['agent_id']:<22} | Region: {a['assigned_region']:<10} | Status: {a['status']}")
    assert len(agents) >= 6, "Expected at least 6 connected agents!"

    # 3. Test Database Routing (Cerebrum, Cerebellum, Medulla, Memory)
    print("\n[TEST 3] Testing Data Routing across Brain Regions...")
    
    # Store User & Project in Cerebrum
    sqlite_store.store_user("test_user_1", "orion_tester", "Orion Tester", "test@orion.ai")
    sqlite_store.store_project("test_proj_1", "Orion Test Suite", backend_dir, "Test description")
    user_row = brain_db.fetch_one("cerebrum", "SELECT * FROM users WHERE id = ?", ("test_user_1",))
    proj_row = brain_db.fetch_one("cerebrum", "SELECT * FROM projects WHERE id = ?", ("test_proj_1",))
    print(f"  [OK] [CEREBRUM] User Cognition Record  : {user_row['display_name']} (@{user_row['username']})")
    print(f"  [OK] [CEREBRUM] Project Reason Record : {proj_row['name']} ({proj_row['path']})")
    assert user_row and proj_row, "Cerebrum routing test failed!"

    # Store Task in Cerebellum
    sqlite_store.store_task("task_001", "Execute System Diagnostics", status="RUNNING", risk_level="LOW")
    task_row = brain_db.fetch_one("cerebellum", "SELECT * FROM tasks WHERE id = ?", ("task_001",))
    print(f"  [OK] [CEREBELLUM] Motor Task Record    : {task_row['title']} [{task_row['status']}]")
    assert task_row, "Cerebellum routing test failed!"

    # Log Event in Medulla
    sqlite_store.log_event("req_1001", "LearningSecurityAgent", "INFO", "SECURITY_CHECK", "Safety evaluation passed")
    log_row = brain_db.fetch_one("medulla", "SELECT * FROM logs WHERE request_id = ?", ("req_1001",))
    print(f"  [OK] [MEDULLA] Autonomic Log Record    : [{log_row['level']}] {log_row['message']}")
    assert log_row, "Medulla routing test failed!"

    # Store Message in Memory.db
    msg_id = sqlite_store.add_message("session_test_100", "user", "Hello Orian, test brain db integration.")
    msg_row = brain_db.fetch_one("memory", "SELECT * FROM messages WHERE id = ?", (msg_id,))
    print(f"  [OK] [MEMORY] Cognitive Msg Record    : ({msg_row['role']}) {msg_row['content']}")
    assert msg_row, "Memory bridge routing test failed!"

    print("\n" + "=" * 65)
    print("     ALL ANATOMICAL BRAIN_DB TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == "__main__":
    run_brain_db_test_suite()
