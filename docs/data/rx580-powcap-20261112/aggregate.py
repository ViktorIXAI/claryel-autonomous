#!/usr/bin/env python3
"""Aggregate the P3001 power-cap study: speed (from the bench report) x measured card watts
(from the 1 s hwmon sampler) per model per cap. Windows are paired start/end lines in
powcap_windows.txt; speed rows appear as pp512 then tg128 per tag in powcap_report.txt."""
import re, csv, collections, sys

D = sys.argv[1] if len(sys.argv) > 1 else "."
TARIFF = 0.25  # EUR/kWh, owner-stated

# --- speed rows
speed = collections.OrderedDict()
for line in open(f"{D}/powcap_report.txt"):
    m = re.match(r"^\s{2,}(\w+)\s+([\d.]+)\s*±", line)
    if not m:
        continue
    tag, val = m.group(1), float(m.group(2))
    speed.setdefault(tag, []).append(val)

# --- bench windows: first line of a tag = start, the later 3-field line = end
starts, ends = {}, {}
for line in open(f"{D}/powcap_windows.txt"):
    p = line.split()
    if len(p) < 2:
        continue
    tag, a = p[0], int(p[1])
    if len(p) >= 3:
        ends[tag] = max(ends.get(tag, 0), int(p[2]))
    elif tag not in starts:
        starts[tag] = a

samples = [(int(r["epoch"]), float(r["power_W"]), float(r["gpu_clk"]))
           for r in csv.DictReader(open(f"{D}/powcap_power.csv"))]

def stats(tag):
    s, e = starts.get(tag), ends.get(tag)
    if s is None or e is None or e <= s:
        return None
    win = [(w, c) for t, w, c in samples if s <= t <= e and w > 5]
    if not win:
        return None
    ws = [w for w, _ in win]
    cs = [c for _, c in win if c > 0]
    return {"avgW": sum(ws) / len(ws), "maxW": max(ws),
            "avgClk": (sum(cs) / len(cs)) if cs else 0, "n": len(ws)}

rows = []
for tag, vals in speed.items():
    if len(vals) < 2:
        print(f"  {tag:26s} INCOMPLETE (only {len(vals)} value) — arm did not finish")
        continue
    pp, tg = vals[0], vals[1]
    st = stats(tag)
    cap = int(re.search(r"cap(\d+)", tag).group(1))
    model = re.sub(r"^cap\d+_", "", tag)
    rows.append((model, cap, pp, tg, st))

print(f"{'model':10s} {'capW':>5} {'pp512':>8} {'tg128':>7} {'dTG%':>6} {'avgW':>6} {'maxW':>5} {'clk':>6} {'Wh/1k':>7} {'EUR/1M':>7}")
best = {}
for model, cap, pp, tg, st in rows:
    if model not in best and cap == 120:
        best[model] = tg
out = collections.OrderedDict()
for model, cap, pp, tg, st in rows:
    out.setdefault(model, []).append((cap, pp, tg, st))
for model, lst in out.items():
    base = next((t for c, p, t, s in lst if c == 120), None)
    for cap, pp, tg, st in sorted(lst, key=lambda x: -x[0]):
        if st:
            wh1k = st["avgW"] / (tg * 3600) * 1000
            line = (f"{model:10s} {cap:5d} {pp:8.1f} {tg:7.2f} "
                    f"{(100*(tg/base-1)) if base else 0:6.1f} {st['avgW']:6.1f} {st['maxW']:5.0f} "
                    f"{st['avgClk']:6.0f} {wh1k:7.2f} {wh1k*TARIFF:7.3f}")
        else:
            line = f"{model:10s} {cap:5d} {pp:8.1f} {tg:7.2f} {'-':>6} {'no power samples':>28}"
        print(line)
    # cheapest row per model
    cand = [(c, (s['avgW'] / (t*3600) * 1000 * TARIFF)) for c, p, t, s in lst if s]
    if cand:
        c, e = min(cand, key=lambda x: x[1])
        print(f"  -> {model}: cheapest at cap {c} W = {e:.3f} EUR per 1M tokens")
