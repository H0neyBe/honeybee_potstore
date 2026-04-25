"""Catch-all + landing page.

The middleware logs *every* request as ``webtrap.request`` already, but
we want a believable landing page on ``/`` and a realistic 404 for
unknown paths so reconnaissance keeps producing data.
"""

from __future__ import annotations

from flask import Blueprint, render_template

bp = Blueprint("catchall", __name__)


@bp.route("/")
def index():
    return render_template("index.html", title="Corp Intranet")


# Keep this LAST.  Flask's Blueprint registration order means it only
# matches if no earlier route did - exactly what we want for a probe
# trap.
@bp.route("/<path:_p>", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"])
def fallback(_p: str):
    return render_template("404.html", path="/" + _p), 404
