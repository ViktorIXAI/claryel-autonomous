#!/usr/bin/env python3
"""Radio health watchdog for the house (Zigbee mesh + Wi-Fi relay path).

Prints an alert ONLY when something is wrong or when the set of known problems
changed; empty output means "deliver nothing". A finding is repeated at most
once per RE_ALERT_H, so a permanently dead sensor does not become daily noise.

[RU] Следит за Zigbee-сетью: пропавшие устройства, низкое качество ссылки
(LQI/RSSI из ZHA), севшие батарейки. Ничего не печатает, если проблем нет или
набор проблем не изменился с прошлого доклада.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time

HA_URL = "http://127.0.0.1:8123"          # fixed on purpose: never overridable from cron env
TOKEN_FILE = os.path.expanduser("~/.config/motion/hass-token")
STATE_DIR = os.path.expanduser("~/.local/state/claryel-radio-watch")
STATE_FILE = os.path.join(STATE_DIR, "state.json")
RE_ALERT_H = 24
LQI_MIN = 40            # below this the link is already dropping frames
RSSI_MAX = -92          # dBm
BATT_MIN = 25           # percent
DELIV_WINDOW = "12h"    # how far back to read the HA log
DELIV_MAX = 5           # failed Zigbee sends in that window before it is worth shouting

LQI_PAT = re.compile(r"_(lqi|rssi)(_|$)")
# Entities that define "the device is present"; quality/battery entities are advisory.
PRIMARY_PAT = re.compile(r"_(temperatura|vlazhnost|batareia|dver|dvizhenie|gorenie|vodakanalit)(_|$)")


def delivery_errors():
    """Devices that are online but uncommandable: ZHA logs MAC_NO_ACK / NWK_NO_ROUTE when a
    Zigbee send never reached the device. HA state looks healthy, so this is invisible in
    /api/states — only the container log shows it."""
    try:
        out = subprocess.run(["docker", "logs", "--since", DELIV_WINDOW, "homeassistant"],
                             capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.TimeoutExpired) as exc:
        print("delivery-error scan failed: %s" % exc, file=sys.stderr)
        return 0, []
    hits = [ln for ln in out.stderr.splitlines()
            if "MAC_NO_ACK" in ln or "NWK_NO_ROUTE" in ln]
    who = set()
    for ln in hits:
        m = re.search(r"automation\.([a-z0-9_]+)", ln)
        who.add(m.group(1) if m else "manual/service call")
    return len(hits), sorted(who)


ROLE_WORDS = ("lqi", "rssi", "temperatura", "vlazhnost", "batareia", "dver", "dvizhenie",
              "gorenie", "vodakanalit", "obnovlenie_proshivki", "identifikatsiia",
              "napryazhenie", "soprotivlenie")


def device_key(entity_id):
    """Group entities of one physical device.

    ZHA names several identical models by one base plus a counter suffix
    (wing_ts0201_temperatura, ..._temperatura_3 = different devices), so the role
    word is stripped and the trailing counter stays: that counter IS the device.
    """
    name = entity_id.split(".", 1)[1]
    name = re.sub(r"_(%s)" % "|".join(ROLE_WORDS), "", name)
    return re.sub(r"_{2,}", "_", name).strip("_")


def main():
    try:
        token = open(TOKEN_FILE).read().strip()
    except OSError as exc:
        print("RADIO WATCH BROKEN: cannot read %s (%s)" % (TOKEN_FILE, exc))
        return 0
    if not token:
        print("RADIO WATCH BROKEN: %s is empty" % TOKEN_FILE)
        return 0

    try:
        out = subprocess.run(
            ["curl", "-s", "-m", "20", "-w", "\n%{http_code}",
             "-H", "Authorization: Bearer " + token, HA_URL + "/api/states"],
            capture_output=True, text=True, timeout=30)
    except subprocess.TimeoutExpired:
        print("HA UNREADABLE: /api/states timed out")
        return 0
    body, _, code = out.stdout.rpartition("\n")
    if code != "200":
        # A watchdog that cannot read its source is worse than no watchdog: say so loudly.
        print("HA UNREADABLE: http=%s (radio health not checked)" % (code or "no-reply"))
        return 0
    try:
        states = json.loads(body)
    except ValueError:
        print("HA UNREADABLE: /api/states returned non-JSON")
        return 0

    by_dev = {}
    for st in states:
        eid = st.get("entity_id", "")
        if not eid.startswith(("sensor.", "binary_sensor.", "switch.", "update.")):
            continue
        if "ts0201" not in eid and "snzb" not in eid and "zbmini" not in eid:
            continue                      # only the Zigbee fleet; Wi-Fi relay is covered elsewhere
        key = device_key(eid)
        rec = by_dev.setdefault(key, {"offline": [], "lqi": None, "rssi": None, "batt": None,
                                      "primary_offline": False})
        state = st.get("state")
        if state == "unavailable":
            rec["offline"].append(eid)
            if PRIMARY_PAT.search(eid):
                rec["primary_offline"] = True
            continue
        if LQI_PAT.search(eid):
            try:
                val = float(state)
            except (TypeError, ValueError):
                continue
            if eid.endswith("_lqi") or "_lqi_" in eid:
                rec["lqi"] = val
            else:
                rec["rssi"] = val
        elif "batareia" in eid:
            try:
                rec["batt"] = float(state)
            except (TypeError, ValueError):
                pass

    # A TS0201 battery channel is noisy: one run saw 1 % while the same device reported
    # 100 % an hour later (60-day history shows 4 distinct values in 10 days). Alert only on
    # two consecutive low readings - a real dying battery still gets reported within a day.
    prev_low = {}
    if os.path.exists(STATE_FILE):
        try:
            prev_low = json.load(open(STATE_FILE)).get("batt_low", {})
        except (ValueError, OSError):
            prev_low = {}

    findings, cur_low = [], {}

    def add(msg):
        # The dedup key drops the digits: a sensor whose LQI bounces 7 -> 0 -> 21 is ONE problem,
        # not a new one, and must not re-alert on every tick.
        findings.append((re.sub(r"\d+", "#", msg), msg))

    for key, rec in sorted(by_dev.items()):
        if rec["primary_offline"] or len(rec["offline"]) >= 3:
            add("ZIGBEE OFFLINE: %s (%d entities unavailable)" % (key, len(rec["offline"])))
        if rec["lqi"] is not None and rec["lqi"] < LQI_MIN:
            add("ZIGBEE LINK WEAK: %s LQI=%d (below %d)" % (key, int(rec["lqi"]), LQI_MIN))
        if rec["rssi"] is not None and rec["rssi"] < RSSI_MAX:
            add("ZIGBEE LINK WEAK: %s RSSI=%d dBm (below %d)" % (key, int(rec["rssi"]), RSSI_MAX))
        if rec["batt"] is not None and rec["batt"] < BATT_MIN:
            cur_low[key] = rec["batt"]
            if key in prev_low:
                add("BATTERY LOW (confirmed twice): %s = %d %%" % (key, int(rec["batt"])))

    n_err, who = delivery_errors()
    if n_err > DELIV_MAX:
        # the count stays out of the message so a repeating incident dedups instead of re-alerting
        print("failed Zigbee sends in %s: %d" % (DELIV_WINDOW, n_err), file=sys.stderr)
        add("ZIGBEE SENDS NOT REACHING DEVICES (device looks online but cannot be commanded): %s"
            % ", ".join(who[:4]))

    os.makedirs(STATE_DIR, exist_ok=True)
    prev = {"keys": [], "at": 0}
    if os.path.exists(STATE_FILE):
        try:
            prev = json.load(open(STATE_FILE))
        except (ValueError, OSError):
            pass
    prev_keys = set(prev.get("keys", prev.get("findings", [])))
    keys = {k for k, _ in findings}

    now = time.time()
    changed = prev_keys != keys
    stale = (now - prev.get("at", 0)) > RE_ALERT_H * 3600
    if not findings:
        for k in sorted(prev_keys):
            print("RADIO RESTORED: %s" % k)
        json.dump({"keys": [], "at": now, "batt_low": cur_low}, open(STATE_FILE, "w"))
        return 0
    if not changed and not stale:
        return 0                            # same problem, already reported recently
    print("RADIO PROBLEMS (%d)%s:" % (len(findings),
                                      " — unchanged since last report" if not changed else ""))
    for _, msg in findings:
        print("  " + msg)
    for k in sorted(prev_keys - keys):
        print("  RADIO RESTORED: " + k)
    json.dump({"keys": sorted(keys), "at": now, "batt_low": cur_low}, open(STATE_FILE, "w"))
    return 0
    json.dump({"findings": findings, "at": now, "batt_low": cur_low}, open(STATE_FILE, "w"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
