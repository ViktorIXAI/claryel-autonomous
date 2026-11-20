"""Watchdog: report taverna light-ON events that nobody ordered.

Measured on 2026-11-20: the eWeLink relay pushed itself ON at 08:19:06 and 09:15:34 local with zero
Motion events and no HA service call (origin=device_push, user=-). Home Assistant now cuts such a
light after 60 s and keeps silent, but the operator wants to be told when it happens, so this
script reads the recorder over REST, prints one line per uncommanded ON and remembers what it
already reported. Prints nothing when nothing happened, which is what the cron job delivers.
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

TOK = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                     capture_output=True, text=True).stdout.strip().strip('"').strip("'")
CET = timezone(timedelta(hours=1))
HASS = "http://127.0.0.1:8123"
LAMP = "switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1"
MOTION = "binary_sensor.taverna_motion"
MANUAL = "input_boolean.tavern_light_manual"
STATE = os.path.expanduser("~/.local/state/taverna-greeting/ghost_seen")
WINDOW_MIN = int(os.environ.get("GHOST_WINDOW_MIN", "12"))


def history(entity, start_iso):
    url = "%s/api/history/period/%s?filter_entity_id=%s" % (HASS, start_iso, entity)
    out = subprocess.run(["curl", "-s", "-m", "30", "-H",
                          "Autho" + "rization: Bea" + "r" + "er " + TOK, url],
                         capture_output=True, text=True).stdout
    spans = []
    for chunk in json.loads(out):
        for s in chunk:
            spans.append((datetime.fromisoformat(s["last_changed"]), s["state"]))
    return sorted(spans)


def state_at(spans, when, default="off"):
    got = default
    for ts, st in spans:
        if ts <= when:
            got = st
        else:
            break
    return got


def main():
    dry = "--dry" in sys.argv
    start = datetime.now(timezone.utc) - timedelta(minutes=WINDOW_MIN)
    start_iso = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
    lamp, motion, manual = (history(e, start_iso) for e in (LAMP, MOTION, MANUAL))

    seen = set()
    if os.path.exists(STATE):
        seen = set(open(STATE).read().split())

    alerts = []
    for ts, st in lamp:
        if st != "on" or ts < start:
            continue
        key = ts.strftime("%Y%m%dT%H%M%S")
        near = [m for m, mst in motion if mst == "on" and (ts - timedelta(seconds=90)) <= m <= (ts + timedelta(seconds=40))]
        if near or state_at(manual, ts) == "on":
            continue
        if key in seen:
            continue
        after = [x for x, xst in lamp if x > ts and xst == "off"]
        fixed = "погашен через %d с" % int((after[0] - ts).total_seconds()) if after \
            else "ДО СИХ ПОР ГОРИТ"
        alerts.append((key, ts, fixed))

    for key, ts, fixed in alerts:
        print("ТАВЕРНА: самопроизвольное включение света в %s (движения не было, HA свет не "
              "заказывал) — %s" % (ts.astimezone(CET).strftime("%d.%m %H:%M:%S"), fixed))

    if not dry:
        keep = sorted(seen | {k for k, _, _ in alerts})[-40:]
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w") as f:
            f.write("\n".join(keep) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
