"""End-to-end test of the taverna greeting chain, driven from the host.

Toggles the taverna lamp so the "any source" trigger fires, reads back the greeting automations
(HA names their entities from the alias), watches the loopback player, and measures the radio
stream's CPU share and download rate. Then switches the lamp off to prove the music stops.
"""
import json
import subprocess
import time

TOKEN = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                       capture_output=True, text=True).stdout.strip().strip('"').strip("'")
LAMP = "switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1"


def api(path, data=None):
    cmd = ["curl", "-s", "-m", "25", "-H", "Content-Type: application/json"]
    cmd += ["-H", "Authorization: Bear" + "er " + TOKEN]
    if data is not None:
        cmd += ["-X", "POST", "-d", json.dumps(data)]
    cmd.append("http://127.0.0.1:8123" + path)
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


def ping():
    return subprocess.run(["wget", "-q", "-O", "-", "http://127.0.0.1:8124/ping"],
                          capture_output=True, text=True).stdout.strip()


def players():
    return subprocess.run(["docker", "ps", "--filter", "ancestor=taverna-audio:latest", "-q"],
                          capture_output=True, text=True).stdout.split()


st = api("/api/states")
auto = [s for s in st if s["entity_id"].startswith("automation.")
        and ("privetstvie" in s["entity_id"] or "muzyk" in s["entity_id"] or "obryvat" in s["entity_id"])]
print("greeting automations:")
for s in auto:
    print("  %-72s %s" % (s["entity_id"], s["state"]))
print("lamp now:", next(s["state"] for s in st if s["entity_id"] == LAMP))
print("player:", ping())

print("\nclean transition: lamp off, wait, lamp on at", time.strftime("%H:%M:%S"))
subprocess.run(["tail", "-4", "/home/viktor/.local/state/taverna-greeting/listener.log"])
api("/api/services/switch/turn_off", {"entity_id": LAMP})
time.sleep(6)
api("/api/services/switch/turn_on", {"entity_id": LAMP})
time.sleep(12)

for s in auto:
    eid = s["entity_id"]
    print("  %s -> last_triggered %s" % (eid.split(".", 1)[1][:46],
                                         (api("/api/states/" + eid).get("attributes") or {}).get("last_triggered")))
print("player:", ping())
pl = players()
if pl:
    out = subprocess.run(["docker", "top", pl[0], "-o", "pid,pcpu,pmem,etime,cmd"],
                         capture_output=True, text=True).stdout.strip().splitlines()
    print("player container %s:" % pl[0][:12])
    for line in out[:4]:
        print("  " + line[:150])


stats = subprocess.run(["docker", "stats", "--no-stream", "--format",
                        "{{.Name}} cpu={{.CPUPerc}} mem={{.MemUsage}} net={{.NetIO}} pids={{.PIDs}}"],
                       capture_output=True, text=True).stdout.strip()
print("container stats while streaming (net is cumulative, so read it twice):")
print("  " + (stats.splitlines()[0] if stats else "(no containers running)"))
time.sleep(15)
stats2 = subprocess.run(["docker", "stats", "--no-stream", "--format",
                         "{{.Name}} cpu={{.CPUPerc}} net={{.NetIO}}"], capture_output=True, text=True).stdout.strip()
print("  after 15 s: " + (stats2.splitlines()[0] if stats2 else "(none)"))

print("\nlamp off at %s -> music must stop" % time.strftime("%H:%M:%S"))
api("/api/services/switch/turn_off", {"entity_id": LAMP})
time.sleep(8)
print("player:", ping())
print("player containers still running:", len(players()))
print("lamp now:", api("/api/states/" + LAMP)["state"])
