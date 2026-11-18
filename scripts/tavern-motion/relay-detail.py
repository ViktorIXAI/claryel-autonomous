import sqlite3, json, datetime
c = sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro", uri=True)
A = datetime.datetime(2026, 11, 18, 0, 0, tzinfo=datetime.timezone.utc).timestamp()

def tsv(v):
    return "?" if not isinstance(v, (int, float)) else datetime.datetime.fromtimestamp(
        v, datetime.timezone.utc).strftime("%H:%M:%S")

for ent in ("sensor.taverna_taverna_basicr4_sonoff_1002bd4e01_action",
            "select.taverna_taverna_basicr4_sonoff_1002bd4e01_1"):
    print("=== %s (today, transitions) ===" % ent)
    prev = None
    opts = None
    for st, up, attr in c.execute(
            "select state, last_updated_ts, attributes from states s "
            "join states_meta m on m.metadata_id=s.metadata_id "
            "where m.entity_id=? and last_updated_ts>? order by state_id", (ent, A)):
        if attr:
            a = json.loads(attr)
            if a.get("options"):
                opts = a["options"]
        if st == prev:
            continue
        prev = st
        print("   %s  %s" % (tsv(up), st))
    if opts:
        print("   options:", opts)
    last = c.execute("select state from states s join states_meta m on m.metadata_id=s.metadata_id "
                     "where m.entity_id=? order by state_id desc limit 1", (ent,)).fetchone()
    print("   current:", last[0] if last else None)

print("=== unavailable episodes for the relay today ===")
n = 0
prev = None
for st, up in c.execute(
        "select state, last_updated_ts from states s join states_meta m on m.metadata_id=s.metadata_id "
        "where m.entity_id='switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1' and last_updated_ts>? "
        "order by state_id", (A,)):
    if st == prev:
        continue
    if st == "unavailable":
        n += 1
        print("   unavailable at", tsv(up))
    prev = st
print("   episodes:", n)
