import sqlite3, json, datetime, time, subprocess
c = sqlite3.connect("file:/config/home-assistant_v2.db?mode=ro", uri=True)
CUT = time.time() - 45 * 60

def tsv(v):
    return "?" if not isinstance(v, (int, float)) else (
        datetime.datetime.fromtimestamp(v, datetime.timezone.utc)
        .astimezone().strftime("%H:%M:%S"))

print("=== HA transitions, last 45 min (local) ===")
for ent in ("binary_sensor.taverna_motion", "input_boolean.tavern_motion_now",
            "switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1",
            "input_boolean.tavern_light_manual"):
    prev = None
    line = []
    for st, up in c.execute(
            "select state, last_updated_ts from states s join states_meta m on m.metadata_id=s.metadata_id "
            "where m.entity_id=? and last_updated_ts>? order by state_id", (ent, CUT)):
        if st == prev:
            continue
        prev = st
        line.append("%s=%s" % (tsv(up), st))
    print("  %-52s %s" % (ent.split(".", 1)[1], "  ".join(line) or "(no change)"))

print("=== automation last_triggered (local) ===")
for ent in ("automation.taverna_dvizhenie_vkliuchit_svet",
            "automation.taverna_5_minut_bez_dvizheniia_vykliuchit_svet",
            "automation.taverna_svet_gorit_bez_dvizheniia_vykliuchit",
            "automation.taverna_flazhok_dvizheniia_gorit_slishkom_dolgo_sniat"):
    row = c.execute("select attributes from states s join states_meta m on m.metadata_id=s.metadata_id "
                    "where m.entity_id=? order by state_id desc limit 1", (ent,)).fetchone()
    a = json.loads(row[0]) if row and row[0] else {}
    lt = a.get("last_triggered")
    if isinstance(lt, str):
        dt = datetime.datetime.fromisoformat(lt.replace("Z", "+00:00")).astimezone()
        lt = dt.strftime("%H:%M:%S")
    print("  %-64s %s" % (ent.split(".", 1)[1], lt or "-"))

print("=== Motion journal, last 45 min ===")
out = subprocess.run(["journalctl", "-u", "motion-tavern.service", "--since", "45 min ago",
                      "--no-pager", "-o", "short"], capture_output=True, text=True).stdout
ev = [l[6:14] for l in out.splitlines() if "Motion detected - starting event" in l]
print("  events:", len(ev), " ".join(ev))
