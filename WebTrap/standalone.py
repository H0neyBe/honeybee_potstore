"""Standalone WebTrap entry point.

Run::

    python standalone.py

It will read configuration from ``./config.yaml`` (if PyYAML is
installed) and environment variables, then bind on the configured
host/port and start serving the deceptive web app.

In production (or any non-trivial deployment) prefer:

    gunicorn -w 4 -b 0.0.0.0:8088 'webtrap:create_app()'

or run the provided Docker image.
"""

from __future__ import annotations

import logging
import os
import signal
import sys

# Allow running directly from the WebTrap directory: ensure the local
# ``webtrap`` package is importable when the script is launched as
# ``python standalone.py``.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webtrap import create_app  # noqa: E402
from webtrap.config import WebTrapConfig  # noqa: E402

log = logging.getLogger("webtrap.main")


def main() -> int:
    cfg = WebTrapConfig.load()
    app = create_app(cfg)

    def _shutdown(signum, _frame):  # pragma: no cover - signal path
        log.info("shutdown signal %s received", signum)
        recorder = app.extensions.get("webtrap_recorder")
        if recorder:
            recorder.close()
        sys.exit(0)

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, _shutdown)
        except (ValueError, OSError):
            pass

    ssl_ctx = None
    if cfg.tls_cert and cfg.tls_key:
        ssl_ctx = (cfg.tls_cert, cfg.tls_key)

    log.warning(
        "Starting WebTrap pot=%s on %s:%d (use a real WSGI server in production)",
        cfg.pot_id, cfg.bind_host, cfg.bind_port,
    )
    app.run(
        host=cfg.bind_host,
        port=cfg.bind_port,
        ssl_context=ssl_ctx,
        debug=False,
        use_reloader=False,
        threaded=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
