import sqlite3, json, datetime, time
c = sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro", uri=True)
CUT = time.time() - 96 * 3600

def ts(v):
    return "?" if not isinstance(v, (int, float)) else datetime.datetime.fromtimestamp(
        v, datetime.timezone.utc).strftime("%m-%d %H:%M:%S")

ORIGIN = {0: "device_push", 1: "system_options", 2: "restored", 3: "device_button",
          4: "external(HA call)", 5: "auth", 6: "automatic", 7: "local_api", 8: "cloud_api"}

def history(ent, cut=CUT, transitions_only=True):
    print("=== %s ===" % ent)
    prev = None
    rows = list(c.execute(
        "select state, last_changed_ts, last_updated_ts, origin_idx, context_user_id from states s "
        "join states_meta m on m.metadata_id=s.metadata_id "
        "where m.entity_id=? and last_updated_ts>? order by state_id", (ent, cut)))
    print("  recorded rows:", len(rows))
    for st, ch, up, org, usr in rows:
        if transitions_only and st == prev:
            continue
        prev = st
        print("  changed %s -> %-4s | origin %-18s | user %s" % (
            ts(ch), st, ORIGIN.get(org, org), usr or "-"))

history("switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1")
history("binary_sensor.taverna_motion", cut=time.time() - 40 * 3600)
history("input_boolean.tavern_motion_now", cut=time.time() - 40 * 3600)
history("input_boolean.tavern_light_blind")
history("automation.taverna_dvizhenie_vkliuchit_svet", cut=time.time() - 40 * 3600)
history("automation.taverna_5_minut_bez_dvizheniia_vykliuchit_svet", cut=time.time() - 40 * 3600)
history("automation.taverna_vkliuchit_slepoe_okno_kamery_pri_vkliuchenii_sveta")
history("automation.taverna_vykliuchit_slepoe_okno_kamery")

print("=== service-call events mentioning the relay (96 h) ===")
n = 0
for et, cts, data, did, org in c.execute(
        "select event_type, time_fired_ts, event_data, data_id, origin_idx from events "
        "where event_type='call_service' and time_fired_ts>? order by event_id", (CUT,)):
    payload = data
    if payload is None and did is not None:
        try:
            payload = c.execute("select event_data from event_data where data_id=?", (did,)).fetchone()[0]
        except Exception:
            pass
    if payload and "basicr4" in payload:
        d = json.loads(payload)
        print("  ", ts(cts), d.get("domain") and (d["domain"] + "." + d["service"]), d.get("service_data"))
        n += 1
print("  matches:", n)

print("=== automations in the registry: what triggers the tavern light ===")
cfg = open("/config/configuration.yaml").read()
i = cfg.find("automation:")
print(cfg[i:i + 200])
