"""Login & admin authentication endpoints.

Captures every credential pair under multiple realistic paths
(WordPress, Laravel, Django, generic JSON API).  Always fails with a
rotating set of plausible error messages.  An optional canary
credential pair (configured per deployment) "succeeds" once - the
follow-up requests reveal post-exploitation tooling.
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, render_template, request

from ..deception import random_login_error
from ..events import (
    CATEGORY_AUTH,
    SEVERITY_HIGH,
    SEVERITY_MEDIUM,
)

bp = Blueprint("login", __name__)


def _record_auth(eventid: str, severity: str, username: str, password: str, message: str, extra=None):
    payload = {"username": username, "password": password}
    if extra:
        payload.update(extra)
    g.recorder.record(
        eventid=eventid,
        category=CATEGORY_AUTH,
        severity=severity,
        message=message,
        request_ctx=g.ctx,
        extra=payload,
    )
    g.handled = True


def _credentials_from_request():
    """Pull username/password out of common request shapes."""
    username = ""
    password = ""
    if request.is_json:
        data = request.get_json(silent=True) or {}
        username = data.get("username") or data.get("user") or data.get("email") or data.get("login") or ""
        password = data.get("password") or data.get("pass") or data.get("pwd") or ""
    else:
        f = request.form
        username = (
            f.get("username")
            or f.get("user")
            or f.get("email")
            or f.get("login")
            or f.get("log")
            or f.get("uname")
            or ""
        )
        password = f.get("password") or f.get("pass") or f.get("pwd") or ""
    if request.authorization:
        username = username or request.authorization.username or ""
        password = password or request.authorization.password or ""
    return username.strip(), password.strip()


# WordPress-style login (kept for completeness even though HonnyPotter
# also covers it - WebTrap is not deployed alongside HonnyPotter on the
# same port and analysts may run only one of them).
@bp.route("/wp-login.php", methods=["GET", "POST"])
@bp.route("/wp-admin", methods=["GET", "POST"])
@bp.route("/wp-admin/", methods=["GET", "POST"])
def wp_login():
    if request.method == "POST":
        u, p = _credentials_from_request()
        _record_auth(
            "webtrap.login.failed",
            SEVERITY_MEDIUM,
            u, p,
            f"Failed WordPress login: {u or '<empty>'}",
            extra={"login_kind": "wordpress"},
        )
    return render_template("login.html", title="WordPress", action_path=request.path,
                           error=random_login_error() if request.method == "POST" else "")


# Generic /admin /administrator (Joomla, custom apps)
@bp.route("/admin", methods=["GET", "POST"])
@bp.route("/admin/", methods=["GET", "POST"])
@bp.route("/admin/login", methods=["GET", "POST"])
@bp.route("/administrator", methods=["GET", "POST"])
@bp.route("/administrator/", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        u, p = _credentials_from_request()
        _record_auth(
            "webtrap.login.failed",
            SEVERITY_MEDIUM,
            u, p,
            f"Failed admin login: {u or '<empty>'}",
            extra={"login_kind": "admin-panel"},
        )
        # Canary check: if the operator set canary creds, "succeed" once.
        cfg = g.config
        if (
            cfg.canary_username
            and cfg.canary_password
            and u == cfg.canary_username
            and p == cfg.canary_password
        ):
            g.recorder.record(
                eventid="webtrap.login.canary_hit",
                category=CATEGORY_AUTH,
                severity=SEVERITY_HIGH,
                message="Canary credential used - high-confidence intrusion",
                request_ctx=g.ctx,
            )
            return render_template("admin.html", title="Admin Console")
    return render_template(
        "login.html",
        title="Admin Console",
        action_path=request.path,
        error=random_login_error() if request.method == "POST" else "",
    )


# Django-style admin
@bp.route("/accounts/login/", methods=["GET", "POST"])
@bp.route("/login", methods=["GET", "POST"])
@bp.route("/login.php", methods=["GET", "POST"])
@bp.route("/signin", methods=["GET", "POST"])
def generic_login():
    if request.method == "POST":
        u, p = _credentials_from_request()
        _record_auth(
            "webtrap.login.failed",
            SEVERITY_MEDIUM,
            u, p,
            f"Failed login: {u or '<empty>'}",
            extra={"login_kind": "generic"},
        )
    return render_template(
        "login.html",
        title="Sign in",
        action_path=request.path,
        error=random_login_error() if request.method == "POST" else "",
    )


# JSON / REST login - always returns 401 with realistic error envelope.
@bp.route("/api/login", methods=["POST"])
@bp.route("/api/v1/login", methods=["POST"])
@bp.route("/api/auth", methods=["POST"])
@bp.route("/api/auth/login", methods=["POST"])
@bp.route("/oauth/token", methods=["POST"])
def api_login():
    u, p = _credentials_from_request()
    _record_auth(
        "webtrap.api.login.failed",
        SEVERITY_MEDIUM,
        u, p,
        f"Failed API login: {u or '<empty>'}",
        extra={"login_kind": "api"},
    )
    return jsonify({"error": "invalid_credentials", "message": "Invalid email or password"}), 401


# phpMyAdmin login
@bp.route("/phpmyadmin", methods=["GET", "POST"])
@bp.route("/phpmyadmin/", methods=["GET", "POST"])
@bp.route("/phpmyadmin/index.php", methods=["GET", "POST"])
@bp.route("/pma", methods=["GET", "POST"])
def phpmyadmin():
    if request.method == "POST":
        u, p = _credentials_from_request()
        _record_auth(
            "webtrap.login.failed",
            SEVERITY_MEDIUM,
            u, p,
            f"Failed phpMyAdmin login: {u or '<empty>'}",
            extra={"login_kind": "phpmyadmin"},
        )
    return render_template(
        "login.html",
        title="phpMyAdmin",
        action_path=request.path,
        error="#1045 - Access denied for user" if request.method == "POST" else "",
    )
