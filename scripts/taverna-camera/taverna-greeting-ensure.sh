#!/bin/sh
# Keep the taverna helpers alive: the greeting listener (speaks + radio) and the camera frame-rate
# switcher. Prints only when something had to be fixed, so a cron tick with no output means both
# were already answering (watchdog pattern).
STATE=~/.local/state/taverna-greeting
mkdir -p "$STATE"

if ! wget -q -O- http://127.0.0.1:8124/ping >/dev/null 2>&1; then
  setsid nohup python3 ~/.hermes/scripts/taverna-greeting-listen.py >> "$STATE/listener.log" 2>&1 &
  sleep 3
  if wget -q -O- http://127.0.0.1:8124/ping >/dev/null 2>&1; then
    echo "GREETING LISTENER RESTARTED: $(tail -1 "$STATE/listener.log")"
  else
    echo "GREETING LISTENER DOWN: $(tail -3 "$STATE/listener.log" | tr '\n' ' ')"
  fi
fi

if ! wget -q -O- http://127.0.0.1:8126/ping >/dev/null 2>&1; then
  pkill -f "[t]averna-camera-ctl.py" 2>/dev/null
  sleep 1
  setsid nohup python3 ~/.hermes/scripts/taverna-camera-ctl.py >> "$STATE/camera-ctl.log" 2>&1 &
  sleep 2
  if wget -q -O- http://127.0.0.1:8126/ping >/dev/null 2>&1; then
    echo "CAMERA-CTL RESTARTED: $(tail -1 "$STATE/camera-ctl.log")"
  else
    echo "CAMERA-CTL DOWN: $(tail -3 "$STATE/camera-ctl.log" | tr '\n' ' ')"
  fi
fi
