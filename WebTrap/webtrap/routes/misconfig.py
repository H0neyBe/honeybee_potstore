"""Misconfigured-service traps.

Endpoints that real targets often leak (.env, .git/config, phpinfo,
server-status, /actuator, etc).  We serve plausible *fake* contents so
the attacker treats the host as a real one.
"""

from __future__ import annotations

from flask import Blueprint, Response, g, jsonify, request

from ..deception import FAKE_ENV_FILE, FAKE_GIT_CONFIG, FAKE_ROBOTS
from ..events import CATEGORY_INFOLEAK, CATEGORY_RECON, SEVERITY_HIGH, SEVERITY_LOW, SEVERITY_MEDIUM

bp = Blueprint("misconfig", __name__)


def _record(eventid, severity, msg, category=CATEGORY_INFOLEAK, extra=None):
    g.recorder.record(eventid, category, severity, msg, g.ctx, extra=extra)
    g.handled = True


@bp.route("/.env")
@bp.route("/.env.local")
@bp.route("/.env.production")
@bp.route("/config/.env")
def env_file():
    _record("webtrap.misconfig.env", SEVERITY_HIGH, ".env file harvested")
    return Response(FAKE_ENV_FILE, mimetype="text/plain")


@bp.route("/.git/config")
@bp.route("/.git/HEAD")
def git_config():
    _record("webtrap.misconfig.git", SEVERITY_HIGH, ".git artefact harvested")
    if request.path.endswith("HEAD"):
        return Response("ref: refs/heads/main\n", mimetype="text/plain")
    return Response(FAKE_GIT_CONFIG, mimetype="text/plain")


@bp.route("/robots.txt")
def robots():
    _record("webtrap.recon.robots", SEVERITY_LOW, "robots.txt fetched", category=CATEGORY_RECON)
    return Response(FAKE_ROBOTS, mimetype="text/plain")


@bp.route("/phpinfo.php")
@bp.route("/info.php")
@bp.route("/test.php")
def phpinfo():
    _record("webtrap.misconfig.phpinfo", SEVERITY_MEDIUM, "phpinfo() page accessed")
    cfg = g.config
    html = f"""<html><body><h1>PHP Version {cfg.fake_php_version}</h1>
<table border=1><tr><td>System</td><td>Linux web01 5.15.0-92-generic #102-Ubuntu</td></tr>
<tr><td>Server API</td><td>FPM/FastCGI</td></tr>
<tr><td>document_root</td><td>/var/www/html</td></tr>
<tr><td>HTTP_HOST</td><td>{cfg.fake_hostname}</td></tr></table></body></html>"""
    return Response(html, mimetype="text/html")


@bp.route("/server-status")
@bp.route("/server-info")
def server_status():
    _record("webtrap.misconfig.server_status", SEVERITY_MEDIUM, "server-status accessed")
    return Response(
        "Apache Server Status for intranet.corp.local\n"
        "Server Version: Apache/2.4.41\nCurrent Time: now\n",
        mimetype="text/plain",
    )


@bp.route("/actuator")
@bp.route("/actuator/")
@bp.route("/actuator/<path:rest>")
def actuator(rest: str = ""):
    _record("webtrap.misconfig.actuator", SEVERITY_HIGH, f"Spring actuator probed: {rest}")
    if rest in ("env", "configprops"):
        return jsonify({
            "applicationConfig": {
                "spring.datasource.url": "jdbc:mysql://db-internal.corp.local:3306/corp_prod",
                "spring.datasource.username": "app_user",
                "spring.datasource.password": "******",
            }
        })
    return jsonify({
        "_links": {
            "self": {"href": "/actuator"},
            "health": {"href": "/actuator/health"},
            "env": {"href": "/actuator/env"},
            "configprops": {"href": "/actuator/configprops"},
            "mappings": {"href": "/actuator/mappings"},
        }
    })


@bp.route("/.well-known/security.txt")
def security_txt():
    _record("webtrap.recon.well_known", SEVERITY_LOW, "security.txt fetched", category=CATEGORY_RECON)
    return Response(
        "Contact: mailto:security@corp.local\nExpires: 2099-01-01T00:00:00Z\n",
        mimetype="text/plain",
    )


@bp.route("/backup.zip")
@bp.route("/backup.tar.gz")
@bp.route("/backup.sql")
@bp.route("/dump.sql")
@bp.route("/database.sql")
def backup():
    _record("webtrap.misconfig.backup", SEVERITY_HIGH, "backup file requested")
    # Tiny believable header bytes - never serve real-looking content.
    return Response(b"\x50\x4b\x03\x04access denied", mimetype="application/octet-stream", status=403)
