# 🍯 HoneyBee PotStore

**Repository:** https://github.com/H0neyBe/honeybee_potstore

Honeypot collection for HoneyBee. Nodes pull honeypots from this repository.

## Available Honeypots

| Honeypot | Type | Directory |
|----------|------|-----------|
| **Cowrie** | SSH/Telnet | `cowrie/` |

## How It Works

1. HoneyBee Node receives `InstallHoneypot` command
2. Node clones this repo: `https://github.com/H0neyBe/honeybee_potstore`
3. Node installs the specified honeypot
4. Honeypot events are forwarded to HoneyBee Core

## Install via Node

```json
{
  "InstallHoneypot": {
    "honeypot_id": "cowrie-01",
    "honeypot_type": "cowrie",
    "ssh_port": 2222,
    "auto_start": true
  }
}
```

The node automatically pulls from this repository.

## Adding New Honeypots

1. Add honeypot directory (e.g., `dionaea/`)
2. Each honeypot needs a `requirements.txt` or `setup.py`
3. Configure to send events to `localhost:9100`

## License

MIT
