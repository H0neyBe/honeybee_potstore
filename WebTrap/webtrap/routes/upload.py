"""Fake file upload endpoints.

The honeypot accepts the upload, stores the bytes (capped) under
``./captured_uploads/<timestamp>_<safe_name>`` and forwards a
``webtrap.upload`` event including a SHA-256 of the contents.  We never
execute or interpret the uploaded data.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
from typing import Tuple

from flask import Blueprint, g, jsonify, render_template, request

from ..events import CATEGORY_UPLOAD, SEVERITY_CRITICAL, SEVERITY_HIGH

bp = Blueprint("upload", __name__)

UPLOAD_DIR = os.environ.get("WEBTRAP_UPLOAD_DIR", "./captured_uploads")
MAX_STORE = 5 * 1024 * 1024  # 5 MiB cap per file - we only need a sample.

_SAFE = re.compile(r"[^A-Za-z0-9._-]")


def _safe_name(name: str) -> str:
    name = _SAFE.sub("_", os.path.basename(name or "upload.bin"))
    return name[:80] or "upload.bin"


def _store_file(filename: str, data: bytes) -> Tuple[str, str]:
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    digest = hashlib.sha256(data).hexdigest()
    safe = _safe_name(filename)
    path = os.path.join(UPLOAD_DIR, f"{int(time.time())}_{digest[:10]}_{safe}")
    with open(path, "wb") as fh:
        fh.write(data[:MAX_STORE])
    return path, digest


@bp.route("/upload", methods=["GET", "POST"])
@bp.route("/upload.php", methods=["GET", "POST"])
@bp.route("/files/upload", methods=["GET", "POST"])
@bp.route("/admin/upload", methods=["GET", "POST"])
def upload():
    if request.method == "GET":
        return render_template("upload.html", title="File Upload")

    captured = []
    for field in request.files:
        for f in request.files.getlist(field):
            data = f.read() or b""
            path, sha = _store_file(f.filename or "unnamed", data)
            severity = SEVERITY_CRITICAL if _looks_like_webshell(f.filename, data) else SEVERITY_HIGH
            g.recorder.record(
                eventid="webtrap.upload",
                category=CATEGORY_UPLOAD,
                severity=severity,
                message=f"File uploaded: {f.filename}",
                request_ctx=g.ctx,
                extra={
                    "upload_field": field,
                    "upload_filename": f.filename,
                    "upload_content_type": f.mimetype,
                    "upload_size": len(data),
                    "upload_sha256": sha,
                    "upload_stored_at": path,
                },
            )
            captured.append({"filename": f.filename, "size": len(data), "sha256": sha})
    g.handled = True

    if not captured:
        return jsonify({"error": "no_file", "message": "No file part in request"}), 400
    # Return a believable success message - keep the attacker working.
    return jsonify({"status": "ok", "message": "Upload received", "files": captured})


_WEBSHELL_NAME = re.compile(r"\.(ph(p[3457s]?|tml)|jsp[x]?|asp[x]?|aspx)$", re.I)
_WEBSHELL_BODY = re.compile(rb"(eval\s*\(|system\s*\(|passthru\s*\(|base64_decode|<\?php|cmd\.exe|/bin/sh)", re.I)


def _looks_like_webshell(filename: str, data: bytes) -> bool:
    if filename and _WEBSHELL_NAME.search(filename):
        return True
    if _WEBSHELL_BODY.search(data[:8192]):
        return True
    return False
