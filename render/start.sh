#!/bin/bash
set -e
# Ensure log directory exists and has correct permissions
mkdir -p /var/log/icecast2
chown -R icecast2:icecast /var/log/icecast2
# Start Icecast in the foreground
echo "Starting Icecast server..."
icecast2 -c /app/icecast.xml
