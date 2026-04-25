#!/bin/bash
# WebTrap installation script for HoneyBee.
set -e

POT_ID="${HONEYBEE_POT_ID:-webtrap-01}"
INSTALL_DIR="${1:-$(pwd)}"
LOG_DIR="${INSTALL_DIR}/logs"
UPLOAD_DIR="${INSTALL_DIR}/captured_uploads"

echo "🍯 Installing WebTrap for HoneyBee..."
echo "   Pot ID:            ${POT_ID}"
echo "   Install Directory: ${INSTALL_DIR}"
echo ""

mkdir -p "${LOG_DIR}" "${UPLOAD_DIR}"
chmod 755 "${LOG_DIR}" "${UPLOAD_DIR}"

PY="${PYTHON:-python3}"
if ! command -v "${PY}" >/dev/null 2>&1; then
    echo "❌ Python 3 is required but '${PY}' was not found in PATH" >&2
    exit 1
fi

if [ ! -d "${INSTALL_DIR}/venv" ]; then
    echo "📦 Creating virtualenv..."
    "${PY}" -m venv "${INSTALL_DIR}/venv"
fi

# shellcheck disable=SC1091
. "${INSTALL_DIR}/venv/bin/activate"
pip install --quiet --upgrade pip
pip install --quiet -r "${INSTALL_DIR}/requirements.txt"

cat > "${INSTALL_DIR}/.env" <<EOF
HONEYBEE_POT_ID=${POT_ID}
HONEYBEE_HOST=${HONEYBEE_HOST:-127.0.0.1}
HONEYBEE_PORT=${HONEYBEE_PORT:-9100}
HONEYBEE_ENABLE=${HONEYBEE_ENABLE:-true}
HONEYBEE_ENABLE_FILE_LOG=true
HONEYBEE_LOG_FILE=${LOG_DIR}/webtrap.log
WEBTRAP_BIND_HOST=${WEBTRAP_BIND_HOST:-0.0.0.0}
WEBTRAP_BIND_PORT=${WEBTRAP_BIND_PORT:-8088}
EOF

echo "✅ WebTrap installed successfully"
echo ""
echo "Start it with:"
echo "   cd ${INSTALL_DIR} && . venv/bin/activate && python standalone.py"
echo "Or via Docker:"
echo "   docker compose up -d"
