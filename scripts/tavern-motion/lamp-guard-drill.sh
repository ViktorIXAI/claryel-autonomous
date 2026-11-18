#!/usr/bin/env bash
# Lamp safety-net drill: simulate the uncommanded ON state seen at 06:01 on 2026-11-18
# (relay on, motion chain silent) and prove the new automation switches it off after 10 min.
set -u
TOK=$(cat ~/.config/motion/hass-token)
H=http://127.0.0.1:8123/api
SW=switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
st() { curl -s -m 8 -H "Authorization: Bearer $TOK" "$H/states/$1" \
        | python3 -c 'import json,sys;d=json.load(sys.stdin);print(d.get("state","?"))'; }
log() { printf '%s %s\n' "$(date +%H:%M:%S)" "$*"; }

J0=$(journalctl -u motion-tavern.service --since "$(date '+%H:%M:%S')" --no-pager 2>/dev/null | grep -c "Motion detected - starting event")
echo "state before: lamp=$(st $SW) sensor=$(st binary_sensor.taverna_motion) manual=$(st input_boolean.tavern_light_manual)"
log "commanding the relay ON by hand (that is what the device did by itself at 06:01)"
curl -s -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' -d '{}' "$H/services/switch/turn_on" \
  -o /dev/null -w 'turn_on http=%{http_code}\n'
python3 - "$SW" <<'PY'
import json, sys, urllib.request, time, datetime
tok = open(__import__("os").path.expanduser("~/.config/motion/hass-token")).read().strip()
ent, base = sys.argv[1], "http://127.0.0.1:8123/api/states/"
def st(e):
    r = urllib.request.Request(base + e, headers={"Authorization": "Bearer " + tok})
    return json.load(urllib.request.urlopen(r, timeout=8)).get("state")
t0 = time.time()
prev = None
while time.time() - t0 < 900:
    s = st(ent)
    if s != prev:
        print("  %s   lamp=%s sensor=%s +%d s" % (
            datetime.datetime.now().strftime("%H:%M:%S"), s, st("binary_sensor.taverna_motion"),
            time.time() - t0), flush=True)
        prev = s
    if s == "off" and time.time() - t0 > 60:
        print("  RESULT: safety net switched the lamp off after %d s (600 s expected)" % (time.time() - t0))
        break
    time.sleep(10)
else:
    print("  RESULT: lamp still %s after 900 s - safety net FAILED" % prev)
PY
echo "motion events during the drill: $(( $(journalctl -u motion-tavern.service --since "$(date -d @$(($(date +%s)-900)) '+%H:%M:%S')" --no-pager 2>/dev/null | grep -c "Motion detected - starting event") )) (0 expected - nobody waved at the camera)"
echo "final: lamp=$(st $SW) sensor=$(st binary_sensor.taverna_motion) manual=$(st input_boolean.tavern_light_manual)"
