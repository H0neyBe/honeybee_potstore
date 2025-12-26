# 🍯 HonnyPotter - WordPress Login Honeypot

**Version:** 1.2.0  
**Type:** WordPress/HTTP Honeypot  
**Protocols:** HTTP, HTTPS  
**Status:** ✅ Ready for HoneyBee

## Overview

HonnyPotter is a WordPress login honeypot that captures brute-force attacks and credential stuffing attempts. It logs all failed login attempts and forwards them to the HoneyBee Node for centralized analysis.

## Features

- ✅ WordPress login emulation
- ✅ XML-RPC endpoint support
- ✅ Brute-force attack detection
- ✅ Credential logging
- ✅ HoneyBee integration (sends events to Node)
- ✅ Low resource usage
- ✅ No database required
- ✅ Standalone or WordPress plugin mode

## Installation

### Option 1: Standalone (Recommended for HoneyBee)

1. **Clone the potstore:**
   ```bash
   git clone https://github.com/H0neyBe/honeybee_potstore
   cd honeybee_potstore/HonnyPotter
   ```

2. **Run installation script:**
   ```bash
   # Linux/macOS
   chmod +x install.sh
   ./install.sh
   
   # Windows
   .\install.ps1
   ```

3. **Configure web server:**
   - Point your web server to `standalone.php`
   - Or use as a standalone endpoint

4. **Set environment variables (optional):**
   ```bash
   export HONEYBEE_POT_ID="honnypotter-01"
   export HONEYBEE_ENABLE="true"
   export HONEYBEE_ENABLE_FILE_LOG="true"
   ```

### Option 2: WordPress Plugin

1. Copy all files to `wp-content/plugins/HonnyPotter/`
2. Activate the plugin in WordPress admin
3. The plugin will automatically forward events to HoneyBee Node

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HONEYBEE_POT_ID` | `honnypotter-01` | Pot instance ID |
| `HONEYBEE_ENABLE` | `true` | Enable HoneyBee forwarding |
| `HONEYBEE_ENABLE_FILE_LOG` | `true` | Enable local file logging |
| `HONEYBEE_LOG_FILE` | `./logs/honnypotter.log` | Log file path |

### Web Server Configuration

#### Apache (.htaccess)
```apache
<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteBase /
    RewriteRule ^wp-login\.php$ standalone.php [L]
</IfModule>
```

#### Nginx
```nginx
location /wp-login.php {
    try_files $uri /HonnyPotter/standalone.php;
}
```

## Usage

### Standalone Mode

Access the login form at:
```
http://your-server/standalone.php
```

Or POST directly:
```bash
curl -X POST http://localhost/standalone.php \
  -d "log=admin&pwd=password123"
```

### WordPress Plugin Mode

1. Install as WordPress plugin
2. Access WordPress login page
3. All failed attempts are logged and forwarded

### XML-RPC Endpoint

HonnyPotter also captures XML-RPC authentication attempts:
```bash
curl -X POST http://localhost/xmlrpc.php \
  -H "Content-Type: text/xml" \
  -d '<?xml version="1.0"?><methodCall>...</methodCall>'
```

## HoneyBee Integration

### Event Format

Events are sent to HoneyBee Node at `localhost:9100` in JSON format:

```json
{
  "eventid": "honnypotter.login.failed",
  "pot_id": "honnypotter-01",
  "pot_type": "honnypotter",
  "timestamp": 1703456789,
  "src_ip": "192.168.1.100",
  "src_port": 54321,
  "dst_port": 80,
  "username": "admin",
  "password": "password123",
  "user_agent": "Mozilla/5.0...",
  "request_uri": "/wp-login.php",
  "request_method": "POST",
  "message": "Failed login attempt: admin from 192.168.1.100",
  "honeybee_category": "authentication",
  "honeybee_severity": "medium"
}
```

### Event Types

- `honnypotter.login.failed` - Failed login attempt
- `honnypotter.xmlrpc.failed` - Failed XML-RPC authentication

### Categories

- `authentication` - Login/authentication events

### Severity Levels

- `medium` - Failed login attempts
- `high` - Multiple rapid failures (future)

## Testing

### Manual Test

```bash
# Test login endpoint
curl -X POST http://localhost/standalone.php \
  -d "log=testuser&pwd=testpass" \
  -v

# Check log file
tail -f logs/honnypotter.log

# Verify HoneyBee Node receives events
# (Check node logs or Core dashboard)
```

### Automated Testing

```bash
# Simulate brute-force attack
for i in {1..10}; do
  curl -X POST http://localhost/standalone.php \
    -d "log=admin$i&pwd=password$i" \
    -s -o /dev/null
done
```

## File Structure

```
HonnyPotter/
├── standalone.php           # Standalone honeypot endpoint
├── wp-login.php             # WordPress login endpoint
├── honeybee-forwarder.php   # HoneyBee event forwarder
├── class.honnypotter.php    # Core plugin class
├── class.honnypotter-admin.php  # Admin interface
├── honnypotter.php          # WordPress plugin loader
├── install.sh               # Installation script (Linux/macOS)
├── install.ps1              # Installation script (Windows)
├── README.md                # This file
└── logs/                    # Log directory (created on install)
    └── honnypotter.log      # Local log file
```

## Requirements

- **PHP:** >= 7.4
- **PHP Extensions:**
  - `json` - JSON encoding/decoding
  - `sockets` - TCP socket communication (for HoneyBee)
- **Web Server:** Apache, Nginx, or PHP built-in server
- **HoneyBee Node:** Running and listening on `localhost:9100`

## Security Notes

⚠️ **Important:** This honeypot logs all failed login attempts, including passwords. 

- Logs may contain sensitive information
- Secure log file permissions (chmod 600)
- Regularly rotate and archive logs
- Do not expose log files publicly
- Use HTTPS in production

## Troubleshooting

### Events Not Reaching HoneyBee Node

1. **Check Node is running:**
   ```bash
   # Verify node is listening on port 9100
   netstat -an | grep 9100
   ```

2. **Check PHP sockets extension:**
   ```bash
   php -m | grep sockets
   ```

3. **Test connection manually:**
   ```bash
   php -r "require 'honeybee-forwarder.php'; honeybee_forward_event('test', 'test');"
   ```

4. **Check error logs:**
   ```bash
   tail -f /var/log/php_errors.log
   ```

### Log File Not Created

- Check directory permissions: `chmod 755 logs/`
- Check PHP write permissions
- Verify `HONEYBEE_ENABLE_FILE_LOG` is not set to `false`

## License

GPLv2 or later (WordPress plugin license)

## Credits

Original plugin by Martin Ingesen  
HoneyBee integration by HoneyBee Project

## Related

- [HoneyBee PotStore](../README.md)
- [HoneyBee Node](../../honeybee_node/README.md)
- [HoneyBee Core](../../honeybee_core/README.md)
