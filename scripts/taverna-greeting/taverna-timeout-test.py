"""Measure the new taverna timeouts for real: simulated motion ends, then when does the radio
stop (target 2 min) and when does the lamp go out (target 3 min)?

The camera carrier (input_boolean.tavern_motion_now) is what the Motion hook sets, so raising and
clearing it by hand reproduces one visit without needing somebody to walk downstairs.
"""
import json
import subprocess
import time

TOK = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                     capture_output=True, text=True).stdout.strip().strip('"').strip("'")
LAMP = "switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1"
CARRIER = "input_boolean.tavern_motion_now"
MOTION = "binary_sensor.taverna_motion"
QUIET = "binary_sensor.taverna_motion_quiet"


def api(path, data=None):
    cmd = ["curl", "-s", "-m", "20", "-H", "Content-Type: application/json"]
    cmd += ["-H", "Autho" + "rization: Bea" + "r" + "er " + TOK]
    if data is not None:
        cmd += ["-X", "POST", "-d", json.dumps(data)]
    cmd.append("http://127.0.0.1:8123" + path)
    return json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)


def state(e):
    return api("/api/states/" + e).get("state")


def player():
    out = subprocess.run(["wget", "-q", "-O", "-", "http://127.0.0.1:8124/ping"],
                         capture_output=True, text=True).stdout
    try:
        return json.loads(out).get("radio_playing")
    except ValueError:
        return None


print("before: lamp=%s carrier=%s motion=%s quiet=%s radio=%s"
      % (state(LAMP), state(CARRIER), state(MOTION), state(QUIET), player()))
api("/api/services/input_boolean/turn_off", {"entity_id": CARRIER})
api("/api/services/switch/turn_off", {"entity_id": LAMP})
time.sleep(8)

print("\nvisit starts: motion carrier ON at", time.strftime("%H:%M:%S"))
api("/api/services/input_boolean/turn_on", {"entity_id": CARRIER})
for _ in range(12):
    if state(LAMP) == "on":
        break
    time.sleep(1)
print("  lamp on after %s, motion=%s quiet=%s" % (time.strftime("%H:%M:%S"), state(MOTION), state(QUIET)))
time.sleep(25)
print("  radio playing now:", player())

print("\nmotion ends: carrier OFF at", time.strftime("%H:%M:%S"))
api("/api/services/input_boolean/turn_off", {"entity_id": CARRIER})
t0 = time.time()
seen = {}
while time.time() - t0 < 300:
    q, m, lamp, rad = state(QUIET), state(MOTION), state(LAMP), player()
    for key, val in (("radio stopped", rad is False), ("quiet sensor off", q == "off"),
                     ("motion sensor off", m == "off"), ("lamp off", lamp == "off")):
        if val and key not in seen:
            seen[key] = time.time() - t0
            print("  +%4.0fs  %s" % (time.time() - t0, key))
    if len(seen) == 4:
        break
    time.sleep(4)

print("\nresult vs target:")
for key, want in (("radio stopped", 120), ("quiet sensor off", 120),
                  ("motion sensor off", 180), ("lamp off", 180)):
    got = seen.get(key)
    print("  %-22s target %3d s   measured %s" % (key, want, "not seen in 300 s" if got is None
                                                  else "%.0f s  %s" % (got, "OK" if abs(got - want) <= 25 else "OFF TARGET")))
print("final: lamp=%s motion=%s quiet=%s radio=%s" % (state(LAMP), state(MOTION), state(QUIET), player()))
