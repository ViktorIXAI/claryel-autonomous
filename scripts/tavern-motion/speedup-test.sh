#!/usr/bin/env bash
# Regression + latency test for the tavern motion chain after the speed-up.
# Writes a timestamped log; changes nothing except switching the tavern relay on/off.
HA=http://127.0.0.1:8123
T=$(cat ~/.config/motion/hass-token)
SW='switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1'
BOOL='input_boolean.tavern_motion_now'
SENS='binary_sensor.taverna_motion'
LOG=~/.hermes/cache/tavern-motion/speedup-test.log

st() { curl -s -m 8 -H "Authorization: Bearer $T" "$HA/api/states/$1" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("state"))' ; }
call() { curl -s -m 8 -X POST -H "Authorization: Bearer $T" -H 'Content-Type: application/json' \
    "$HA/api/services/$1/$2" -d "{\"entity_id\":\"$SW\"}" -o /dev/null -w '%{http_code}'; }
ev() { journalctl -u motion-tavern.service --since "$1" --no-pager -o short-iso 2>/dev/null | grep -ciE "motion detected - starting event"; }
mark() { echo "$(date '+%H:%M:%S') $*"; }

mark "=== switch state at start: $(st $SW)"
call switch turn_off >/dev/null; sleep 15
A0=$(date -d 'now' '+%Y-%m-%d %H:%M:%S'); mark "window A (dark idle) start"
sleep 120
mark "window A events: $(ev "$A0")  sensor=$(st $SENS) switch=$(st $SW)"

B0=$(date -d 'now' '+%Y-%m-%d %H:%M:%S'); mark "window B (lamp on/off brightness step) start"
mark "  turn_on http=$(call switch turn_on)"; sleep 20
mark "  turn_off http=$(call switch turn_off)"; sleep 60
mark "window B events: $(ev "$B0")  sensor=$(st $SENS) switch=$(st $SW)"

# forced event through the real hook: measures hook -> HA -> Zigbee relay latency
TD=$(mktemp -d); echo $(( $(date +%s) - 120 )) > "$TD/start-ts"; echo 0 > "$TD/last-post"
mark "forced hook start: sensor=$(st $SENS) switch=$(st $SW)"
S=$(date +%s%3N)
STATE_DIR="$TD" ~/.local/libexec/tavern-motion-hook.sh start >/dev/null 2>&1
while [ $(( $(date +%s%3N) - S )) -lt 8000 ]; do
    [ "$(st $SW)" = "on" ] && break
    sleep 0.1
done
E=$(date +%s%3N)
mark "switch reached 'on' after $((E-S)) ms   boolean=$(st $BOOL) sensor=$(st $SENS)"
sleep 6
mark "after 6 s: sensor=$(st $SENS) (delay_on is 1 s; the ON automation is the backup path)"
FULL0=$(date -d 'now' '+%Y-%m-%d %H:%M:%S')
mark "waiting 320 s to confirm the 5-minute auto-off still works"
sleep 320
mark "auto-off check: switch=$(st $SW) sensor=$(st $SENS) boolean=$(st $BOOL)"
C0=$(date -d "$FULL0" '+%Y-%m-%d %H:%M:%S')
mark "camera events during the whole watch: $(ev '2026-11-18 04:55:00')"
rm -rf "$TD"
mark "=== done"
