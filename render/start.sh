#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-10000}"
cp /app/icecast.xml /app/icecast.runtime.xml
sed -i "s|<port>8000</port>|<port>${PORT}</port>|" /app/icecast.runtime.xml
sed -i "s|<bind-address>127.0.0.1</bind-address>|<bind-address>0.0.0.0</bind-address>|" /app/icecast.runtime.xml
exec icecast2 -c /app/icecast.runtime.xml -b
