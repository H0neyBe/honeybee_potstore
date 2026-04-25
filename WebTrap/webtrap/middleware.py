"""Per-request capture middleware.

Builds the ``request_ctx`` dictionary every route handler attaches to
its events: source IP, port, headers, body, UA fingerprint, behavioural
session snapshot and any payload tags detected.
"""

from __future__ import annotations

import logging
from typing import Any, Dict

from flask import Flask, g, request

from .config import WebTrapConfig
from .events import (
    CATEGORY_PROBE,
    SEVERITY_LOW,
    EventRecorder,
)
from .fingerprint import classify_payload, classify_user_agent
from .session import SessionTracker

log = logging.getLogger("webtrap.middleware")


def _client_ip(cfg: WebTrapConfig) -> str:
    if cfg.trust_proxy_headers:
        for hdr in ("CF-Connecting-IP", "X-Real-IP", "X-Forwarded-For"):
            v = request.headers.get(hdr)
            if v:
                return v.split(",")[0].strip()
    return request.remote_addr or "0.0.0.0"


def _capture_body(cfg: WebTrapConfig) -> str:
    try:
        raw = request.get_data(cache=True, as_text=False) or b""
    except Exception:
        return ""
    if len(raw) > cfg.max_body_capture:
        raw = raw[: cfg.max_body_capture]
    try:
        return raw.decode("utf-8", errors="replace")
    except Exception:
        return raw.hex()


def install_middleware(app: Flask, cfg: WebTrapConfig, recorder: EventRecorder) -> None:
    tracker = SessionTracker()

    @app.before_request
    def _before():  # type: ignore[unused-variable]
        ip = _client_ip(cfg)
        ua = request.headers.get("User-Agent", "")
        ua_info = classify_user_agent(ua)

        cookie_id = request.cookies.get("PHPSESSID") or request.cookies.get("session")
        sess = tracker.touch(ip, cookie_id, request.path, request.method)

        body = _capture_body(cfg)
        qs = request.query_string.decode("utf-8", errors="replace")
        tags = classify_payload(request.path, qs, body)

        headers: Dict[str, str] = {}
        if cfg.capture_headers:
            for k, v in request.headers.items():
                if k.lower() == "cookie" and not cfg.capture_cookies:
                    continue
                headers[k] = v

        ctx: Dict[str, Any] = {
            "src_ip": ip,
            "src_port": request.environ.get("REMOTE_PORT") or 0,
            "dst_port": cfg.bind_port,
            "user_agent": ua,
            "request_uri": request.full_path if request.query_string else request.path,
            "request_method": request.method,
            "request_headers": headers,
            "request_body": body,
            "request_body_size": len(body),
            "ua_category": ua_info["ua_category"],
            "ua_tool": ua_info["ua_tool"],
            "ua_fingerprint": ua_info["ua_fingerprint"],
            "payload_tags": tags,
            "session": sess.snapshot(),
        }
        g.ctx = ctx
        g.recorder = recorder
        g.config = cfg

    @app.after_request
    def _after(resp):  # type: ignore[unused-variable]
        # Server banner deception - always present plausible headers.
        resp.headers["Server"] = cfg.fake_server_banner
        resp.headers["X-Powered-By"] = f"PHP/{cfg.fake_php_version}"
        resp.headers.pop("X-Frame-Options", None)

        # Catch-all probe event for paths that no specific route logged.
        # Routes that fired their own event set g.handled = True.
        if not getattr(g, "handled", False) and getattr(g, "ctx", None):
            severity = SEVERITY_LOW
            if g.ctx.get("payload_tags"):
                from .events import SEVERITY_HIGH
                severity = SEVERITY_HIGH
            recorder.record(
                eventid="webtrap.request",
                category=CATEGORY_PROBE,
                severity=severity,
                message=f"{request.method} {request.path}",
                request_ctx=g.ctx,
                extra={"response_status": resp.status_code},
            )
        return resp
