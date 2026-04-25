"""Central event recorder.

Builds the canonical HoneyBee event envelope, mirrors it to a local
JSON-line file (the durable record), and hands it to the TCP forwarder.
The schema matches the existing pots so the HoneyBee Node parses our
events with no changes to the listener.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from typing import Any, Dict, Optional

from .config import WebTrapConfig
from .forwarder import HoneyBeeForwarder

log = logging.getLogger("webtrap.events")


# Public categories used by HoneyBee Core for grouping / dashboarding.
CATEGORY_AUTH = "authentication"
CATEGORY_RECON = "reconnaissance"
CATEGORY_EXPLOIT = "exploitation"
CATEGORY_UPLOAD = "upload"
CATEGORY_INFOLEAK = "info-leak"
CATEGORY_PROBE = "probe"

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"
SEVERITY_CRITICAL = "critical"


class EventRecorder:
    def __init__(self, config: WebTrapConfig, forwarder: Optional[HoneyBeeForwarder] = None) -> None:
        self.config = config
        self.forwarder = forwarder or HoneyBeeForwarder(
            host=config.honeybee_host,
            port=config.honeybee_port,
            timeout=config.honeybee_timeout,
            enabled=config.honeybee_enable,
        )
        self._file_lock = threading.Lock()
        self._fh = None
        if config.enable_file_log:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(config.log_file)) or ".", exist_ok=True)
                self._fh = open(config.log_file, "a", encoding="utf-8")
            except OSError as exc:
                log.error("cannot open log file %s: %s", config.log_file, exc)

    # ------------------------------------------------------------------
    def record(
        self,
        eventid: str,
        category: str,
        severity: str,
        message: str,
        request_ctx: Dict[str, Any],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        event: Dict[str, Any] = {
            "eventid": eventid,
            "pot_id": self.config.pot_id,
            "pot_type": self.config.pot_type,
            "timestamp": int(time.time()),
            "honeybee_category": category,
            "honeybee_severity": severity,
            "message": message,
        }
        # Standard request envelope.  Keys match HonnyPotter where they
        # overlap (src_ip, src_port, dst_port, user_agent, request_uri,
        # request_method) so the same Node listener parses both.
        event.update(request_ctx)
        if extra:
            event.update(extra)

        # Local file log first (durable) then forward.
        if self._fh:
            try:
                with self._file_lock:
                    self._fh.write(json.dumps(event, default=str) + "\n")
                    self._fh.flush()
            except OSError as exc:
                log.error("log write failed: %s", exc)

        self.forwarder.send(event)
        return event

    def close(self) -> None:
        try:
            if self._fh:
                self._fh.close()
        finally:
            self.forwarder.stop()
