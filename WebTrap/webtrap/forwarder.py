"""TCP JSON-line forwarder to a HoneyBee Node.

Mirrors the behaviour of HonnyPotter's ``honeybee-forwarder.php`` and
Cowrie's ``honeybee.py`` output plugin: each event is a single JSON
object terminated by ``\\n`` sent to ``127.0.0.1:9100``.

The forwarder is non-blocking from the request handler's point of view -
events are queued on an internal background worker thread so a slow Node
never stalls the honeypot or tips off the attacker via response delay.
"""

from __future__ import annotations

import json
import logging
import queue
import socket
import threading
import time
from typing import Any, Dict, Optional

log = logging.getLogger("webtrap.forwarder")


class HoneyBeeForwarder:
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 9100,
        timeout: float = 5.0,
        enabled: bool = True,
        max_queue: int = 4096,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.enabled = enabled
        self._q: "queue.Queue[Optional[Dict[str, Any]]]" = queue.Queue(maxsize=max_queue)
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        if enabled:
            self.start()

    # ------------------------------------------------------------------
    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._worker, name="webtrap-forwarder", daemon=True
        )
        self._thread.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop.set()
        try:
            self._q.put_nowait(None)
        except queue.Full:
            pass
        if self._thread:
            self._thread.join(timeout=timeout)

    # ------------------------------------------------------------------
    def send(self, event: Dict[str, Any]) -> bool:
        """Enqueue an event for forwarding.  Returns False if dropped."""
        if not self.enabled:
            return False
        try:
            self._q.put_nowait(event)
            return True
        except queue.Full:
            log.warning("event queue full - dropping event %s", event.get("eventid"))
            return False

    # ------------------------------------------------------------------
    def _worker(self) -> None:
        backoff = 1.0
        while not self._stop.is_set():
            try:
                event = self._q.get(timeout=1.0)
            except queue.Empty:
                continue
            if event is None:
                break
            ok = self._deliver(event)
            if not ok:
                # Light exponential backoff on failure.  We still drop
                # the event - the local file log is the durable record.
                time.sleep(min(backoff, 10.0))
                backoff = min(backoff * 2.0, 10.0)
            else:
                backoff = 1.0

    def _deliver(self, event: Dict[str, Any]) -> bool:
        try:
            payload = (json.dumps(event, default=str) + "\n").encode("utf-8")
        except (TypeError, ValueError) as exc:
            log.error("failed to serialize event: %s", exc)
            return True  # don't retry - it'll never serialize

        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as s:
                s.settimeout(self.timeout)
                s.sendall(payload)
            return True
        except OSError as exc:
            log.debug("forwarder delivery failed: %s", exc)
            return False
