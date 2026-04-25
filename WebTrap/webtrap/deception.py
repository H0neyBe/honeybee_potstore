"""Deception data: fake credentials, dummy database rows, error templates."""

from __future__ import annotations

import random
from typing import Dict, List

# Always-fail credentials presented in error messages or hinted at via
# leaked-config endpoints to keep attackers engaged.
FAKE_USERS: List[Dict[str, str]] = [
    {"id": "1", "username": "admin", "email": "admin@corp.local", "role": "administrator"},
    {"id": "2", "username": "jdoe", "email": "j.doe@corp.local", "role": "user"},
    {"id": "3", "username": "svc_backup", "email": "ops@corp.local", "role": "service"},
    {"id": "4", "username": "guest", "email": "guest@corp.local", "role": "guest"},
    {"id": "5", "username": "developer", "email": "dev@corp.local", "role": "developer"},
]

# Rotating realistic-looking but fake error messages.  Every variant
# implies a real backend exists so the attacker keeps probing.
LOGIN_ERRORS = [
    "ERROR: Invalid username or incorrect password.",
    "ERROR: The password you entered for the username \"{user}\" is incorrect.",
    "Authentication failed.  Please check your credentials and try again.",
    "Your account has been temporarily locked after multiple failed attempts. Try again in 15 minutes.",
]

DB_ERRORS = [
    "Warning: mysqli_query(): MySQL server has gone away",
    "Notice: Undefined index: user_id in /var/www/html/includes/db.php on line 142",
    "PDOException: SQLSTATE[42S02]: Base table or view not found",
]

# Fake env-style content served from misconfigured endpoints.  Values
# look plausible but are deliberately wrong / unreachable.
FAKE_ENV_FILE = """\
APP_NAME=corp-intranet
APP_ENV=production
APP_DEBUG=false
APP_URL=https://intranet.corp.local

DB_CONNECTION=mysql
DB_HOST=db-internal.corp.local
DB_PORT=3306
DB_DATABASE=corp_prod
DB_USERNAME=app_user
DB_PASSWORD=Pr0d-D8-S3cret!

REDIS_HOST=redis-internal.corp.local
REDIS_PASSWORD=R3disS3cret!

MAIL_DRIVER=smtp
MAIL_HOST=smtp.corp.local
MAIL_USERNAME=noreply@corp.local
MAIL_PASSWORD=M@ilP@ss123

AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
"""

FAKE_GIT_CONFIG = """\
[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = git@gitlab.corp.local:platform/intranet.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
"""

FAKE_ROBOTS = """\
User-agent: *
Disallow: /admin/
Disallow: /backup/
Disallow: /api/internal/
Disallow: /old-site/
Disallow: /.git/
Disallow: /phpmyadmin/
"""


def random_login_error(username: str = "") -> str:
    return random.choice(LOGIN_ERRORS).format(user=username or "user")


def random_db_error() -> str:
    return random.choice(DB_ERRORS)


def fake_users_json(limit: int = 5) -> List[Dict[str, str]]:
    return FAKE_USERS[:limit]
