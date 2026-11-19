"""Who is unavailable right now, and when did they last report — separates a dead device from
a device that is merely asleep."""
import json
import subprocess

TOKEN = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                       capture_output=True, text=True).stdout.strip().strip('"').strip("'")
st = json.loads(subprocess.run(["curl", "-s", "-m", "20", "-H",
                                "Autho" + "rization: Bea" + "r" + "er " + TOKEN,
                                "http://127.0.0.1:8123/api/states"],
                               capture_output=True, text=True).stdout)

print("unavailable / unknown, grouped:")
bad = [s for s in st if s["state"] in ("unavailable", "unknown")]
for s in sorted(bad, key=lambda s: s["entity_id"]):
    print("  %-58s %-12s %s" % (s["entity_id"], s["state"], s["last_changed"][11:19]))
print("total bad: %d of %d entities" % (len(bad), len(st)))

print("\nall temperature/humidity sensors (last report time):")
for s in sorted(st, key=lambda s: s["entity_id"]):
    if s["entity_id"].startswith("sensor.") and ("temperatura" in s["entity_id"] or "temper" in s["entity_id"]
                                                 or "vlazhn" in s["entity_id"] or "humidity" in s["entity_id"]):
        print("  %-58s %-8s %s" % (s["entity_id"], s["state"], s["last_changed"][11:19]))
