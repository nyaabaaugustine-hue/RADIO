#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-10000}"
cp /app/icecast.xml /app/icecast.runtime.xml
sed -i "s|<port>8000</port>|<port>${PORT}</port>|" /app/icecast.runtime.xml
sed -i "s|<bind-address>127.0.0.1</bind-address>|<bind-address>0.0.0.0</bind-address>|" /app/icecast.runtime.xml

# Optional env-driven secrets and config
SOURCE_PASSWORD="${ICECAST_SOURCE_PASSWORD:-S0urce_Auth_2025_XyZ9ZB}"
ADMIN_USER="${ICECAST_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${ICECAST_ADMIN_PASSWORD:-Adm1n_PoWer_2025_KLm88}"
RELAY_PASSWORD="${ICECAST_RELAY_PASSWORD:-R3lay_Pass_2025_QpW77}"
ADMIN_EMAIL="${ICECAST_ADMIN_EMAIL:-admin@example.com}"

# Validate passwords: ASCII letters/digits/underscore only, min length 12
validate_secret() {
  local s="$1"
  [[ "${#s}" -ge 12 ]] || { echo "Secret too short"; return 1; }
  [[ "$s" =~ ^[A-Za-z0-9_]+$ ]] || { echo "Secret contains invalid chars"; return 1; }
  return 0
}
validate_secret "${SOURCE_PASSWORD}" || { echo "Invalid ICECAST_SOURCE_PASSWORD"; exit 1; }
validate_secret "${ADMIN_PASSWORD}" || { echo "Invalid ICECAST_ADMIN_PASSWORD"; exit 1; }
validate_secret "${RELAY_PASSWORD}" || { echo "Invalid ICECAST_RELAY_PASSWORD"; exit 1; }
[[ "$ADMIN_USER" =~ ^[A-Za-z0-9_]+$ ]] || { echo "Invalid ICECAST_ADMIN_USER"; exit 1; }

# Apply runtime substitutions
sed -i "s|<source-password>.*</source-password>|<source-password>${SOURCE_PASSWORD}</source-password>|" /app/icecast.runtime.xml
sed -i "s|<admin-user>.*</admin-user>|<admin-user>${ADMIN_USER}</admin-user>|" /app/icecast.runtime.xml
sed -i "s|<admin-password>.*</admin-password>|<admin-password>${ADMIN_PASSWORD}</admin-password>|" /app/icecast.runtime.xml
sed -i "s|<relay-password>.*</relay-password>|<relay-password>${RELAY_PASSWORD}</relay-password>|" /app/icecast.runtime.xml
sed -i "s|<admin>.*</admin>|<admin>${ADMIN_EMAIL}</admin>|" /app/icecast.runtime.xml
HOSTNAME_VAL="${ICECAST_HOSTNAME:-${RENDER_EXTERNAL_URL:-}}"
if [ -n "$HOSTNAME_VAL" ]; then
  HOSTNAME_VAL="${HOSTNAME_VAL#http://}"
  HOSTNAME_VAL="${HOSTNAME_VAL#https://}"
  HOSTNAME_VAL="${HOSTNAME_VAL%%/*}"
  sed -i "s|<hostname>.*</hostname>|<hostname>${HOSTNAME_VAL}</hostname>|" /app/icecast.runtime.xml
fi

exec icecast2 -c /app/icecast.runtime.xml
