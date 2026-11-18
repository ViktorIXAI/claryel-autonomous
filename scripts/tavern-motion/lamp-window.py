import sqlite3, json, datetime
c = sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro", uri=True)
A = datetime.datetime(2026, 11, 18, 4, 30, tzinfo=datetime.timezone.utc).timestamp()
B = datetime.datetime(2026, 11, 18, 13, 40, tzinfo=datetime.timezone.utc).timestamp()

def tsv(v):
    return "?" if not isinstance(v, (int, float)) else datetime.datetime.fromtimestamp(
        v, datetime.timezone.utc).strftime("%H:%M:%S")

def payload(data, did):
    if data:
        return data
    if did is not None:
        row = c.execute("select event_data from event_data where data_id=?", (did,)).fetchone()
        if row:
            return row[0]
    return None

print("=== all service calls in 04:30-13:40 UTC (13:30 local start) ===")
for cts, data, did, org, usr in c.execute(
        "select time_fired_ts, event_data, data_id, origin_idx, context_user_id from events "
        "where event_type='call_service' and time_fired_ts between ? and ? order by event_id", (A, B)):
    p = payload(data, did)
    if not p:
        continue
    d = json.loads(p)
    svc = (d.get("domain") or "") + "." + (d.get("service") or "")
    sd = d.get("service_data") or {}
    if "tavern" in json.dumps(sd).lower() or "basicr4" in json.dumps(sd).lower():
        print("  %s  %-34s %-40s user=%s origin=%s" % (
            tsv(cts), svc, json.dumps(sd, ensure_ascii=False)[:60], (usr or "-")[:8], org))

print("=== switch rows with attributes in that window ===")
for st, up, attr, usr, org in c.execute(
        "select s.state, s.last_updated_ts, s.attributes, s.context_user_id, s.origin_idx from states s "
        "join states_meta m on m.metadata_id=s.metadata_id "
        "where m.entity_id='switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1' "
        "and s.last_updated_ts between ? and ? order by s.state_id", (A, B)):
    a = json.loads(attr) if attr else {}
    print("  %s %-11s friendly=%s user=%s origin=%s" % (
        tsv(up), st, a.get("friendly_name"), (usr or "-")[:8], org))

print("=== motion sensor + latch in that window (transitions only) ===")
for ent in ("binary_sensor.taverna_motion", "input_boolean.tavern_motion_now"):
    print("  --", ent)
    prev = None
    for st, up in c.execute(
            "select state, last_updated_ts from states s join states_meta m on m.metadata_id=s.metadata_id "
            "where m.entity_id=? and last_updated_ts between ? and ? order by state_id", (ent, A, B)):
        if st == prev:
            continue
        prev = st
        print("     %s %s" % (tsv(up), st))

print("=== automation attributes (last_triggered) at the latest rows ===")
for ent in ("automation.taverna_dvizhenie_vkliuchit_svet",
            "automation.taverna_5_minut_bez_dvizheniia_vykliuchit_svet",
            "automation.taverna_flazhok_dvizheniia_gorit_slishkom_dolgo_sniat"):
    row = c.execute(
        "select s.attributes, s.last_updated_ts from states s join states_meta m on m.metadata_id=s.metadata_id "
        "where m.entity_id=? order by s.state_id desc limit 1", (ent,)).fetchone()
    if row and row[0]:
        a = json.loads(row[0])
        print("  %-62s last_triggered=%s last_action=%s" % (
            ent, a.get("last_triggered"), a.get("last_action")))
