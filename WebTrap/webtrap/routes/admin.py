"""Fake admin dashboard pages reachable only via the canary login."""

from __future__ import annotations

from flask import Blueprint, g, render_template

from ..events import CATEGORY_RECON, SEVERITY_HIGH

bp = Blueprint("admin", __name__)


@bp.route("/admin/dashboard")
@bp.route("/admin/users")
@bp.route("/admin/settings")
def admin_pages():
    g.recorder.record(
        eventid="webtrap.admin.access",
        category=CATEGORY_RECON,
        severity=SEVERITY_HIGH,
        message="Authenticated admin area accessed (post-canary)",
        request_ctx=g.ctx,
    )
    g.handled = True
    return render_template("admin.html", title="Admin Console")
