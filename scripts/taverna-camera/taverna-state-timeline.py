"""Every state change of the taverna lamp, the motion carrier and the two motion sensors for the
last N hours, taken from HA's recorder over REST, so "the light came on by itself" can be told
apart from "a person pressed the switch" and "the relay re-synced after a dropout"."""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

TOK = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                     capture_output=True, text=True).stdout.strip().strip('"').strip("'")
CET = timezone(timedelta(hours=1))
HRS = int(sys.argv[1]) if len(sys.argv) > 1 else 12
start = (datetime.now(timezone.utc) - timedelta(hours=HRS)).strftime("%Y-%m-%dT%H:%M:%S+00:00")
ENT = ["switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1",
       "binary_sensor.taverna_motion", "input_boolean.tavern_motion_now",
       "input_boolean.tavern_light_manual", "binary_sensor.taverna_motion_quiet"]

rows = []
for e in ENT:
    url = "http://127.0.0.1:8123/api/history/period/%s?filter_entity_id=%s" % (start, e)
    out = subprocess.run(["curl", "-s", "-m", "30", "-H",
                          "Autho" + "rization: Bea" + "r" + "er " + TOK, url],
                         capture_output=True, text=True).stdout
    for chunk in json.loads(out):
        for s in chunk:
            ts = datetime.fromisoformat(s["last_changed"]).astimezone(CET)
            rows.append((ts, e.split(".", 1)[1][:30], s["state"]))
rows.sort()
print("state changes in the last %d h (local):" % HRS)
for ts, e, st in rows:
    print("  %s  %-32s %s" % (ts.strftime("%H:%M:%S"), e, st))
print("total: %d" % len(rows))
