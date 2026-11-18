#!/usr/bin/env bash
# Verify the OFF leg (after clearing the stale latch from the previous test) and measure the
# final ON latency with the reordered fast path in the hook.
HA=http://127.0.0.1:8123
T=$(cat ~/.config/motion/hass-token)
SW='switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1'
BOOL='input_boolean.tavern_motion_now'
SENS='binary_sensor.taverna_motion'
st() { curl -s -m 8 -H "Authorization: Bearer $T" "$HA/api/states/$1" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("state"))'; }
mark() { echo "$(date '+%H:%M:%S') $*"; }

mark "clearing the latch left by the previous test: hook end"
~/.local/libexec/tavern-motion-hook.sh end
mark "  boolean=$(st $BOOL) sensor=$(st $SENS) switch=$(st $SW)"
t0=$(date +%s)
while [ $(( $(date +%s) - t0 )) -lt 420 ]; do
    if [ "$(st $SW)" = "off" ]; then mark "  light went OFF after $(( $(date +%s) - t0 )) s (sensor delay_off 5 min + automation)"; break; fi
    sleep 5
done
mark "  states now: sensor=$(st $SENS) switch=$(st $SW)"

TD=$(mktemp -d); echo $(( $(date +%s) - 120 )) > "$TD/start-ts"; echo 0 > "$TD/last-post"
mark "forced ON test with the reordered hook: switch=$(st $SW)"
S=$(date +%s%3N)
STATE_DIR="$TD" ~/.local/libexec/tavern-motion-hook.sh start >/dev/null 2>&1
while [ $(( $(date +%s%3N) - S )) -lt 8000 ]; do
    [ "$(st $SW)" = "on" ] && break
    sleep 0.05
done
mark "  switch reached 'on' after $(( $(date +%s%3N) - S )) ms  (boolean=$(st $BOOL) sensor=$(st $SENS))"
mark "heartbeat file: $(ls -l ~/.local/state/tavern-motion/heartbeat 2>/dev/null | awk '{print $6,$7,$8,$9}')"
mark "closing the event through the real hook (end)"
HB_FILE=~/.local/state/tavern-motion/heartbeat ~/.local/libexec/tavern-motion-hook.sh end
mark "  final: boolean=$(st $BOOL) sensor=$(st $SENS) switch=$(st $SW)  (the lamp follows HA's 5-minute delay)"
rm -rf "$TD"
mark "=== done"
