#!/bin/bash
# Setup aliyundrive-webdav via pip, connect Alipan to local WebDAV
# Usage: ./setup-aliyundrive-webdav.sh <refresh_token>
# Get refresh_token from browser: localStorage.getItem('token') -> refresh_token

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <refresh_token>"
  echo ""
  echo "To get refresh_token, open alipan.com in browser and run in console:"
  echo "  JSON.parse(localStorage.getItem('token')).refresh_token"
  exit 1
fi

REFRESH_TOKEN="$1"
PORT="${2:-18080}"

echo "Installing aliyundrive-webdav..."
pip3 install aliyundrive-webdav 2>/dev/null || pip install aliyundrive-webdav

echo "Starting WebDAV server on port $PORT..."
echo "Connect in Finder: Cmd+K -> http://127.0.0.1:$PORT"
echo ""

aliyundrive-webdav \
  --refresh-token "$REFRESH_TOKEN" \
  --port "$PORT" \
  --root / \
  --host 127.0.0.1
