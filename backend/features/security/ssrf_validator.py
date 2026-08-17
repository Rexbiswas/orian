import ipaddress
import urllib.parse
import socket
import logging
from typing import List, Optional

logger = logging.getLogger("orian.security.ssrf_validator")

FORBIDDEN_HOSTS = [
    "localhost",
    "127.0.0.1",
    "::1",
    "0.0.0.0",
    "169.254.169.254", # AWS/GCP/Azure Metadata Endpoint
    "metadata.google.internal",
    "100.100.100.200"
]

class SSRFValidator:
    """Enterprise Server-Side Request Forgery (SSRF) & Network Protection Validator preventing arbitrary loopback or cloud metadata probing."""

    def __init__(self, allow_local_iot: bool = True):
        self.allow_local_iot = allow_local_iot

    def validate_url(self, url_str: str, allow_private: bool = False) -> str:
        """Parses and validates destination URL against SSRF attack vectors."""
        if not url_str:
            raise ValueError("URL cannot be empty")

        parsed = urllib.parse.urlparse(url_str)
        scheme = parsed.scheme.lower()

        if scheme not in ["http", "https"]:
            raise PermissionError(f"URL scheme '{scheme}' is forbidden. Only HTTP and HTTPS are permitted.")

        hostname = parsed.hostname
        if not hostname:
            raise ValueError("URL must contain a valid hostname")

        host_lower = hostname.lower()

        # Check explicit forbidden hosts
        if host_lower in FORBIDDEN_HOSTS:
            if not allow_private:
                raise PermissionError(f"Access to internal network host '{hostname}' is blocked by SSRF policy.")

        # Resolve IP and check if private
        try:
            ip_str = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(ip_str)

            if ip_obj.is_loopback:
                if not allow_private:
                    raise PermissionError(f"Requests to loopback IP '{ip_str}' are strictly blocked.")

            if ip_obj.is_link_local or ip_str == "169.254.169.254":
                raise PermissionError(f"Requests to cloud metadata link-local address '{ip_str}' are strictly blocked.")

            if ip_obj.is_private and not allow_private:
                # Unless configured for local IoT subnet communication
                if not self.allow_local_iot:
                    raise PermissionError(f"Requests to private intranet IP '{ip_str}' are forbidden.")

        except socket.gaierror:
            logger.warning(f"Could not resolve host '{hostname}', proceeding with caution.")
        except PermissionError:
            raise
        except Exception as e:
            logger.error(f"SSRF validation exception: {e}")

        return url_str

ssrf_validator = SSRFValidator()
