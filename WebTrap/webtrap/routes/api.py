"""Fake REST API endpoints.

These return believable JSON shapes (Laravel, DRF, Express) so
attackers continue probing.  Every response is 401/403/500 except for
endpoints intentionally leaking *fake* data.
"""

from __future__ import annotations

from flask import Blueprint, g, jsonify, request

from ..deception import fake_users_json, random_db_error
from ..events import (
    CATEGORY_EXPLOIT,
    CATEGORY_INFOLEAK,
    CATEGORY_RECON,
    SEVERITY_HIGH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
)

bp = Blueprint("api", __name__)


def _record(eventid, category, severity, msg, extra=None):
    g.recorder.record(eventid, category, severity, msg, g.ctx, extra=extra)
    g.handled = True


@bp.route("/api", methods=["GET"])
@bp.route("/api/", methods=["GET"])
@bp.route("/api/v1", methods=["GET"])
@bp.route("/api/v1/", methods=["GET"])
def api_index():
    _record("webtrap.api.probe", CATEGORY_RECON, SEVERITY_LOW, "API root probed")
    return jsonify({
        "name": "intranet-api",
        "version": "1.4.2",
        "endpoints": [
            "/api/v1/users",
            "/api/v1/login",
            "/api/v1/files",
            "/api/v1/config",
        ],
    })


@bp.route("/api/v1/users", methods=["GET"])
@bp.route("/api/users", methods=["GET"])
def api_users():
    severity = SEVERITY_HIGH if g.ctx.get("payload_tags") else SEVERITY_MEDIUM
    _record(
        "webtrap.api.users.access",
        CATEGORY_INFOLEAK,
        severity,
        "User list endpoint accessed",
    )
    # Serve dummy data - encourages further enumeration we can capture.
    return jsonify({"data": fake_users_json(), "total": 5, "page": 1})


@bp.route("/api/v1/users/<user_id>", methods=["GET", "PUT", "DELETE"])
@bp.route("/api/users/<user_id>", methods=["GET", "PUT", "DELETE"])
def api_user_detail(user_id: str):
    severity = SEVERITY_HIGH if request.method != "GET" else SEVERITY_MEDIUM
    _record(
        "webtrap.api.user.access",
        CATEGORY_EXPLOIT if request.method != "GET" else CATEGORY_INFOLEAK,
        severity,
        f"{request.method} on /api/users/{user_id}",
        extra={"target_user_id": user_id},
    )
    if request.method == "GET":
        users = {u["id"]: u for u in fake_users_json()}
        if user_id in users:
            return jsonify(users[user_id])
        return jsonify({"error": "not_found"}), 404
    return jsonify({"error": "forbidden", "message": "Insufficient privileges"}), 403


@bp.route("/api/v1/config", methods=["GET"])
@bp.route("/api/config", methods=["GET"])
def api_config():
    _record(
        "webtrap.api.config.access",
        CATEGORY_INFOLEAK,
        SEVERITY_HIGH,
        "Configuration endpoint accessed",
    )
    return jsonify({
        "error": "forbidden",
        "message": "Configuration endpoint requires admin scope",
        "trace_id": "8c2e9b1f-2f1a-4d2a-9e0a-3a3b1c5e8f01",
    }), 403


@bp.route("/api/v1/search", methods=["GET", "POST"])
@bp.route("/api/search", methods=["GET", "POST"])
def api_search():
    q = request.args.get("q") or (request.get_json(silent=True) or {}).get("q") or ""
    severity = SEVERITY_HIGH if g.ctx.get("payload_tags") else SEVERITY_LOW
    _record(
        "webtrap.api.search",
        CATEGORY_EXPLOIT if g.ctx.get("payload_tags") else CATEGORY_RECON,
        severity,
        f"Search query: {q[:80]}",
        extra={"query": q},
    )
    if "'" in q or '"' in q or "--" in q:
        # SQLi fish - return a believable DB error.
        return jsonify({"error": "internal_error", "message": random_db_error()}), 500
    return jsonify({"results": [], "query": q})


@bp.route("/graphql", methods=["GET", "POST"])
def graphql():
    body = request.get_data(as_text=True)
    _record(
        "webtrap.api.graphql",
        CATEGORY_RECON,
        SEVERITY_MEDIUM,
        "GraphQL endpoint accessed",
        extra={"graphql_body": body[:2000]},
    )
    return jsonify({"errors": [{"message": "GraphQL endpoint requires authentication"}]}), 401
