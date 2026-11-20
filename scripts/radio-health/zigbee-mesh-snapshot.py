"""Zigbee mesh snapshot: who routes, who is an end device, and what the coordinator sees.

Column names verified against zigbee.db in this container (node_descriptors_v16.logical_type,
neighbors_v16.device_ieee/nwk/depth/lqi/rx_on_when_idle). IEEE values are truncated - full IEEE ids
match the MAC pattern and never leave the host.
"""
import datetime
import sqlite3

con = sqlite3.connect("file:/config/zigbee.db?mode=ro", uri=True)
cur = con.cursor()

print("--- logical_type per device (2=EndDevice, 245=Router)")
q = """select d.ieee, d.nwk, d.status, d.last_seen, n.logical_type
       from devices_v16 d left join node_descriptors_v16 n on n.ieee = d.ieee
       order by n.logical_type, d.last_seen"""
for ieee, nwk, status, seen, lt in cur.execute(q):
    when = "-"
    if seen:
        try:
            when = datetime.datetime.utcfromtimestamp(float(seen)).strftime("%m-%d %H:%M")
        except (TypeError, ValueError):
            when = str(seen)[:19]
    print(f"   ieee {str(ieee)[:6]}… nwk {nwk} type={lt} status={status} last_seen={when}")

print("\nrelays_v16 rows:", cur.execute("select count(*) from relays_v16").fetchone()[0])
print("routes_v16 rows:", cur.execute("select count(*) from routes_v16").fetchone()[0])

print("\n--- neighbours as seen by the coordinator")
tot = 0
for r in cur.execute("select device_type, rx_on_when_idle, depth, lqi from neighbors_v16"):
    tot += 1
print("   rows:", tot,
      "| types:", sorted({r[0] for r in cur.execute("select device_type from neighbors_v16")}),
      "| rx_idle:", sorted({r[1] for r in cur.execute("select rx_on_when_idle from neighbors_v16")}),
      "| depths:", sorted({r[2] for r in cur.execute("select depth from neighbors_v16")}),
      "| lqi min/max:", cur.execute("select min(lqi), max(lqi) from neighbors_v16").fetchone())
con.close()
