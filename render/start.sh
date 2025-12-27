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
exec icecast2 -c /app/icecast.runtime.xml
