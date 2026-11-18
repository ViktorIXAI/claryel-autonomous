#!/usr/bin/env bash
# Verify: (1) the frame toggle keeps the sensor continuously on (no flicker),
#         (2) the 15-minute HA latch guard clears a latch whose 'end' event was lost,
#         (3) the lamp then goes dark through the normal 5-minute sensor delay.
HA=http://127.0.0.1:8123
T=$(cat ~/.config/motion/hass-token)
SW='switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1'
BOOL='input_boolean.tavern_motion_now'
SENS='binary_sensor.taverna_motion'
st() { curl -s -m 8 -H "Authorization: Bearer $T" "$HA/api/states/$1" | python3 -c 'import json,sys;print(json.load(sys.stdin).get("state"))'; }
mark() { echo "$(date '+%H:%M:%S') $*"; }
fresh_hook() { local d=$(mktemp -d); echo $(( $(date +%s) - 120 )) > "$d/start-ts"; echo 0 > "$d/last-post"; STATE_DIR="$d" ~/.local/libexec/tavern-motion-hook.sh "$@"; rm -rf "$d"; }

mark "start event (latch on, lamp commanded on)"
fresh_hook start
mark "  latch=$(st $BOOL) switch=$(st $SW)"
sleep 3
mark "  sensor after 3 s: $(st $SENS)"

mark "frame toggles at 5/15/25 s while polling the sensor twice a second"
blips=0; prev=$(st $SENS)
end=$(( $(date +%s) + 30 ))
while [ $(date +%s) -lt $end ]; do
    case $(( $(date +%s) - (end - 30) )) in 5|15|25) fresh_hook frame; mark "  sent frame at +$(($(date +%s)-(end-30)))s latch=$(st $BOOL)";; esac
    cur=$(st $SENS)
    if [ "$cur" != "$prev" ] && [ "$cur" = "off" ]; then blips=$((blips+1)); mark "  SENSOR BLIP to off at +$(($(date +%s)-(end-30)))s"; fi
    prev=$cur
    sleep 0.5
done
mark "sensor blips during toggles: $blips (0 expected)  final sensor=$(st $SENS) latch=$(st $BOOL)"

t0=$(date +%s)
mark "no more hook calls; waiting for the 15-min latch guard"
last=""
while [ $(( $(date +%s) - t0 )) -lt 1560 ]; do
    l=$(st $BOOL); s=$(st $SW)
    if [ "$l" != "$last" ]; then mark "  latch -> $l at +$(( ($(date +%s)-t0)/60 )) min"; last=$l; fi
    if [ "$l" = "off" ] && [ "$s" = "off" ]; then mark "  lamp is OFF at +$(( $(date +%s)-t0 ))s after the last motion frame"; break; fi
    sleep 10
done
mark "final: latch=$(st $BOOL) sensor=$(st $SENS) switch=$(st $SW)"
mark "guard automation last_triggered:"
curl -s -m 8 -H "Authorization: Bearer $T" "$HA/api/states/automation.taverna_flazhok_dvizheniia_gorit_slishkom_dolgo_sniat" | python3 -c 'import json,sys;print(" ",json.load(sys.stdin).get("attributes",{}).get("last_triggered"))'
mark "=== done"
