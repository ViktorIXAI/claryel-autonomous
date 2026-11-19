#!/bin/sh
# Start the taverna greeting listener if it is not answering, then report its status.
STATE=~/.local/state/taverna-greeting
mkdir -p "$STATE"
if ! wget -q -O- http://127.0.0.1:8124/ping >/dev/null 2>&1; then
  setsid nohup python3 ~/.hermes/scripts/taverna-greeting-listen.py >> "$STATE/listener.log" 2>&1 &
  sleep 3
fi
wget -q -O- http://127.0.0.1:8124/ping 2>/dev/null || { echo "LISTENER DOWN"; tail -5 "$STATE/listener.log"; }
