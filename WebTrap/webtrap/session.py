"""In-memory session/IP behaviour tracking for WebTrap.

For a honeypot we don't need durable sessions - we need a
*behavioural* view of an attacker:  How many distinct paths did they
hit?  How fast?  Did they progress from scanning to exploitation?

State is kept in memory; on restart we forget - this is intentional and
matches HonnyPotter's stateless design.  Aggregate intelligence lives
in the HoneyBee Core that consumes our events.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import defaultdict, deque
from typing import Deque, Dict, Optional


class SessionTracker:
    SESSION_TTL = 1800  # 30 minutes idle

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_cookie: Dict[str, "_Session"] = {}
        self._by_ip: Dict[str, "_Session"] = {}

    def touch(self, ip: str, cookie: Optional[str], path: str, method: str) -> "_Session":
        with self._lock:
            self._gc()
            sess: Optional[_Session] = None
            if cookie and cookie in self._by_cookie:
                sess = self._by_cookie[cookie]
            elif ip in self._by_ip:
                sess = self._by_ip[ip]
            if sess is None:
                sess = _Session(session_id=cookie or uuid.uuid4().hex)
                if cookie:
                    self._by_cookie[cookie] = sess
                self._by_ip[ip] = sess
            sess.record(path, method)
            return sess

    def _gc(self) -> None:
        cutoff = time.time() - self.SESSION_TTL
        for table in (self._by_cookie, self._by_ip):
            stale = [k for k, v in table.items() if v.last_seen < cutoff]
            for k in stale:
                table.pop(k, None)


class _Session:
    __slots__ = (
        "session_id",
        "first_seen",
        "last_seen",
        "request_count",
        "paths",
        "methods",
        "recent_paths",
    )

    def __init__(self, session_id: str) -> None:
        self.session_id = session_id
        self.first_seen = time.time()
        self.last_seen = self.first_seen
        self.request_count = 0
        self.paths: Dict[str, int] = defaultdict(int)
        self.methods: Dict[str, int] = defaultdict(int)
        self.recent_paths: Deque[str] = deque(maxlen=20)

    def record(self, path: str, method: str) -> None:
        now = time.time()
        self.last_seen = now
        self.request_count += 1
        self.paths[path] += 1
        self.methods[method] += 1
        self.recent_paths.append(path)

    def snapshot(self) -> Dict:
        return {
            "session_id": self.session_id,
            "first_seen": int(self.first_seen),
            "last_seen": int(self.last_seen),
            "duration": int(self.last_seen - self.first_seen),
            "request_count": self.request_count,
            "unique_paths": len(self.paths),
            "methods": dict(self.methods),
            "recent_paths": list(self.recent_paths),
        }
