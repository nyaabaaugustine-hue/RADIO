#!/bin/sh
set -eu
PORT="${PORT:-8000}"
cp /app/icecast.xml /app/icecast.runtime.xml
sed -i "s|<port>8000</port>|<port>${PORT}</port>|" /app/icecast.runtime.xml
sed -i "s|<bind-address>127.0.0.1</bind-address>|<bind-address>0.0.0.0</bind-address>|" /app/icecast.runtime.xml
HOSTNAME_VAL="${ICECAST_HOSTNAME:-${RENDER_EXTERNAL_URL:-}}"
if [ -n "${HOSTNAME_VAL}" ]; then
  HOSTNAME_VAL="${HOSTNAME_VAL#http://}"
  HOSTNAME_VAL="${HOSTNAME_VAL#https://}"
  HOSTNAME_VAL="${HOSTNAME_VAL%%/*}"
  sed -i "s|<hostname>.*</hostname>|<hostname>${HOSTNAME_VAL}</hostname>|" /app/icecast.runtime.xml
fi
# Optional admin credential override from environment
if [ -n "${ICECAST_ADMIN_USER:-}" ]; then
  sed -i "s|<admin-user>.*</admin-user>|<admin-user>${ICECAST_ADMIN_USER}</admin-user>|" /app/icecast.runtime.xml
fi
if [ -n "${ICECAST_ADMIN_PASSWORD:-}" ]; then
  sed -i "s|<admin-password>.*</admin-password>|<admin-password>${ICECAST_ADMIN_PASSWORD}</admin-password>|" /app/icecast.runtime.xml
fi
exec icecast2 -c /app/icecast.runtime.xml
