"""Lightweight User-Agent and request fingerprinting.

The goal isn't perfect classification - it's giving the analyst a fast
hint so noisy automated scanners can be triaged from interactive
attackers.  Heuristics intentionally err on the side of "tool" because
honeypot traffic is overwhelmingly automated.
"""

from __future__ import annotations

import hashlib
import re
from typing import Dict

# Well-known offensive / scanning tools.  Keep ordered roughly from most
# to least specific so the first match wins.
_TOOL_PATTERNS = [
    ("sqlmap", "sqlmap"),
    ("nikto", "nikto"),
    ("nmap", "nmap"),
    ("masscan", "masscan"),
    ("zgrab", "zgrab"),
    ("nuclei", "nuclei"),
    ("acunetix", "acunetix"),
    ("burpsuite", "burp"),
    ("burp", "burp"),
    ("dirbuster", "dirbuster"),
    ("gobuster", "gobuster"),
    ("ffuf", "ffuf"),
    ("wpscan", "wpscan"),
    ("hydra", "hydra"),
    ("metasploit", "metasploit"),
    ("python-requests", "python-requests"),
    ("python/", "python"),
    ("go-http-client", "go-http"),
    ("curl/", "curl"),
    ("wget", "wget"),
    ("libwww-perl", "libwww-perl"),
    ("httpx", "httpx"),
]

_BOT_HINTS = ("bot", "crawler", "spider", "scan")


def classify_user_agent(ua: str) -> Dict[str, str]:
    """Return a dict with classification + stable fingerprint hash."""
    ua_l = (ua or "").lower().strip()
    category = "browser"
    tool = ""

    if not ua_l:
        category = "empty"
    else:
        for needle, name in _TOOL_PATTERNS:
            if needle in ua_l:
                category = "tool"
                tool = name
                break
        else:
            if any(h in ua_l for h in _BOT_HINTS):
                category = "bot"
            elif "mozilla" not in ua_l:
                category = "non-browser"

    # Short stable fingerprint (8 hex = 32 bits) - enough to group
    # repeat visitors without storing the full UA in every alert.
    fp = hashlib.sha256(ua_l.encode("utf-8", "replace")).hexdigest()[:16]
    return {"ua_category": category, "ua_tool": tool, "ua_fingerprint": fp}


# Cheap heuristics that flag obvious attack payloads in the request
# path, query string or body.  Returns a list of tag strings.
_PAYLOAD_PATTERNS = [
    ("sqli", re.compile(r"(union\s+select|select\s+.*from|sleep\(|benchmark\(|or\s+1=1|--\s|/\*\*/)", re.I)),
    ("xss", re.compile(r"(<script|javascript:|onerror=|onload=|<svg)", re.I)),
    ("path-traversal", re.compile(r"(\.\./|\.\.\\|/etc/passwd|/proc/self|c:\\windows)", re.I)),
    ("rce", re.compile(r"(;\s*(?:cat|wget|curl|nc|bash|sh)\s|`.*`|\$\(.*\)|\|\s*(?:nc|bash|sh)\b)", re.I)),
    ("lfi", re.compile(r"(php://|file://|expect://|data://)", re.I)),
    ("ssrf", re.compile(r"(169\.254\.169\.254|metadata\.google|localhost:\d+)", re.I)),
    ("log4shell", re.compile(r"\$\{jndi:", re.I)),
    ("ssti", re.compile(r"(\{\{.*\}\}|\{%.*%\})", re.I)),
    ("webshell", re.compile(r"(c99|r57|wso|b374k|adminer|phpinfo\(\))", re.I)),
]


def classify_payload(*samples: str) -> list:
    tags: list = []
    blob = "\n".join(s for s in samples if s)
    if not blob:
        return tags
    for tag, pat in _PAYLOAD_PATTERNS:
        if pat.search(blob):
            tags.append(tag)
    return tags
