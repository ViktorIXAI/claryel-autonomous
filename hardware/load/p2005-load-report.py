"""Build the 2026-11-18 P2005 load report (hourly table) from sar + telemetry + session DB.

Column indices come from each sar report's own header line, so a change in sysstat's
column set cannot silently shift numbers into the wrong field.
"""
import collections
import csv
import datetime
import sqlite3

TZ = datetime.timezone(datetime.timedelta(hours=1))
D0, D1 = 1794956400, 1795042800
BASE = "/home/viktor/.hermes/cache/scratch/p2005-20261118"


def hh(text):
    try:
        return datetime.datetime.strptime(text.strip(), "%I:%M:%S %p").hour
    except ValueError:
        return None


def sar(path, col):
    """Return [(hour, value)] for the named sysstat column of one report file."""
    out, idx, nfields = [], None, None
    for line in open(path):
        p = line.split()
        if any(c in p for c in ("runq-sz", "%idle", "kbmemfree")):
            idx = p.index(col)             # header carries the same two-token time field
            nfields = len(p)
            continue
        if idx is None:                    # the -r pull had no header line
            idx, nfields = {"%memused": 5}.get(col, 0), len(p)
        if len(p) != nfields or line.startswith("Average"):
            continue
        h = hh(p[0] + " " + p[1])
        if h is None:
            continue
        try:
            v = float(p[idx])
        except ValueError:
            continue
        if col.endswith("%") and not 0.0 <= v <= 100.0:
            continue                      # a percent column can never leave 0..100
        out.append((h, v))
    return out


cpu_idle = sar(BASE + "/sar_u.txt", "%idle")
cpu_user = sar(BASE + "/sar_u.txt", "%user")
cpu_sys = sar(BASE + "/sar_u.txt", "%system")
cpu_iowait = sar(BASE + "/sar_u.txt", "%iowait")
load1 = sar(BASE + "/sar_q.txt", "ldavg-1")
runq = sar(BASE + "/sar_q.txt", "runq-sz")
memused = sar(BASE + "/sar_r.txt", "%memused")
memavail = sar(BASE + "/sar_r.txt", "kbavail")
swpin = sar(BASE + "/sar_w.txt", "pswpin/s")
swpout = sar(BASE + "/sar_w.txt", "pswpout/s")


def by_hour(series):
    d = collections.defaultdict(list)
    for h, v in series:
        d[h].append(v)
    return d


CBUSY = {h: 100 - sum(v) / len(v) for h, v in by_hour(cpu_idle).items()}
CIOW = {h: sum(v) / len(v) for h, v in by_hour(cpu_iowait).items()}
CUSER = {h: sum(v) / len(v) for h, v in by_hour(cpu_user).items()}
LOAD = {h: max(v) for h, v in by_hour(load1).items()}
RQ = {h: max(v) for h, v in by_hour(runq).items()}
MEM = {h: max(v) for h, v in by_hour(memused).items()}
AVAIL = {h: min(v) / 1048576.0 for h, v in by_hour(memavail).items()}
SWP = {h: (max(v), max(dict(by_hour(swpout)).get(h, [0]))) for h, v in by_hour(swpin).items()}

therm = list(csv.DictReader(open(BASE + "/thermal18.csv")))
power = list(csv.DictReader(open(BASE + "/power18.csv")))

db = sqlite3.connect("file:/home/viktor/.hermes/state.db?mode=ro", uri=True)
turns = [r[0] for r in db.execute(
    """select m.timestamp from messages m join sessions s on s.id=m.session_id
       where m.timestamp>=? and m.timestamp<?
         and (s.model like '%iq3_s%' or s.model like '%basalt%')""", (D0, D1))]

gpuh, pkgh, pwk = (collections.defaultdict(list) for _ in range(3))
for r in therm:
    h = datetime.datetime.fromtimestamp(int(r["ts"]), TZ).hour
    gpuh[h].append(float(r["gpu_w"]))
    if r["pkg_w"]:
        pkgh[h].append(float(r["pkg_w"]))
for r in power:
    pwk[datetime.datetime.fromtimestamp(int(r["ts"]), TZ).hour].append(float(r["draw_w"]))
turnh = collections.Counter(datetime.datetime.fromtimestamp(t, TZ).hour for t in turns)

rows = []
for h in range(24):
    g, c = gpuh.get(h) or [0], pkgh.get(h) or [0]
    rows.append((h, CUSER.get(h, 0), CBUSY.get(h, 0), CIOW.get(h, 0), LOAD.get(h, 0), RQ.get(h, 0),
                 sum(g) / len(g), max(g), sum(c) / len(c), max(c) if c else 0, MEM.get(h, 0),
                 turnh.get(h, 0)))

with open(BASE + "/hourly-2026-11-18.csv", "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["hour_cet", "cpu_user_pct", "cpu_busy_pct", "iowait_pct", "load1_max", "runq_max",
                "gpu_w_avg", "gpu_w_max", "cpu_pkg_w_avg", "cpu_pkg_w_max", "mem_used_pct",
                "brain_llm_turns", "mem_avail_gib"])
    for r in rows:
        w.writerow(["%02d:00" % r[0]] + ["%.1f" % x for x in r[1:]] + ["%.1f" % AVAIL.get(r[0], 0)])

gpu_wh = sum(min(300.0, float(r["gpu_w"])) for r in therm) * 120 / 3600.0
pkg_wh = sum(float(r["pkg_w"]) for r in therm if r["pkg_w"]) * 120 / 3600.0
n_pkg = sum(1 for r in therm if r["pkg_w"])
summary = {
    "cpu_busy_mean_pct": sum(CBUSY.values()) / max(1, len(CBUSY)),
    "cpu_busy_max_pct": max(CBUSY.values()),
    "cpu_user_mean_pct": sum(CUSER.values()) / max(1, len(CUSER)),
    "iowait_max_pct": max(CIOW.values()),
    "load1_mean": sum(LOAD.values()) / len(LOAD),
    "load1_max": max(LOAD.values()),
    "runq_max": max(RQ.values()),
    "mem_used_max_pct": max(MEM.values()),
    "gpu_w_mean": sum(float(r["gpu_w"]) for r in therm) / len(therm),
    "gpu_w_max": max(float(r["gpu_w"]) for r in therm),
    "gpu_wh": gpu_wh,
    "gpu_over60W_min": 2 * sum(1 for r in therm if float(r["gpu_w"]) > 60),
    "gpu_clkboost_min": 2 * sum(1 for r in therm if float(r["gpu_clk"]) > 1000),
    "cpu_pkg_wh": pkg_wh,
    "cpu_pkg_samples": n_pkg,
    "cpu_pkg_w_max": max(float(r["pkg_w"]) for r in therm if r["pkg_w"]),
    "probe_wall_w_max": max(float(r["draw_w"]) for r in power),
    "tctl_max_c": max(float(r["cpu_tctl"]) for r in therm),
    "gpu_max_c": max(float(r["gpu_c"]) for r in therm),
    "dimm_max_c": max(float(r["dimm_max_c"] or 0) for r in therm),
    "nvme_max_c": max(float(r["nvme_lexar_c"] or 0) for r in therm),
    "mem_avail_min_gib": min(AVAIL.values()),
    "swap_in_max_ps": max((s[0] for s in SWP.values()), default=0),
    "swap_out_max_ps": max((s[1] for s in SWP.values()), default=0),
    "power_samples_with_rapl": sum(1 for r in therm if r["pkg_w"]),
    "ac_online_in_rapl_window": sum(1 for r in therm if r["pkg_w"] and r["ac_online"] == "1"),
    "brain_llm_turns": len(turns),
    "cpu_truly_idle_min": 10 * sum(1 for _, v in cpu_idle if 100 - v < 2),
    "gpu_over150W_min": 2 * sum(1 for r in therm if float(r["gpu_w"]) >= 150),
    "gpu_mean_active_w": (sum(float(r["gpu_w"]) for r in therm if float(r["gpu_w"]) > 60)
                         / max(1, sum(1 for r in therm if float(r["gpu_w"]) > 60))),
}
with open(BASE + "/summary-2026-11-18.txt", "w") as fh:
    for k, v in summary.items():
        fh.write("%s = %.2f\n" % (k, v))

print("| hour | CPU busy % | user % | iowait % | load1 max | runq max | GPU W avg/max | CPU pkg W avg/max | RAM used % | RAM avail GiB | brain turns |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for h, cu, cb, io, ld, rq, ga, gx, pa, px, mm, tn in rows:
    print("| %02d:00 | %.0f | %.0f | %.1f | %.1f | %.0f | %.0f / %.0f | %s | %.0f | %.1f | %d |" % (
        h, cb, cu, io, ld, rq, ga, gx, ("%.0f / %.0f" % (pa, px)) if pa else "-", mm,
        AVAIL.get(h, 0), tn))
print()
for k, v in summary.items():
    print("%-20s %.2f" % (k, v))
