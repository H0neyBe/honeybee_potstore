"""WebTrap configuration loader.

Configuration sources (later overrides earlier):
1. Built-in defaults
2. YAML file pointed at by ``WEBTRAP_CONFIG`` env var (or ``./config.yaml``)
3. Environment variables (``HONEYBEE_*`` / ``WEBTRAP_*``)
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, Optional


def _envbool(key: str, default: bool) -> bool:
    val = os.environ.get(key)
    if val is None:
        return default
    return val.strip().lower() not in ("0", "false", "no", "off", "")


def _envint(key: str, default: int) -> int:
    val = os.environ.get(key)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass
class WebTrapConfig:
    # HoneyBee integration
    pot_id: str = "webtrap-01"
    pot_type: str = "webtrap"
    honeybee_host: str = "127.0.0.1"
    honeybee_port: int = 9100
    honeybee_enable: bool = True
    honeybee_timeout: float = 5.0

    # Listener
    bind_host: str = "0.0.0.0"
    bind_port: int = 8088
    tls_cert: Optional[str] = None
    tls_key: Optional[str] = None

    # Logging
    enable_file_log: bool = True
    log_file: str = "./logs/webtrap.log"
    log_level: str = "INFO"

    # Capture limits
    max_body_capture: int = 65536  # bytes captured per request
    capture_headers: bool = True
    capture_cookies: bool = True

    # Deception
    fake_hostname: str = "intranet.corp.local"
    fake_server_banner: str = "Apache/2.4.41 (Ubuntu)"
    fake_php_version: str = "7.4.3"
    # Optional: rare "successful" login to lure attackers deeper.  The
    # credentials are only known to the honeypot operator and never accept
    # any real traffic.
    canary_username: str = ""
    canary_password: str = ""

    # Trusted proxy / IP detection
    trust_proxy_headers: bool = True

    extra: Dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    @classmethod
    def load(cls, path: Optional[str] = None) -> "WebTrapConfig":
        cfg = cls()

        # YAML file
        yaml_path = path or os.environ.get("WEBTRAP_CONFIG") or "config.yaml"
        if yaml_path and Path(yaml_path).is_file():
            try:
                import yaml  # type: ignore
                with open(yaml_path, "r", encoding="utf-8") as fh:
                    data = yaml.safe_load(fh) or {}
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
                    else:
                        cfg.extra[k] = v
            except ImportError:
                # PyYAML is optional - fall back to env-only config.
                pass

        # Environment overrides
        cfg.pot_id = os.environ.get("HONEYBEE_POT_ID", cfg.pot_id)
        cfg.honeybee_host = os.environ.get("HONEYBEE_HOST", cfg.honeybee_host)
        cfg.honeybee_port = _envint("HONEYBEE_PORT", cfg.honeybee_port)
        cfg.honeybee_enable = _envbool("HONEYBEE_ENABLE", cfg.honeybee_enable)
        cfg.bind_host = os.environ.get("WEBTRAP_BIND_HOST", cfg.bind_host)
        cfg.bind_port = _envint("WEBTRAP_BIND_PORT", cfg.bind_port)
        cfg.tls_cert = os.environ.get("WEBTRAP_TLS_CERT", cfg.tls_cert)
        cfg.tls_key = os.environ.get("WEBTRAP_TLS_KEY", cfg.tls_key)
        cfg.enable_file_log = _envbool("HONEYBEE_ENABLE_FILE_LOG", cfg.enable_file_log)
        cfg.log_file = os.environ.get("HONEYBEE_LOG_FILE", cfg.log_file)
        cfg.log_level = os.environ.get("WEBTRAP_LOG_LEVEL", cfg.log_level)
        cfg.fake_hostname = os.environ.get("WEBTRAP_FAKE_HOSTNAME", cfg.fake_hostname)
        cfg.canary_username = os.environ.get("WEBTRAP_CANARY_USER", cfg.canary_username)
        cfg.canary_password = os.environ.get("WEBTRAP_CANARY_PASS", cfg.canary_password)
        return cfg

    def as_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # Don't leak canary password in diagnostic dumps.
        d.pop("canary_password", None)
        return d
