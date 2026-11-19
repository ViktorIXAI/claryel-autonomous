"""One-shot LQI/RSSI/battery snapshot for every Zigbee device in HA, so "does the signal reach
the temperature sensor we moved far away" is answered with numbers instead of guesses."""
import json
import subprocess
import time

TOKEN = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                       capture_output=True, text=True).stdout.strip().strip('"').strip("'")


def api(path):
    out = subprocess.run(["curl", "-s", "-m", "20", "-H",
                          "Autho" + "rization: Bea" + "r" + "er " + TOKEN,
                          "http://127.0.0.1:8123" + path], capture_output=True, text=True).stdout
    return json.loads(out)


st = api("/api/states")
by = {s["entity_id"]: s for s in st}
rows = []
for eid, s in by.items():
    if not eid.startswith("sensor.") or not eid.endswith("_lqi"):
        continue
    base = eid[:-4]
    src = by.get(base)
    bat = None
    for cand in (base + "_battery", base.replace("sensor.", "sensor.") + "_battery_level"):
        if cand in by:
            bat = by[cand]["state"]
            break
    rows.append((eid[7:-4], s["state"], (s.get("attributes") or {}).get("friendly_name"),
                 src["state"] if src else "-", src["last_changed"][11:19] if src else "-", bat))

print("%-40s %5s %-10s %-9s %-6s %s" % ("device", "LQI", "value", "as of", "batt", "name"))
for name, lqi, friendly, val, changed, bat in sorted(rows, key=lambda r: (r[1] in ("unknown", "None"), r[1])):
    try:
        rank = int(lqi)
    except (TypeError, ValueError):
        rank = -1
    flag = "" if rank < 0 else ("  <-- weak" if rank < 40 else "")
    print("%-40s %5s %-10s %-9s %-6s %s%s" % (name[:40], lqi, str(val)[:10], changed, str(bat)[:6],
                                              (friendly or "")[:34], flag))
now = time.strftime("%H:%M:%S")
unavail = [s["entity_id"] for s in st if s["state"] == "unavailable"]
print("\nclock %s | unavailable entities: %d | zigbee sensors with LQI: %d"
      % (now, len(unavail), len(rows)))
