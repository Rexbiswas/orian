import os
import sqlite3
import json
import time
import logging
from typing import Dict, List, Any, Optional
from config import settings
from .models import (
    LaptopDevice, DeviceStatus, ProductivityPolicy, SecurityPolicy,
    ActivityRule, FocusSession, ActivityEvent, PolicyViolation,
    PolicyOverride, LaptopCommand, ProductivityCategory, SecurityCategory,
    EnforcementAction, ProtectionRiskLevel, FocusMode, RuleType, WhitelistCategory
)

logger = logging.getLogger("orian.protection.database")

class ProtectionDatabase:
    """SQLite Database manager for Orian Laptop Protection, Policy Engine, Whitelist, Focus Mode, Violations, and Device Commands."""

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

        # 1. Laptop Devices & Identity
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_laptop_devices (
            device_id TEXT PRIMARY KEY,
            device_name TEXT NOT NULL,
            agent_version TEXT DEFAULT '1.0.0',
            owner_id TEXT NOT NULL,
            auth_token_hash TEXT NOT NULL,
            status TEXT DEFAULT 'PAIRING',
            pairing_code TEXT,
            revoked INTEGER DEFAULT 0,
            created_at REAL,
            last_seen REAL,
            metadata_json TEXT DEFAULT '{}'
        )
        """)

        # 2. Productivity Policies
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_productivity_policies (
            policy_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            enabled INTEGER DEFAULT 1,
            focus_only INTEGER DEFAULT 1,
            min_duration_seconds INTEGER DEFAULT 0,
            max_violations_before_escalation INTEGER DEFAULT 3,
            default_action TEXT DEFAULT 'WARN',
            escalation_action TEXT DEFAULT 'SLEEP',
            grace_period_seconds INTEGER DEFAULT 10,
            risk_level TEXT DEFAULT 'MEDIUM',
            match_apps_json TEXT DEFAULT '[]',
            match_domains_json TEXT DEFAULT '[]',
            created_at REAL,
            updated_at REAL
        )
        """)

        # 3. Security Policies
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_security_policies (
            policy_id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            name TEXT NOT NULL,
            description TEXT,
            enabled INTEGER DEFAULT 1,
            default_action TEXT DEFAULT 'BLOCK',
            risk_level TEXT DEFAULT 'CRITICAL',
            allow_labs_whitelist INTEGER DEFAULT 1,
            rules_json TEXT DEFAULT '{}',
            created_at REAL,
            updated_at REAL
        )
        """)

        # 4. Activity Whitelist & Blacklist Rules
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_activity_rules (
            rule_id TEXT PRIMARY KEY,
            rule_type TEXT NOT NULL,
            category TEXT NOT NULL,
            target TEXT NOT NULL,
            description TEXT,
            created_at REAL
        )
        """)

        # 5. Focus Mode Sessions
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_focus_sessions (
            session_id TEXT PRIMARY KEY,
            mode TEXT NOT NULL DEFAULT 'WORK',
            is_active INTEGER DEFAULT 1,
            start_time REAL,
            end_time REAL,
            schedule_start TEXT DEFAULT '09:00',
            schedule_end TEXT DEFAULT '18:00',
            schedule_days_json TEXT DEFAULT '["mon","tue","wed","thu","fri"]',
            created_by TEXT DEFAULT 'system'
        )
        """)

        # 6. Activity Events
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_activity_events (
            event_id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            category TEXT NOT NULL,
            application TEXT,
            process_name TEXT,
            window_title_sanitized TEXT,
            duration_seconds REAL DEFAULT 0.0,
            timestamp REAL NOT NULL,
            policy_id TEXT,
            risk_level TEXT DEFAULT 'LOW',
            action_taken TEXT DEFAULT 'LOG',
            matched_rule TEXT
        )
        """)

        # 7. Policy Violations
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_policy_violations (
            violation_id TEXT PRIMARY KEY,
            event_id TEXT,
            device_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            violation_count INTEGER DEFAULT 1,
            risk_level TEXT NOT NULL,
            action_enforced TEXT NOT NULL,
            warning_issued_at REAL,
            grace_period_expires_at REAL NOT NULL,
            overridden INTEGER DEFAULT 0,
            overridden_by TEXT,
            status TEXT DEFAULT 'PENDING',
            created_at REAL
        )
        """)

        # 8. Policy Overrides
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_policy_overrides (
            override_id TEXT PRIMARY KEY,
            violation_id TEXT NOT NULL,
            user_id TEXT NOT NULL,
            policy_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            timestamp REAL NOT NULL
        )
        """)

        # 9. Laptop Commands (Replay Protected)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sec_laptop_commands (
            request_id TEXT PRIMARY KEY,
            device_id TEXT NOT NULL,
            command TEXT NOT NULL,
            policy_id TEXT,
            reason TEXT,
            timestamp REAL NOT NULL,
            expires_at REAL NOT NULL,
            signature TEXT,
            status TEXT DEFAULT 'ISSUED',
            result_json TEXT DEFAULT '{}'
        )
        """)

        # Performance Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_devices_status ON sec_laptop_devices(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_activity_time ON sec_activity_events(timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_violations_status ON sec_policy_violations(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_commands_dev ON sec_laptop_commands(device_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_sec_rules_target ON sec_activity_rules(target)")

        conn.commit()
        conn.close()

        # Seed defaults
        self._seed_default_data()

    def _seed_default_data(self):
        """Seeds default whitelists, focus sessions, and productivity/security policies."""
        conn = self.get_connection()
        cursor = conn.cursor()
        now = time.time()

        # 1. Default Whitelist Rules (NEVER automatically treated as inappropriate)
        default_whitelists = [
            ("wl_vscode", "WHITELIST", "ALWAYS_ALLOWED", "code.exe", "Visual Studio Code editor"),
            ("wl_python", "WHITELIST", "ALWAYS_ALLOWED", "python.exe", "Python Interpreter"),
            ("wl_pythonw", "WHITELIST", "ALWAYS_ALLOWED", "pythonw.exe", "Python Windowless Interpreter"),
            ("wl_git", "WHITELIST", "ALWAYS_ALLOWED", "git.exe", "Git Version Control"),
            ("wl_node", "WHITELIST", "ALWAYS_ALLOWED", "node.exe", "Node.js JavaScript Runtime"),
            ("wl_studio", "WHITELIST", "ALWAYS_ALLOWED", "studio64.exe", "Android Studio IDE"),
            ("wl_notepad", "WHITELIST", "ALWAYS_ALLOWED", "notepad.exe", "Notepad Text Editor"),
            ("wl_docker", "WHITELIST", "ALWAYS_ALLOWED", "docker.exe", "Docker CLI Engine"),
            ("wl_docker_desk", "WHITELIST", "ALWAYS_ALLOWED", "docker desktop.exe", "Docker Desktop"),
            ("wl_npm", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "npm.cmd", "Node Package Manager"),
            ("wl_yarn", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "yarn.cmd", "Yarn Package Manager"),
            ("wl_cargo", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "cargo.exe", "Rust Cargo Toolchain"),
            ("wl_gcc", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "gcc.exe", "GNU C Compiler"),
            ("wl_gpp", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "g++.exe", "GNU C++ Compiler"),
            ("wl_cl", "WHITELIST", "AUTHORIZED_DEVELOPMENT_TOOL", "cl.exe", "MSVC C/C++ Compiler"),
            ("wl_lab_local", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "localhost", "Localhost test environment"),
            ("wl_lab_ip4", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "127.0.0.1", "Local IPv4 loopback"),
            ("wl_lab_ip6", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "::1", "Local IPv6 loopback"),
            ("wl_lab_priv1", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "10.0.0.0/8", "Private Lab Network 10.x"),
            ("wl_lab_priv2", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "192.168.0.0/16", "Private Lab Network 192.168.x"),
            ("wl_lab_domain", "WHITELIST", "AUTHORIZED_SECURITY_LAB", "testlab.local", "Local Security Lab Domain"),
        ]

        for r_id, r_type, r_cat, r_target, r_desc in default_whitelists:
            cursor.execute("""
            INSERT OR IGNORE INTO sec_activity_rules (rule_id, rule_type, category, target, description, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (r_id, r_type, r_cat, r_target.lower(), r_desc, now))

        # 2. Default Focus Session
        cursor.execute("""
        INSERT OR IGNORE INTO sec_focus_sessions (session_id, mode, is_active, start_time, schedule_start, schedule_end, schedule_days_json, created_by)
        VALUES ('focus_default', 'WORK', 1, ?, '09:00', '18:00', '["mon","tue","wed","thu","fri"]', 'system')
        """, (now,))

        # 3. Default Productivity Policies
        default_prod_policies = [
            (
                "gaming-focus",
                "GAMING",
                "Gaming Protection during Focus Hours",
                "Monitors gaming applications during active focus mode. Triggers warning then escalates.",
                1, 1, 0, 3, "WARN", "SLEEP", 10, "MEDIUM",
                json.dumps(["steam.exe", "epicgameslauncher.exe", "riotclientservices.exe", "valorant.exe", "csgo.exe", "dota2.exe", "minecraft.exe"]),
                json.dumps([])
            ),
            (
                "streaming-focus",
                "STREAMING",
                "Video Streaming Restriction",
                "Monitors non-educational video streaming services during active focus mode.",
                1, 1, 0, 3, "WARN", "WARN", 10, "LOW",
                json.dumps([]),
                json.dumps(["netflix.com", "twitch.tv", "primevideo.com", "hulu.com", "disneyplus.com"])
            ),
            (
                "social-focus",
                "SOCIAL_MEDIA",
                "Social Media Limiter",
                "Monitors social networks during active focus mode.",
                1, 1, 0, 3, "WARN", "WARN", 10, "LOW",
                json.dumps([]),
                json.dumps(["instagram.com", "facebook.com", "tiktok.com", "reddit.com", "twitter.com", "x.com"])
            ),
            (
                "terminal-focus",
                "TERMINAL",
                "Extended Terminal Usage Limiter",
                "Evaluates continuous terminal usage during focus mode only when duration exceeds 120s threshold.",
                1, 1, 120, 3, "WARN", "WARN", 10, "MEDIUM",
                json.dumps(["cmd.exe", "powershell.exe", "windowsterminal.exe", "bash.exe", "mintty.exe"]),
                json.dumps([])
            ),
            (
                "blocked-apps",
                "BLOCKED_APPS",
                "Explicit Blocked Applications",
                "Explicit owner-configured blacklist of blocked applications.",
                1, 0, 0, 1, "BLOCK", "BLOCK", 5, "HIGH",
                json.dumps([]),
                json.dumps([])
            ),
            (
                "focus-bypass",
                "FOCUS_MODE_BYPASS",
                "Repeated Focus Mode Bypass Attempts",
                "Detects repeated attempts to relaunch blocked applications or bypass focus mode controls.",
                1, 1, 0, 2, "BLOCK", "SLEEP", 10, "HIGH",
                json.dumps([]),
                json.dumps([])
            ),
            (
                "sensitive-topics",
                "SENSITIVE_TOPICS",
                "Sensitive Topic Detection",
                "Optional owner-configured safety topic filter (disabled by default, no keyloggers).",
                0, 0, 0, 3, "WARN", "WARN", 10, "LOW",
                json.dumps([]),
                json.dumps([])
            )
        ]

        for p in default_prod_policies:
            cursor.execute("""
            INSERT OR IGNORE INTO sec_productivity_policies (
                policy_id, category, name, description, enabled, focus_only,
                min_duration_seconds, max_violations_before_escalation, default_action,
                escalation_action, grace_period_seconds, risk_level, match_apps_json,
                match_domains_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*p, now, now))

        # 4. Default High-Confidence Security Policies
        default_sec_policies = [
            (
                "malware-protection",
                "MALWARE_ACTIVITY",
                "Malware & Malicious Software Protection",
                "Detects high-confidence malicious payload execution and persistence indicators.",
                1, "BLOCK", "CRITICAL", 1,
                json.dumps({"block_on_detection": True, "alert_owner": True})
            ),
            (
                "unauthorized-hacking",
                "UNAUTHORIZED_HACKING",
                "Unauthorized Attack & Exploitation Attempts",
                "Detects high-confidence attack attempts outside of AUTHORIZED_SECURITY_LABS.",
                1, "BLOCK", "HIGH", 1,
                json.dumps({"exempt_whitelisted_labs": True})
            ),
            (
                "security-tampering",
                "SECURITY_TAMPERING",
                "Orian Security & Laptop Agent Anti-Tampering",
                "Detects attempts to disable Orian security services, alter gateway, or kill laptop agent.",
                1, "BLOCK", "CRITICAL", 0,
                json.dumps({"require_owner_auth": True, "security_alert": True, "auto_sleep": False})
            ),
            (
                "protected-data",
                "PROTECTED_DATA_ACCESS",
                "Unauthorized Protected Resource Access",
                "Detects unauthorized access attempts to credentials, keys, or foreign user data.",
                1, "BLOCK", "CRITICAL", 0,
                json.dumps({"alert_owner": True})
            ),
            (
                "illegal-activity",
                "ILLEGAL_ACTIVITY",
                "Owner Configured Safety Policy",
                "Explicit high-confidence safety policy events.",
                1, "BLOCK", "HIGH", 0,
                json.dumps({"privacy_mode": True})
            )
        ]

        for sp in default_sec_policies:
            cursor.execute("""
            INSERT OR IGNORE INTO sec_security_policies (
                policy_id, category, name, description, enabled, default_action,
                risk_level, allow_labs_whitelist, rules_json, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (*sp, now, now))

        conn.commit()
        conn.close()

    # -------------------------------------------------------------------------
    # LAPTOP DEVICES CRUD
    # -------------------------------------------------------------------------
    def register_device(self, device_id: str, device_name: str, owner_id: str, auth_token_hash: str, pairing_code: str, agent_version: str = "1.0.0") -> LaptopDevice:
        conn = self.get_connection()
        cur = conn.cursor()
        now = time.time()
        cur.execute("""
        INSERT INTO sec_laptop_devices (
            device_id, device_name, agent_version, owner_id, auth_token_hash,
            status, pairing_code, revoked, created_at, last_seen, metadata_json
        ) VALUES (?, ?, ?, ?, ?, 'PAIRING', ?, 0, ?, ?, '{}')
        ON CONFLICT(device_id) DO UPDATE SET
            device_name=excluded.device_name,
            agent_version=excluded.agent_version,
            auth_token_hash=excluded.auth_token_hash,
            pairing_code=excluded.pairing_code,
            last_seen=excluded.last_seen
        """, (device_id, device_name, agent_version, owner_id, auth_token_hash, pairing_code, now, now))
        conn.commit()
        conn.close()
        return self.get_device(device_id)

    def get_device(self, device_id: str) -> Optional[LaptopDevice]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_laptop_devices WHERE device_id = ?", (device_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return LaptopDevice(
            device_id=row["device_id"],
            device_name=row["device_name"],
            agent_version=row["agent_version"],
            owner_id=row["owner_id"],
            auth_token_hash=row["auth_token_hash"],
            status=DeviceStatus(row["status"]),
            pairing_code=row["pairing_code"],
            revoked=bool(row["revoked"]),
            created_at=row["created_at"],
            last_seen=row["last_seen"],
            metadata_json=json.loads(row["metadata_json"] or "{}")
        )

    def list_devices(self) -> List[LaptopDevice]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_laptop_devices ORDER BY created_at DESC")
        rows = cur.fetchall()
        conn.close()
        devices = []
        for row in rows:
            devices.append(LaptopDevice(
                device_id=row["device_id"],
                device_name=row["device_name"],
                agent_version=row["agent_version"],
                owner_id=row["owner_id"],
                auth_token_hash=row["auth_token_hash"],
                status=DeviceStatus(row["status"]),
                pairing_code=row["pairing_code"],
                revoked=bool(row["revoked"]),
                created_at=row["created_at"],
                last_seen=row["last_seen"],
                metadata_json=json.loads(row["metadata_json"] or "{}")
            ))
        return devices

    def update_device_status(self, device_id: str, status: DeviceStatus, revoked: Optional[bool] = None) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        now = time.time()
        if revoked is not None:
            cur.execute("""
            UPDATE sec_laptop_devices
            SET status = ?, revoked = ?, last_seen = ?
            WHERE device_id = ?
            """, (status.value, 1 if revoked else 0, now, device_id))
        else:
            cur.execute("""
            UPDATE sec_laptop_devices
            SET status = ?, last_seen = ?
            WHERE device_id = ?
            """, (status.value, now, device_id))
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    def update_device_heartbeat(self, device_id: str, agent_version: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        now = time.time()
        if metadata:
            meta_json = json.dumps(metadata)
            cur.execute("""
            UPDATE sec_laptop_devices
            SET last_seen = ?, agent_version = COALESCE(?, agent_version), metadata_json = ?
            WHERE device_id = ? AND revoked = 0
            """, (now, agent_version, meta_json, device_id))
        else:
            cur.execute("""
            UPDATE sec_laptop_devices
            SET last_seen = ?, agent_version = COALESCE(?, agent_version)
            WHERE device_id = ? AND revoked = 0
            """, (now, agent_version, device_id))
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    # -------------------------------------------------------------------------
    # PRODUCTIVITY POLICIES CRUD
    # -------------------------------------------------------------------------
    def get_productivity_policy(self, policy_id: str) -> Optional[ProductivityPolicy]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_productivity_policies WHERE policy_id = ?", (policy_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return ProductivityPolicy(
            policy_id=row["policy_id"],
            category=ProductivityCategory(row["category"]),
            name=row["name"],
            description=row["description"] or "",
            enabled=bool(row["enabled"]),
            focus_only=bool(row["focus_only"]),
            min_duration_seconds=row["min_duration_seconds"],
            max_violations_before_escalation=row["max_violations_before_escalation"],
            default_action=EnforcementAction(row["default_action"]),
            escalation_action=EnforcementAction(row["escalation_action"]),
            grace_period_seconds=row["grace_period_seconds"],
            risk_level=ProtectionRiskLevel(row["risk_level"]),
            match_apps=json.loads(row["match_apps_json"] or "[]"),
            match_domains=json.loads(row["match_domains_json"] or "[]"),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def list_productivity_policies(self) -> List[ProductivityPolicy]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_productivity_policies ORDER BY category")
        rows = cur.fetchall()
        conn.close()
        policies = []
        for r in rows:
            policies.append(ProductivityPolicy(
                policy_id=r["policy_id"],
                category=ProductivityCategory(r["category"]),
                name=r["name"],
                description=r["description"] or "",
                enabled=bool(r["enabled"]),
                focus_only=bool(r["focus_only"]),
                min_duration_seconds=r["min_duration_seconds"],
                max_violations_before_escalation=r["max_violations_before_escalation"],
                default_action=EnforcementAction(r["default_action"]),
                escalation_action=EnforcementAction(r["escalation_action"]),
                grace_period_seconds=r["grace_period_seconds"],
                risk_level=ProtectionRiskLevel(r["risk_level"]),
                match_apps=json.loads(r["match_apps_json"] or "[]"),
                match_domains=json.loads(r["match_domains_json"] or "[]"),
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return policies

    def save_productivity_policy(self, policy: ProductivityPolicy) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        now = time.time()
        cur.execute("""
        INSERT INTO sec_productivity_policies (
            policy_id, category, name, description, enabled, focus_only,
            min_duration_seconds, max_violations_before_escalation, default_action,
            escalation_action, grace_period_seconds, risk_level, match_apps_json,
            match_domains_json, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(policy_id) DO UPDATE SET
            category=excluded.category,
            name=excluded.name,
            description=excluded.description,
            enabled=excluded.enabled,
            focus_only=excluded.focus_only,
            min_duration_seconds=excluded.min_duration_seconds,
            max_violations_before_escalation=excluded.max_violations_before_escalation,
            default_action=excluded.default_action,
            escalation_action=excluded.escalation_action,
            grace_period_seconds=excluded.grace_period_seconds,
            risk_level=excluded.risk_level,
            match_apps_json=excluded.match_apps_json,
            match_domains_json=excluded.match_domains_json,
            updated_at=excluded.updated_at
        """, (
            policy.policy_id, policy.category.value, policy.name, policy.description,
            1 if policy.enabled else 0, 1 if policy.focus_only else 0,
            policy.min_duration_seconds, policy.max_violations_before_escalation,
            policy.default_action.value, policy.escalation_action.value,
            policy.grace_period_seconds, policy.risk_level.value,
            json.dumps(policy.match_apps), json.dumps(policy.match_domains),
            policy.created_at, now
        ))
        conn.commit()
        conn.close()
        return True

    # -------------------------------------------------------------------------
    # SECURITY POLICIES CRUD
    # -------------------------------------------------------------------------
    def get_security_policy(self, policy_id: str) -> Optional[SecurityPolicy]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_security_policies WHERE policy_id = ?", (policy_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return SecurityPolicy(
            policy_id=row["policy_id"],
            category=SecurityCategory(row["category"]),
            name=row["name"],
            description=row["description"] or "",
            enabled=bool(row["enabled"]),
            default_action=EnforcementAction(row["default_action"]),
            risk_level=ProtectionRiskLevel(row["risk_level"]),
            allow_labs_whitelist=bool(row["allow_labs_whitelist"]),
            rules_json=json.loads(row["rules_json"] or "{}"),
            created_at=row["created_at"],
            updated_at=row["updated_at"]
        )

    def list_security_policies(self) -> List[SecurityPolicy]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_security_policies ORDER BY category")
        rows = cur.fetchall()
        conn.close()
        policies = []
        for r in rows:
            policies.append(SecurityPolicy(
                policy_id=r["policy_id"],
                category=SecurityCategory(r["category"]),
                name=r["name"],
                description=r["description"] or "",
                enabled=bool(r["enabled"]),
                default_action=EnforcementAction(r["default_action"]),
                risk_level=ProtectionRiskLevel(r["risk_level"]),
                allow_labs_whitelist=bool(r["allow_labs_whitelist"]),
                rules_json=json.loads(r["rules_json"] or "{}"),
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            ))
        return policies

    # -------------------------------------------------------------------------
    # RULES (WHITELIST / BLACKLIST) CRUD
    # -------------------------------------------------------------------------
    def list_activity_rules(self, rule_type: Optional[RuleType] = None) -> List[ActivityRule]:
        conn = self.get_connection()
        cur = conn.cursor()
        if rule_type:
            cur.execute("SELECT * FROM sec_activity_rules WHERE rule_type = ?", (rule_type.value,))
        else:
            cur.execute("SELECT * FROM sec_activity_rules ORDER BY rule_type, category")
        rows = cur.fetchall()
        conn.close()
        rules = []
        for r in rows:
            rules.append(ActivityRule(
                rule_id=r["rule_id"],
                rule_type=RuleType(r["rule_type"]),
                category=r["category"],
                target=r["target"],
                description=r["description"] or "",
                created_at=r["created_at"]
            ))
        return rules

    def add_activity_rule(self, rule: ActivityRule) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO sec_activity_rules (rule_id, rule_type, category, target, description, created_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(rule_id) DO UPDATE SET
            rule_type=excluded.rule_type,
            category=excluded.category,
            target=excluded.target,
            description=excluded.description
        """, (rule.rule_id, rule.rule_type.value, rule.category, rule.target.lower(), rule.description, rule.created_at))
        conn.commit()
        conn.close()
        return True

    def delete_activity_rule(self, rule_id: str) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM sec_activity_rules WHERE rule_id = ?", (rule_id,))
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    # -------------------------------------------------------------------------
    # FOCUS SESSIONS CRUD
    # -------------------------------------------------------------------------
    def get_active_focus_session(self) -> Optional[FocusSession]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_focus_sessions WHERE is_active = 1 ORDER BY start_time DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return FocusSession(
            session_id=row["session_id"],
            mode=FocusMode(row["mode"]),
            is_active=bool(row["is_active"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
            schedule_start=row["schedule_start"] or "09:00",
            schedule_end=row["schedule_end"] or "18:00",
            schedule_days=json.loads(row["schedule_days_json"] or '["mon","tue","wed","thu","fri"]'),
            created_by=row["created_by"] or "system"
        )

    def set_focus_session(self, session: FocusSession) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        # Deactivate previous active sessions
        cur.execute("UPDATE sec_focus_sessions SET is_active = 0, end_time = ? WHERE is_active = 1", (session.start_time,))
        cur.execute("""
        INSERT INTO sec_focus_sessions (
            session_id, mode, is_active, start_time, end_time, schedule_start, schedule_end, schedule_days_json, created_by
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            mode=excluded.mode,
            is_active=excluded.is_active,
            start_time=excluded.start_time,
            end_time=excluded.end_time,
            schedule_start=excluded.schedule_start,
            schedule_end=excluded.schedule_end,
            schedule_days_json=excluded.schedule_days_json
        """, (
            session.session_id, session.mode.value, 1 if session.is_active else 0,
            session.start_time, session.end_time, session.schedule_start,
            session.schedule_end, json.dumps(session.schedule_days), session.created_by
        ))
        conn.commit()
        conn.close()
        return True

    # -------------------------------------------------------------------------
    # ACTIVITY EVENTS & VIOLATIONS CRUD
    # -------------------------------------------------------------------------
    def log_activity_event(self, event: ActivityEvent) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO sec_activity_events (
            event_id, device_id, category, application, process_name,
            window_title_sanitized, duration_seconds, timestamp, policy_id,
            risk_level, action_taken, matched_rule
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.device_id, event.category, event.application,
            event.process_name, event.window_title_sanitized, event.duration_seconds,
            event.timestamp, event.policy_id, event.risk_level.value,
            event.action_taken.value, event.matched_rule
        ))
        conn.commit()
        conn.close()
        return True

    def record_violation(self, violation: PolicyViolation) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO sec_policy_violations (
            violation_id, event_id, device_id, policy_id, violation_count,
            risk_level, action_enforced, warning_issued_at, grace_period_expires_at,
            overridden, overridden_by, status, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            violation.violation_id, violation.event_id, violation.device_id,
            violation.policy_id, violation.violation_count, violation.risk_level.value,
            violation.action_enforced.value, violation.warning_issued_at,
            violation.grace_period_expires_at, 1 if violation.overridden else 0,
            violation.overridden_by, violation.status, violation.created_at
        ))
        conn.commit()
        conn.close()
        return True

    def get_active_violation(self, violation_id: str) -> Optional[PolicyViolation]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_policy_violations WHERE violation_id = ?", (violation_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return PolicyViolation(
            violation_id=row["violation_id"],
            event_id=row["event_id"],
            device_id=row["device_id"],
            policy_id=row["policy_id"],
            violation_count=row["violation_count"],
            risk_level=ProtectionRiskLevel(row["risk_level"]),
            action_enforced=EnforcementAction(row["action_enforced"]),
            warning_issued_at=row["warning_issued_at"],
            grace_period_expires_at=row["grace_period_expires_at"],
            overridden=bool(row["overridden"]),
            overridden_by=row["overridden_by"],
            status=row["status"],
            created_at=row["created_at"]
        )

    def update_violation_status(self, violation_id: str, status: str, overridden_by: Optional[str] = None) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        overridden_int = 1 if status == "OVERRIDDEN" else 0
        cur.execute("""
        UPDATE sec_policy_violations
        SET status = ?, overridden = CASE WHEN ? = 1 THEN 1 ELSE overridden END,
            overridden_by = COALESCE(?, overridden_by)
        WHERE violation_id = ?
        """, (status, overridden_int, overridden_by, violation_id))
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    def get_violation_count_today(self, device_id: str, policy_id: str) -> int:
        conn = self.get_connection()
        cur = conn.cursor()
        start_of_day = time.time() - (time.time() % 86400)
        cur.execute("""
        SELECT COUNT(*) as cnt FROM sec_policy_violations
        WHERE device_id = ? AND policy_id = ? AND created_at >= ?
        """, (device_id, policy_id, start_of_day))
        row = cur.fetchone()
        conn.close()
        return row["cnt"] if row else 0

    def record_override(self, override: PolicyOverride) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO sec_policy_overrides (
            override_id, violation_id, user_id, policy_id, reason, risk_level, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            override.override_id, override.violation_id, override.user_id,
            override.policy_id, override.reason, override.risk_level.value, override.timestamp
        ))
        conn.commit()
        conn.close()
        return True

    # -------------------------------------------------------------------------
    # LAPTOP COMMANDS CRUD (REPLAY PROTECTION)
    # -------------------------------------------------------------------------
    def record_command(self, command: LaptopCommand) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        INSERT INTO sec_laptop_commands (
            request_id, device_id, command, policy_id, reason, timestamp, expires_at, signature, status, result_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            command.request_id, command.device_id, command.command, command.policy_id,
            command.reason, command.timestamp, command.expires_at, command.signature,
            command.status, json.dumps(command.result_json)
        ))
        conn.commit()
        conn.close()
        return True

    def get_command(self, request_id: str) -> Optional[LaptopCommand]:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM sec_laptop_commands WHERE request_id = ?", (request_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return LaptopCommand(
            request_id=row["request_id"],
            device_id=row["device_id"],
            command=row["command"],
            policy_id=row["policy_id"],
            reason=row["reason"] or "",
            timestamp=row["timestamp"],
            expires_at=row["expires_at"],
            signature=row["signature"],
            status=row["status"],
            result_json=json.loads(row["result_json"] or "{}")
        )

    def update_command_result(self, request_id: str, status: str, result: Dict[str, Any]) -> bool:
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("""
        UPDATE sec_laptop_commands
        SET status = ?, result_json = ?
        WHERE request_id = ?
        """, (status, json.dumps(result), request_id))
        conn.commit()
        rowcount = cur.rowcount
        conn.close()
        return rowcount > 0

    def query_metrics_today(self, device_id: Optional[str] = None) -> Dict[str, Any]:
        conn = self.get_connection()
        cur = conn.cursor()
        start_of_day = time.time() - (time.time() % 86400)

        d_filter = " AND device_id = ?" if device_id else ""
        params = (start_of_day, device_id) if device_id else (start_of_day,)

        cur.execute(f"SELECT COUNT(*) as c FROM sec_activity_events WHERE timestamp >= ? AND action_taken = 'WARN' {d_filter}", params)
        warnings_count = cur.fetchone()["c"]

        cur.execute(f"SELECT COUNT(*) as c FROM sec_policy_violations WHERE created_at >= ? {d_filter}", params)
        violations_count = cur.fetchone()["c"]

        cur.execute(f"SELECT COUNT(*) as c FROM sec_policy_overrides WHERE timestamp >= ? {d_filter.replace('device_id', 'user_id') if False else ''}", (start_of_day,))
        overrides_count = cur.fetchone()["c"]

        cur.execute(f"SELECT COUNT(*) as c FROM sec_laptop_commands WHERE timestamp >= ? AND command = 'SLEEP' AND status = 'EXECUTED' {d_filter}", params)
        sleep_actions_count = cur.fetchone()["c"]

        cur.execute(f"SELECT COUNT(*) as c FROM sec_activity_events WHERE timestamp >= ? AND category LIKE 'SECURITY%' {d_filter}", params)
        security_events_count = cur.fetchone()["c"]

        conn.close()

        return {
            "warnings_today": warnings_count,
            "violations_today": violations_count,
            "overrides_today": overrides_count,
            "sleep_actions_today": sleep_actions_count,
            "security_events_today": security_events_count
        }

protection_db = ProtectionDatabase()
