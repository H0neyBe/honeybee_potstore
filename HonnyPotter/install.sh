#!/bin/bash
# HonnyPotter Installation Script for HoneyBee
# 
# This script sets up HonnyPotter as a standalone honeypot.

set -e

POT_ID="${HONEYBEE_POT_ID:-honnypotter-01}"
INSTALL_DIR="${1:-$(pwd)}"
LOG_DIR="${INSTALL_DIR}/logs"

echo "🍯 Installing HonnyPotter for HoneyBee..."
echo "   Pot ID: ${POT_ID}"
echo "   Install Directory: ${INSTALL_DIR}"
echo ""

# Create logs directory
mkdir -p "${LOG_DIR}"
chmod 755 "${LOG_DIR}"

# Set permissions
chmod 644 *.php
chmod 755 install.sh

# Create .htaccess for Apache (optional)
if [ -f ".htaccess.example" ]; then
    cp .htaccess.example .htaccess
    echo "✅ Created .htaccess"
fi

# Set environment variables
export HONEYBEE_POT_ID="${POT_ID}"
export HONEYBEE_LOG_FILE="${LOG_DIR}/honnypotter.log"
export HONEYBEE_ENABLE="true"
export HONEYBEE_ENABLE_FILE_LOG="true"

echo "✅ HonnyPotter installed successfully!"
echo ""
echo "Configuration:"
echo "   Pot ID: ${POT_ID}"
echo "   Log File: ${HONEYBEE_LOG_FILE}"
echo "   HoneyBee Forwarder: Enabled"
echo ""
echo "To start:"
echo "   1. Configure your web server to point to: ${INSTALL_DIR}/standalone.php"
echo "   2. Or use as WordPress plugin: Copy to wp-content/plugins/HonnyPotter/"
echo "   3. Set HONEYBEE_POT_ID environment variable if different from default"
echo ""
echo "Testing:"
echo "   curl -X POST http://localhost/standalone.php -d 'log=admin&pwd=password123'"

