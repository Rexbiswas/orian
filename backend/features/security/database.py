import os
import sqlite3
import json
import time
import logging
from typing import Dict, List, Any, Optional
from config import settings
from .models import Role, Permission

logger = logging.getLogger("orian.security.database")

class SecurityDatabase:
    """SQLite Security Database manager creating and managing tables for users, sessions, RBAC, audit logs, and IoT credentials."""

    def __init__(self, db_path: str = settings.SQLITE_DB_PATH):
        self.db_path = db_path
        self._init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
        conn = self.get_connection()
        cursor = conn.cursor()

        # 1. Users
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT,
            email TEXT,
            role TEXT NOT NULL DEFAULT 'USER',
            is_active INTEGER DEFAULT 1,
            mfa_enabled INTEGER DEFAULT 0,
            mfa_secret_encrypted TEXT,
            failed_login_attempts INTEGER DEFAULT 0,
            locked_until REAL,
            created_at REAL,
            updated_at REAL
        )
        """)

        # 2. Sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_sessions (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            role TEXT NOT NULL,
            token_hash TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            is_mfa_verified INTEGER DEFAULT 0,
            is_active INTEGER DEFAULT 1,
            created_at REAL,
            last_active REAL,
            expires_at REAL,
            FOREIGN KEY (user_id) REFERENCES sec_users (id) ON DELETE CASCADE
        )
        """)

        # 3. Roles & Permissions RBAC
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_roles (
            name TEXT PRIMARY KEY,
            description TEXT,
            level INTEGER NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_permissions (
            name TEXT PRIMARY KEY,
            description TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_role_permissions (
            role_name TEXT NOT NULL,
            permission_name TEXT NOT NULL,
            PRIMARY KEY (role_name, permission_name),
            FOREIGN KEY (role_name) REFERENCES sec_roles (name) ON DELETE CASCADE,
            FOREIGN KEY (permission_name) REFERENCES sec_permissions (name) ON DELETE CASCADE
        )
        """)

        # 4. Confirmation Tickets
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_confirmation_tickets (
            ticket_id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            action TEXT NOT NULL,
            target TEXT,
            risk_level TEXT NOT NULL,
            command TEXT NOT NULL,
            parameters_json TEXT DEFAULT '{}',
            expires_at REAL NOT NULL,
            confirmed INTEGER DEFAULT 0,
            confirmed_at REAL,
            created_at REAL
        )
        """)

        # 5. Audit Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_audit_logs (
            id TEXT PRIMARY KEY,
            timestamp REAL NOT NULL,
            user_id TEXT,
            session_id TEXT,
            action TEXT NOT NULL,
            tool TEXT,
            target TEXT,
            risk TEXT,
            result TEXT,
            error_message TEXT,
            ip_address TEXT,
            device TEXT,
            request_id TEXT,
            details_json TEXT DEFAULT '{}'
        )
        """)

        # 6. Security Events
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_security_events (
            id TEXT PRIMARY KEY,
            timestamp REAL NOT NULL,
            event_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            user_id TEXT,
            ip_address TEXT,
            message TEXT,
            details_json TEXT DEFAULT '{}'
        )
        """)

        # 7. IoT Device Credentials & Identity
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_iot_credentials (
            device_id TEXT PRIMARY KEY,
            secret_token_hash TEXT NOT NULL,
            public_id TEXT UNIQUE NOT NULL,
            status TEXT DEFAULT 'ACTIVE',
            is_registered INTEGER DEFAULT 1,
            last_nonce TEXT,
            last_command_timestamp REAL DEFAULT 0,
            created_at REAL,
            updated_at REAL
        )
        """)

        # 8. Self-Programming Code Changes & Rollbacks
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_code_changes (
            change_id TEXT PRIMARY KEY,
            user_id TEXT,
            component TEXT,
            change_type TEXT,
            patch_content TEXT,
            snapshot_id TEXT,
            status TEXT,
            reason TEXT,
            tests_passed INTEGER DEFAULT 1,
            health_score REAL DEFAULT 100.0,
            created_at REAL,
            applied_at REAL,
            rolled_back_at REAL
        )
        """)

        # Indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_sessions_token ON sec_sessions(token_hash)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_audit_time ON sec_audit_logs(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_events_time ON sec_security_events(timestamp)")

        conn.commit()
        conn.close()

        # Seed RBAC tables
        self._seed_rbac_defaults()

    def _seed_rbac_defaults(self):
        """Seeds default roles and granular permissions if not present."""
        conn = self.get_connection()
        cursor = conn.cursor()

        roles = [
            ("OWNER", "Complete unrestricted system control and security governance", 100),
            ("ADMIN", "System configuration, diagnostics, and management", 80),
            ("TRUSTED_USER", "Full tool execution, desktop control, and IoT operations", 60),
            ("USER", "Standard conversational AI and basic tool usage", 40),
            ("GUEST", "Restricted conversation and safe calculation only", 20),
            ("DEVICE", "Machine-to-machine IoT device identity", 10),
        ]

        for name, desc, lvl in roles:
            cursor.execute("INSERT OR IGNORE INTO sec_roles (name, description, level) VALUES (?, ?, ?)", (name, desc, lvl))

        permissions = [
            ("chat", "Interact with Orian conversational LLM"),
            ("calculator", "Execute simple and advanced mathematical evaluations"),
            ("read_memory", "Read cognitive memories and past interactions"),
            ("write_memory", "Store memories and preferences"),
            ("open_application", "Launch and control desktop applications"),
            ("read_file", "Read files within user workspace"),
            ("write_file", "Write files within user workspace"),
            ("delete_file", "Delete files"),
            ("execute_command", "Run system and shell commands"),
            ("iot_read", "Query IoT devices, status, and telemetry feeds"),
            ("iot_control", "Dispatch commands to IoT hardware"),
            ("system_control", "Change OS settings and perform cleanup"),
            ("code_read", "Inspect source code and project repositories"),
            ("code_modify", "Modify codebase or generate patches"),
            ("self_diagnose", "Run health checks and self-diagnostics"),
            ("self_program", "Execute controlled self-programming routines"),
            ("security_admin", "Manage users, credentials, and security policies"),
            ("user_admin", "Create, update, and deactivate user accounts"),
        ]

        for name, desc in permissions:
            cursor.execute("INSERT OR IGNORE INTO sec_permissions (name, description) VALUES (?, ?)", (name, desc))

        # Permission mappings
        role_perms = {
            "GUEST": ["chat", "calculator"],
            "USER": ["chat", "calculator", "read_memory", "write_memory", "read_file", "iot_read"],
            "TRUSTED_USER": ["chat", "calculator", "read_memory", "write_memory", "read_file", "write_file", "open_application", "iot_read", "iot_control", "self_diagnose"],
            "ADMIN": ["chat", "calculator", "read_memory", "write_memory", "read_file", "write_file", "delete_file", "open_application", "iot_read", "iot_control", "system_control", "code_read", "self_diagnose", "user_admin"],
            "OWNER": [p[0] for p in permissions], # All permissions
            "DEVICE": ["iot_read", "iot_control"]
        }

        for role_name, perms in role_perms.items():
            for perm in perms:
                cursor.execute("INSERT OR IGNORE INTO sec_role_permissions (role_name, permission_name) VALUES (?, ?)", (role_name, perm))

        conn.commit()
        conn.close()

security_db = SecurityDatabase()
