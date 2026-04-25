# 🍯 WebTrap — Vulnerable Web Application Honeypot

**Version:** 1.0.0
**Type:** Web / HTTP(S) Honeypot
**Protocols:** HTTP, HTTPS
**Status:** ✅ Ready for HoneyBee

WebTrap is a **medium-interaction web honeypot** that simulates a vulnerable
corporate intranet — fake admin panels, login pages, REST/GraphQL APIs, file
upload endpoints, and the kind of misconfigured services attackers love
(`.env`, `.git/config`, `phpinfo.php`, Spring `/actuator`, exposed backups).
Every interaction is captured, fingerprinted and forwarded to a HoneyBee Node
using the same JSON-line TCP protocol as Cowrie and HonnyPotter.

---

## ✨ Features

- ✅ **Modular Flask app** — drop-in (`from webtrap import create_app`) or run
  standalone (`python standalone.py`) or via Docker.
- ✅ **Multi-surface deception**
  - WordPress, Joomla, phpMyAdmin and generic `/admin` login forms
  - Django / generic `/login`, `/signin`, `/accounts/login/`
  - REST APIs: `/api/v1/users`, `/api/v1/login`, `/api/v1/config`, `/api/v1/search`
  - GraphQL endpoint, OAuth `/oauth/token`
  - File upload (`/upload`, `/upload.php`, `/files/upload`, `/admin/upload`)
  - Misconfigured services (`.env`, `.git/config`, `phpinfo.php`, `/server-status`,
    `/actuator/*`, `backup.sql`, `robots.txt`, `.well-known/security.txt`)
- ✅ **Full request capture** — IP, port, headers, body (capped), cookies, query string
- ✅ **User-Agent fingerprinting** — classifies browsers, bots and known attack
  tooling (sqlmap, nikto, nuclei, gobuster, burp, hydra, …) and emits a stable
  16-hex fingerprint hash for grouping.
- ✅ **Payload tagging** — heuristic detection of SQLi, XSS, RCE, LFI, SSRF,
  Log4Shell, SSTI, path traversal and webshell patterns.
- ✅ **Behavioural session tracking** — per-IP / per-cookie session aggregation
  (request count, unique paths, methods, recency window).
- ✅ **Captured-file storage** — uploads are written to disk with SHA-256 and
  `application/octet-stream` only; never executed.
- ✅ **Canary credentials** — optional bait creds that "succeed" once and
  reveal a fake admin console for high-confidence intrusion alerting.
- ✅ **Async forwarder** — events are queued on a background thread so the
  honeypot never stalls if the Node is slow or unreachable.
- ✅ **Local file log** — durable JSON-line audit trail in `logs/webtrap.log`.

---

## 🚀 Quick start

### 1. Local (Linux/macOS)

```bash
cd honeybee_potstore/WebTrap
chmod +x install.sh
./install.sh
. venv/bin/activate
python standalone.py
```

### 2. Local (Windows)

```powershell
cd honeybee_potstore\WebTrap
.\install.ps1
.\venv\Scripts\Activate.ps1
python standalone.py
```

### 3. Docker

```bash
docker compose up -d
```

By default WebTrap listens on `0.0.0.0:8088` and forwards events to
`127.0.0.1:9100` (the HoneyBee Node).

### 4. Plug into another Flask/WSGI project

```python
from webtrap import create_app
app = create_app()
# Mount under a sub-path with DispatcherMiddleware, or run as your only app.
```

---

## ⚙️ Configuration

Configuration is layered — defaults < `config.yaml` < environment variables.

| Variable                        | Default               | Description                      |
| ------------------------------- | --------------------- | -------------------------------- |
| `HONEYBEE_POT_ID`               | `webtrap-01`          | Pot instance ID                  |
| `HONEYBEE_HOST`                 | `127.0.0.1`           | HoneyBee Node host               |
| `HONEYBEE_PORT`                 | `9100`                | HoneyBee Node TCP port           |
| `HONEYBEE_ENABLE`               | `true`                | Enable forwarding                |
| `HONEYBEE_ENABLE_FILE_LOG`      | `true`                | Mirror events to local file      |
| `HONEYBEE_LOG_FILE`             | `./logs/webtrap.log`  | Log path                         |
| `WEBTRAP_BIND_HOST`             | `0.0.0.0`             | Listen host                      |
| `WEBTRAP_BIND_PORT`             | `8088`                | Listen port                      |
| `WEBTRAP_TLS_CERT` / `_KEY`     | (unset)               | Optional TLS                     |
| `WEBTRAP_LOG_LEVEL`             | `INFO`                | Python log level                 |
| `WEBTRAP_FAKE_HOSTNAME`         | `intranet.corp.local` | Hostname used in deception pages |
| `WEBTRAP_CANARY_USER` / `_PASS` | (unset)               | Optional canary credentials      |
| `WEBTRAP_UPLOAD_DIR`            | `./captured_uploads`  | Where uploaded files are stored  |
| `WEBTRAP_CONFIG`                | `./config.yaml`       | YAML config path                 |

---

## 📡 Event format

Events are JSON, one per line, sent over TCP to the HoneyBee Node — the
**same shape** the Node already parses for HonnyPotter (see
`internal/node/eventfwd/listener.go`).

```json
{
  "eventid": "webtrap.login.failed",
  "pot_id": "webtrap-01",
  "pot_type": "webtrap",
  "timestamp": 1745596389,
  "honeybee_category": "authentication",
  "honeybee_severity": "medium",
  "message": "Failed admin login: root",
  "src_ip": "203.0.113.42",
  "src_port": 51823,
  "dst_port": 8088,
  "user_agent": "sqlmap/1.7.11#stable",
  "ua_category": "tool",
  "ua_tool": "sqlmap",
  "ua_fingerprint": "9b1c2f4e7a0d3210",
  "request_uri": "/admin/login",
  "request_method": "POST",
  "request_headers": {
    "Content-Type": "application/x-www-form-urlencoded",
    "...": "..."
  },
  "request_body": "log=root&pwd=' OR '1'='1",
  "request_body_size": 28,
  "payload_tags": ["sqli"],
  "session": {
    "session_id": "9b1c...",
    "first_seen": 1745596300,
    "last_seen": 1745596389,
    "duration": 89,
    "request_count": 14,
    "unique_paths": 11,
    "methods": { "GET": 10, "POST": 4 },
    "recent_paths": ["/", "/robots.txt", "/.env", "/admin/login"]
  },
  "username": "root",
  "password": "' OR '1'='1",
  "login_kind": "admin-panel"
}
```

### Event IDs

| eventid                           | category                     | severity          | when                              |
| --------------------------------- | ---------------------------- | ----------------- | --------------------------------- |
| `webtrap.request`                 | `probe`                      | low / high\*      | every uncategorised request       |
| `webtrap.login.failed`            | `authentication`             | medium            | any failed HTML login             |
| `webtrap.api.login.failed`        | `authentication`             | medium            | failed JSON / OAuth login         |
| `webtrap.login.canary_hit`        | `authentication`             | high              | canary creds matched              |
| `webtrap.api.probe`               | `reconnaissance`             | low               | API root probed                   |
| `webtrap.api.users.access`        | `info-leak`                  | medium / high\*   | user-list endpoint hit            |
| `webtrap.api.user.access`         | `info-leak` / `exploitation` | medium / high     | user CRUD on `/api/users/{id}`    |
| `webtrap.api.config.access`       | `info-leak`                  | high              | config endpoint accessed          |
| `webtrap.api.search`              | `recon` / `exploit`          | low / high\*      | search endpoint, payload-aware    |
| `webtrap.api.graphql`             | `reconnaissance`             | medium            | GraphQL endpoint probed           |
| `webtrap.upload`                  | `upload`                     | high / critical\* | file upload (critical = webshell) |
| `webtrap.misconfig.env`           | `info-leak`                  | high              | `.env` harvested                  |
| `webtrap.misconfig.git`           | `info-leak`                  | high              | `.git/*` harvested                |
| `webtrap.misconfig.phpinfo`       | `info-leak`                  | medium            | phpinfo accessed                  |
| `webtrap.misconfig.server_status` | `info-leak`                  | medium            | Apache server-status              |
| `webtrap.misconfig.actuator`      | `info-leak`                  | high              | Spring actuator accessed          |
| `webtrap.misconfig.backup`        | `info-leak`                  | high              | backup file requested             |
| `webtrap.recon.robots`            | `reconnaissance`             | low               | robots.txt fetched                |
| `webtrap.admin.access`            | `reconnaissance`             | high              | post-canary admin page browse     |

`*` severity is escalated automatically when the request matches a
`payload_tags` entry (sqli, xss, rce, lfi, ssrf, log4shell, ssti, …).

---

## 🧪 Testing

```bash
# Generic probe
curl -s http://localhost:8088/.env

# Failed admin login
curl -s -X POST http://localhost:8088/admin/login \
     -d "log=admin&pwd=admin123"

# SQLi-flavoured search (will be tagged)
curl -s "http://localhost:8088/api/v1/search?q=1'%20OR%20'1'='1"

# Webshell upload (will be tagged 'critical')
echo '<?php system($_GET["c"]); ?>' > shell.php
curl -s -F "file=@shell.php" http://localhost:8088/upload

# Inspect events
tail -f logs/webtrap.log
```

Verify that HoneyBee Node receives events:

```bash
nc -lk 127.0.0.1 9100   # quick smoke-test in absence of a real Node
```

---

## 🗂 File structure

```
WebTrap/
├── webtrap/                  # importable Python package
│   ├── __init__.py
│   ├── app.py                # Flask application factory
│   ├── config.py             # YAML + env config
│   ├── events.py             # event recorder
│   ├── forwarder.py          # async TCP JSON-line forwarder
│   ├── fingerprint.py        # UA + payload classification
│   ├── middleware.py         # per-request capture
│   ├── session.py            # in-memory behavioural sessions
│   ├── deception.py          # fake users, errors, env content
│   ├── routes/
│   │   ├── login.py          # all login surfaces
│   │   ├── admin.py          # post-canary admin pages
│   │   ├── api.py            # REST + GraphQL traps
│   │   ├── upload.py         # file upload capture
│   │   ├── misconfig.py      # leaky endpoints
│   │   └── catchall.py       # landing + 404
│   └── templates/            # HTML deception pages
├── standalone.py             # entry point for direct run
├── config.yaml               # default config
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── install.sh                # Linux / macOS installer
├── install.ps1               # Windows installer
└── README.md
```

---

## 🔐 Security notes

- WebTrap **never executes uploaded files**. Uploads are stored byte-for-byte
  (capped at 5 MiB) under `captured_uploads/` with their SHA-256.
- Run WebTrap **in an isolated network segment** or behind a reverse proxy
  with strict outbound egress filtering — like every honeypot, it is a
  deliberately attractive target.
- The deception strings in `deception.py` are **fake**. Do not insert real
  credentials there; the honeypot's value comes from being convincing-but-empty.
