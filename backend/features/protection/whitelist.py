import ipaddress
import logging
from typing import Set, Tuple, Optional, List
from .models import RuleType, WhitelistCategory, ActivityRule
from .database import protection_db

logger = logging.getLogger("orian.protection.whitelist")

class OrianActivityWhitelist:
    """Enterprise Activity Whitelist Engine ensuring productivity and developer tools, cybersecurity labs, and system utilities are never mistakenly penalized."""

    def __init__(self):
        self.db = protection_db
        self.always_allowed: Set[str] = set()
        self.dev_tools: Set[str] = set()
        self.focus_allowed: Set[str] = set()
        self.security_labs: Set[str] = set()
        self.security_lab_subnets: List[ipaddress.IPv4Network] = []
        self.reload_rules()

    def reload_rules(self):
        """Loads all whitelist rules from SQLite into memory for sub-millisecond lookups."""
        rules = self.db.list_activity_rules(rule_type=RuleType.WHITELIST)

        always = set()
        dev = set()
        focus = set()
        labs = set()
        subnets = []

        for r in rules:
            target = r.target.lower().strip()
            if r.category == WhitelistCategory.ALWAYS_ALLOWED.value:
                always.add(target)
            elif r.category == WhitelistCategory.AUTHORIZED_DEVELOPMENT_TOOL.value:
                dev.add(target)
            elif r.category == WhitelistCategory.ALLOWED_DURING_FOCUS.value:
                focus.add(target)
            elif r.category == WhitelistCategory.AUTHORIZED_SECURITY_LAB.value:
                labs.add(target)
                if "/" in target:
                    try:
                        subnets.append(ipaddress.ip_network(target, strict=False))
                    except Exception:
                        pass

        self.always_allowed = always
        self.dev_tools = dev
        self.focus_allowed = focus
        self.security_labs = labs
        self.security_lab_subnets = subnets
        logger.debug(f"Loaded {len(rules)} whitelist rules into memory.")

    def is_always_allowed(self, app_or_proc: str) -> bool:
        norm = app_or_proc.lower().strip()
        # Direct match or basename match
        if norm in self.always_allowed or norm in self.dev_tools:
            return True
        for item in self.always_allowed | self.dev_tools:
            if norm.endswith(item) or item in norm:
                return True
        return False

    def is_allowed_during_focus(self, app_or_proc: str, domain: Optional[str] = None) -> bool:
        if self.is_always_allowed(app_or_proc):
            return True
        norm_app = app_or_proc.lower().strip()
        if norm_app in self.focus_allowed:
            return True
        if domain:
            norm_dom = domain.lower().strip()
            if norm_dom in self.focus_allowed:
                return True
        return False

    def is_authorized_security_lab(self, target_host_or_ip: str) -> bool:
        norm = target_host_or_ip.lower().strip()
        if norm in self.security_labs:
            return True
        # Check IP subnet match
        try:
            ip_obj = ipaddress.ip_address(norm)
            for net in self.security_lab_subnets:
                if ip_obj in net:
                    return True
        except ValueError:
            pass

        # Local hostnames
        if norm in ["localhost", "127.0.0.1", "::1", "0.0.0.0"] or norm.endswith(".local") or norm.endswith(".internal"):
            return True
        return False

    def evaluate_whitelist(
        self,
        process_name: str,
        application_name: str = "",
        domain: Optional[str] = None,
        is_focus_active: bool = False,
        is_security_action: bool = False,
        target_network: Optional[str] = None
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """Evaluates whether an activity or cybersecurity action is whitelisted.
        Returns: (is_whitelisted, category_name, rule_description)
        """
        p_name = process_name.lower().strip()
        a_name = application_name.lower().strip()

        # 1. Check Always Allowed (VS Code, Python, Git, Node.js, Android Studio, Docker, Notepad, etc.)
        if self.is_always_allowed(p_name):
            return True, WhitelistCategory.ALWAYS_ALLOWED.value, f"Process '{process_name}' is in ALWAYS_ALLOWED whitelist"
        if a_name and self.is_always_allowed(a_name):
            return True, WhitelistCategory.ALWAYS_ALLOWED.value, f"Application '{application_name}' is in ALWAYS_ALLOWED whitelist"

        # 2. Check Authorized Security Lab if security/network action
        if is_security_action or target_network:
            check_target = target_network or domain or p_name
            if self.is_authorized_security_lab(check_target):
                return True, WhitelistCategory.AUTHORIZED_SECURITY_LAB.value, f"Target '{check_target}' is an AUTHORIZED_SECURITY_LAB"

        # 3. Check Focus Allowed
        if is_focus_active:
            if self.is_allowed_during_focus(p_name, domain):
                return True, WhitelistCategory.ALLOWED_DURING_FOCUS.value, f"Process/Domain is in ALLOWED_DURING_FOCUS whitelist"

        return False, None, None

activity_whitelist = OrianActivityWhitelist()
