#!/usr/bin/env bash
# Tavern camera night test: does the picture become usable when the lamp lights the room?
# The greeting/music automations are muted for the duration so nothing plays at 03:40,
# and input_boolean.tavern_light_manual is raised so the ghost-light cutoff stands down.
set -u
T=$(grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-)
H="http://127.0.0.1:8123/api"
AUTH="Authorization: Bearer $T"
SW=switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
OUT=~/.hermes/cache/scratch/night-test
mkdir -p "$OUT"; cd "$OUT"

post() { curl -s --max-time 15 -X POST -H "$AUTH" -H 'Content-Type: application/json' "$H/services/$1" -d "$2"; echo; }

bright() {
  ffmpeg -v info -i "$1" -vf "signalstats,metadata=print" -frames:v 1 -f null - 2>&1 \
    | grep -oE "Y(AVG|MIN|MAX)=[0-9.]+" | sort -u | tr '\n' ' '
}

echo "=== 0. mute greeting, raise manual flag, verify relay reachable"
post homeassistant/update_entity_state '{"entity_id":"automation.taverna_greeting_voice","state":"off"}'
post input_boolean/turn_on   '{"entity_id":"input_boolean.tavern_light_manual"}'
curl -s --max-time 10 -H "$AUTH" "$H/states/$SW" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("relay:",d["state"],d["attributes"].get("friendly_name"))'

echo "=== 1. dark frames (lamp off)"
for i in 1 2; do
  curl -s --max-time 8 -o "dark$i.jpg" "http://127.0.0.1:8126/frame.jpg"
  printf "   dark%s: %s bytes | " "$i" "$(stat -c%s dark$i.jpg)"; bright "dark$i.jpg"; echo
  sleep 2
done

echo "=== 2. lamp ON, frames at ~3 s and ~15 s"
post switch/turn_on "{\"entity_id\":\"$SW\"}"
sleep 3;  curl -s --max-time 8 -o "lit1.jpg" "http://127.0.0.1:8126/frame.jpg"
printf "   lit1:  %s bytes | " "$(stat -c%s lit1.jpg)"; bright lit1.jpg; echo
sleep 12; curl -s --max-time 8 -o "lit2.jpg" "http://127.0.0.1:8126/frame.jpg"
printf "   lit2:  %s bytes | " "$(stat -c%s lit2.jpg)"; bright lit2.jpg; echo

echo "=== 3. motion saw the lamp coming on?"
journalctl -u motion-tavern.service --since "-3 min" -o short-iso --no-pager 2>/dev/null \
  | grep -iE "starting event|End of event|light switch|changing thresholds" | tail -8

echo "=== 4. restore: lamp off, manual flag off, greeting back on"
post switch/turn_off "{\"entity_id\":\"$SW\"}"
sleep 2
post input_boolean/turn_off '{"entity_id":"input_boolean.tavern_light_manual"}'
post homeassistant/update_entity_state '{"entity_id":"automation.taverna_greeting_voice","state":"on"}'
for e in "$SW" input_boolean.tavern_light_manual automation.taverna_greeting_voice; do
  curl -s --max-time 10 -H "$AUTH" "$H/states/$e" | python3 -c 'import json,sys; d=json.load(sys.stdin); print("   ",d["entity_id"],"=",d["state"])'
done
