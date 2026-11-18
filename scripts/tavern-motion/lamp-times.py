import sqlite3, datetime, time
c = sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro", uri=True)

def tsv(v):
    return "?" if not isinstance(v, (int, float)) else datetime.datetime.fromtimestamp(
        v, datetime.timezone.utc).strftime("%m-%d %H:%M:%S")

print("recorder window:", tsv(c.execute("select min(last_updated_ts) from states").fetchone()[0]),
      "->", tsv(c.execute("select max(last_updated_ts) from states").fetchone()[0]))

for ent in ("switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1",
            "automation.taverna_dvizhenie_vkliuchit_svet",
            "automation.taverna_5_minut_bez_dvizheniia_vykliuchit_svet",
            "automation.taverna_vkliuchit_slepoe_okno_kamery_pri_vkliuchenii_sveta",
            "automation.taverna_vykliuchit_slepoe_okno_kamery",
            "input_boolean.tavern_light_blind"):
    print("=== %s ===" % ent)
    prev = None
    for st, up in c.execute(
            "select state, last_updated_ts from states s "
            "join states_meta m on m.metadata_id=s.metadata_id "
            "where m.entity_id=? order by state_id", (ent,)):
        if st == prev:
            continue
        prev = st
        print("   %-12s at %s" % (st, tsv(up)))
