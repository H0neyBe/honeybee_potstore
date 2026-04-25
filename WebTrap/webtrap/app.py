"""Flask application factory for WebTrap.

Use :func:`create_app` either as a standalone WSGI entry point or
import it from another project::

    from webtrap import create_app
    app = create_app()

The factory wires:
    * configuration (env / YAML)
    * the request-capture middleware
    * every deception blueprint
    * the HoneyBee TCP forwarder + local file log
"""

from __future__ import annotations

import logging
import os
from typing import Optional

from flask import Flask

from .config import WebTrapConfig
from .events import EventRecorder
from .middleware import install_middleware
from .routes import ALL_BLUEPRINTS

log = logging.getLogger("webtrap")


def create_app(config: Optional[WebTrapConfig] = None) -> Flask:
    cfg = config or WebTrapConfig.load()

    logging.basicConfig(
        level=getattr(logging, cfg.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s :: %(message)s",
    )

    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir if os.path.isdir(static_dir) else None,
    )
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MiB hard cap
    # Suppress Flask's default 'strict_slashes' redirects - they leak
    # routing logic to a probing attacker.
    app.url_map.strict_slashes = False

    recorder = EventRecorder(cfg)
    app.extensions["webtrap_recorder"] = recorder
    app.extensions["webtrap_config"] = cfg

    install_middleware(app, cfg, recorder)
    for bp in ALL_BLUEPRINTS:
        app.register_blueprint(bp)

    # Generic, non-revealing error handlers - return believable pages
    # rather than Flask's debug stack-traces.
    @app.errorhandler(404)
    def _404(e):
        from flask import render_template, request
        return render_template("404.html", path=request.path), 404

    @app.errorhandler(500)
    def _500(e):
        from flask import render_template
        return render_template("500.html"), 500

    log.info("WebTrap initialised pot_id=%s bind=%s:%d forwarder=%s:%d enabled=%s",
             cfg.pot_id, cfg.bind_host, cfg.bind_port,
             cfg.honeybee_host, cfg.honeybee_port, cfg.honeybee_enable)
    return app
