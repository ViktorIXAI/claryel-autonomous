#!/usr/bin/env python3
# v1.9 probe classification vs v1.7 final and v1.8 probe
import os, json, sys
from collections import defaultdict

BASE = os.path.expanduser("~/.hermes/bench/parb")
def load(p):
    d = {}
    for line in open(p, encoding="utf-8"):
        if not line.strip(): continue
        r = json.loads(line)
        k = (r["task"], r["rep"])
        if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
            d[k] = r
    return d

def by_task(rows):
    t = defaultdict(list)
    for (task, rep), r in rows.items():
        t[task].append((rep, float(r.get("content") or 0), r))
    return t

v18 = load(BASE + "/v19-final/results-v18p.jsonl")
v19 = load(BASE + "/v19-final/results-v19p.jsonl")
t18, t19 = by_task(v18), by_task(v19)

tasks = sorted(set(t18) | set(t19))
print(f"tasks={len(tasks)} v18p_recs={len(v18)} v19p_recs={len(v19)}")
print()

def mean(v): return sum(v)/len(v) if v else None

results = []
for task in tasks:
    s18 = [c for _, c, _ in t18.get(task, [])]
    s19 = [c for _, c, _ in t19.get(task, [])]
    allp = s18 + s19
    if not allp:
        continue
    m18, m19 = mean(s18), mean(s19)
    flags = []
    if all(x < 0.75 for x in allp): flags.append("CHRONIC")
    if (max(allp) - min(allp)) > 0.5: flags.append("LOTTERY")
    if m18 is not None and m19 is not None:
        if m18 < 0.6 and m19 == 1.0: flags.append("FIXED")
        if m18 >= 0.75 and m19 < 0.5: flags.append("REGRESSED")
    results.append((task, s18, s19, m18, m19, flags))
    print(f"{task:12s} v18p={s18} m18={m18 if m18 is None else round(m18,3)} | v19p={s19 if s19 else 'PENDING'} m19={m19 if m19 is None else round(m19,3)} | {'+'.join(flags) if flags else '-'}")

print()
print("=== SPECIAL CHECKS ===")
# D-ea contour events in v19 ledger
led = BASE + "/v19-final/gate-ledger-v19p.jsonl"
if os.path.exists(led):
    from collections import Counter
    evs = Counter()
    for line in open(led, encoding="utf-8"):
        if not line.strip(): continue
        e = json.loads(line)
        for ev in e.get("events", []):
            if "v19" in ev or "fix:v19" in ev: evs[ev] += 1
    print("v19 probe events:", dict(evs) or "-")

def notes_of(rows, task):
    out = []
    for rep, c, r in rows.get(task, []):
        out.append((rep, c, sorted(set(str(n) for n in (r.get("notes") or [])))))
    return out

for task in ["F-ha-01-0", "F-ha-02-0"]:
    print(f"\n{task} notes v18p:")
    for rep, c, n in notes_of(t18, task): print(f"  rep{rep} c={c} {n}")
    print(f"{task} notes v19p:")
    for rep, c, n in notes_of(t19, task): print(f"  rep{rep} c={c} {n}")

print("\n=== v1.7-final reference (B2003/Mac means for probe tasks) ===")
for box, p in [("B2003", "/v17-final/results-v17-b2003.jsonl"), ("Mac", "/v17-final/results-v17-mac.jsonl")]:
    d = load(BASE + p)
    for task in tasks:
        vals = [float(r.get("content") or 0) for (t, rep), r in d.items() if t == task]
        if vals:
            print(f"  {box} {task:12s} n={len(vals)} mean={sum(vals)/len(vals):.3f}")

print("\n=== CLASS SUMMARY ===")
summary = defaultdict(list)
for task, s18, s19, m18, m19, flags in results:
    summary[",".join(flags) if flags else "no-flag"].append(task)
for k in sorted(summary):
    print(f"{k}: {summary[k]}")
