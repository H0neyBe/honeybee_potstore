# 🍯 HoneyBee PotStore

**Repository:** https://github.com/H0neyBe/honeybee_potstore

Honeypot (Pot) collection for HoneyBee. Nodes pull honeypots from this repository.

## Available Honeypots

| Honeypot | Type | Directory | Status |
|----------|------|-----------|--------|
| **Cowrie** | SSH/Telnet | `cowrie/` | ✅ Ready |

## How It Works

1. HoneyBee Core sends `NodeCommand` with `InstallPot` to a node
2. Node clones this repo: `https://github.com/H0neyBe/honeybee_potstore`
3. Node installs the specified honeypot (pot)
4. Honeypot events are forwarded to HoneyBee Core

## Protocol v2 - Install Command

Send via HoneyBee Core CLI or API:

```json
{
  "version": 2,
  "message": {
    "NodeCommand": {
      "node_id": 12345,
      "command": {
        "InstallPot": {
          "pot_id": "cowrie-01",
          "honeypot_type": "cowrie",
          "git_url": null,
          "git_branch": null,
          "config": {
            "ssh_port": "2222",
            "telnet_port": "2223"
          },
          "auto_start": true
        }
      }
    }
  }
}
```

**Note:** If `git_url` is `null` or omitted, the node automatically uses this repository.

## Other Commands

### Deploy (Start) Pot
```json
{
  "NodeCommand": {
    "node_id": 12345,
    "command": {
      "DeployPot": "cowrie-01"
    }
  }
}
```

### Stop Pot
```json
{
  "NodeCommand": {
    "node_id": 12345,
    "command": {
      "StopPot": "cowrie-01"
    }
  }
}
```

### Restart Pot
```json
{
  "NodeCommand": {
    "node_id": 12345,
    "command": {
      "RestartPot": "cowrie-01"
    }
  }
}
```

### Get Pot Status
```json
{
  "NodeCommand": {
    "node_id": 12345,
    "command": {
      "GetPotStatus": "cowrie-01"
    }
  }
}
```

### Get All Installed Pots
```json
{
  "NodeCommand": {
    "node_id": 12345,
    "command": {
      "GetInstalledPots": {}
    }
  }
}
```

## Adding New Honeypots

1. **Create honeypot directory** (e.g., `dionaea/`)
2. **Add requirements**: Include `requirements.txt` or `setup.py`
3. **Event forwarding**: Configure to send JSON events to `localhost:9100`
4. **Event format**: Send one JSON object per line

### Event Format
```json
{
  "eventid": "cowrie.login.success",
  "src_ip": "192.168.1.100",
  "src_port": 54321,
  "dst_port": 2222,
  "username": "admin",
  "password": "password123",
  "session": "abc123",
  "message": "Login successful"
}
```

## Honeypot Requirements

Each honeypot in the potstore should:
- ✅ Be installable via `pip install -r requirements.txt` or `pip install -e .`
- ✅ Support Python 3.7+
- ✅ Send events to TCP socket `localhost:9100`
- ✅ Use JSON format for events (one per line)
- ✅ Include a `requirements.txt` file

## Directory Structure

```
honeybee_potstore/
├── README.md
├── LICENSE
├── cowrie/              # Cowrie SSH/Telnet honeypot
│   ├── requirements.txt
│   ├── src/
│   │   └── cowrie/
│   │       └── output/
│   │           └── honeybee.py  # Custom output plugin
│   └── ...
└── [future-pots]/       # Future honeypots
```

## Custom Output Plugins

### Cowrie HoneyBee Plugin

Located at: `cowrie/src/cowrie/output/honeybee.py`

Automatically configured by the node to send events to `localhost:9100`.

## Testing a Honeypot

1. Clone this repository
2. Install the honeypot:
   ```bash
   cd cowrie
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
3. Configure output to send to `localhost:9100`
4. Start the honeypot
5. Attack it and verify events are sent

## License

MIT
