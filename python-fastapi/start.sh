#!/bin/bash
set -e

# Default PORT if not set
RUNTIME_PORT="${RUNTIME_PORT:-8888}" envsubst '${RUNTIME_PORT}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf

# Start both Python apps
python server.py & nginx -g "daemon off;"
