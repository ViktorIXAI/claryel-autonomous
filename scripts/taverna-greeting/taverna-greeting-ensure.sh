#!/bin/sh
# Keep the taverna greeting listener alive. Prints only when something had to be fixed, so a
# cron tick with no output means the listener was already answering (watchdog pattern).
STATE=~/.local/state/taverna-greeting
mkdir -p "$STATE"
if wget -q -O- http://127.0.0.1:8124/ping >/dev/null 2>&1; then
  exit 0
fi
setsid nohup python3 ~/.hermes/scripts/taverna-greeting-listen.py >> "$STATE/listener.log" 2>&1 &
sleep 3
if wget -q -O- http://127.0.0.1:8124/ping >/dev/null 2>&1; then
  echo "TAVERNA GREETING LISTENER RESTARTED: $(tail -1 "$STATE/listener.log")"
else
  echo "TAVERNA GREETING LISTENER DOWN: $(tail -3 "$STATE/listener.log" | tr '\n' ' ')"
fi
