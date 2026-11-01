#!/usr/bin/env python3
# Nightly v1.9 diagnostic: probe classification + nudge economics
import json, collections, statistics, re, sys

KINDS = ["no_final_answer", "too_few_safe_steps", "conflict_not_flagged",
         "q5_contradiction_missed", "contradiction", "cause_not_named", "bad_negation_kept"]

FIN = os.environ.get("PARB_FIN", "./v18-final")

def rows(path):
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except Exception:
                pass
    return out

# ---------- 1) Probe classification ----------
probe = rows(f"{FIN}/results-v18p-0130.jsonl")
best = {}
for r in probe:
    if r.get("content") is None:
        continue
    k = (r["task"], r["rep"])
    best[k] = max(best.get(k, -1), r["content"])

tasks = collections.defaultdict(dict)
for (t, rep), c in best.items():
    tasks[t][rep] = c

# v1.7 baselines from final snapshots (both boxes, dedup best per task/rep, mean per task)
v17 = {}
for fn in ("results-v17-b2003.jsonl", "results-v17-mac.jsonl"):
    for r in rows(f"./v17-final/{fn}"):
        if r.get("content") is None:
            continue
        k = (r["task"], r.get("rep"), r.get("box", fn))
        v17[k] = max(v17.get(k, -1), r["content"])
v17_task = collections.defaultdict(list)
for (t, rep, _), c in v17.items():
    v17_task[t].append(c)
v17_mean = {t: sum(v) / len(v) for t, v in v17_task.items()}

CHRONIC, LOTTERY, FIXED, NEITHER = [], [], [], []
for t in sorted(tasks):
    scores = list(tasks[t].values())
    n = len(scores)
    mean = sum(scores) / n
    mn, mx = min(scores), max(scores)
    v17m = v17_mean.get(t)
    chronic = all(s < 0.75 for s in scores)
    lottery = (mx - mn) > 0.5
    fixed = (all(s == 1.0 for s in scores) and v17m is not None and v17m < 0.6)
    rec = dict(task=t, n=n, mean=round(mean, 3), mn=round(mn, 3), mx=round(mx, 3),
               scores=sorted(round(s, 2) for s in scores), v17=(round(v17m, 3) if v17m is not None else None))
    if chronic: CHRONIC.append(rec)
    if lottery: LOTTERY.append(rec)
    if fixed: FIXED.append(rec)
    if not (chronic or lottery or fixed): NEITHER.append(rec)

print(f"PROBE tasks={len(tasks)} records={len(best)} reps={sorted({rep for (_,rep) in best})}")
print(f"overall probe mean content = {statistics.mean(best.values()):.3f}")
for name, lst in (("CHRONIC", CHRONIC), ("LOTTERY", LOTTERY), ("FIXED", FIXED), ("OTHER", NEITHER)):
    print(f"\n== {name} ({len(lst)}) ==")
    for r in lst:
        tag = ""
        if r in CHRONIC and r in LOTTERY: tag = " [CHRONIC+LOTTERY]"
        print(f"  {r['task']:14s} probe_mean={r['mean']:.2f} scores={r['scores']} v17_mean={r['v17']}{tag}")

# ---------- 2) Nudge economics ----------
def nudge_econ(led_rows, label):
    fired = collections.Counter()
    adopted = collections.Counter()
    for r in led_rows:
        for ev in r.get("events", []):
            m = re.match(r"contour:v18_nudge_fired_(.+)$", ev)
            if m:
                s = m.group(1)
                for kind in KINDS:
                    if kind in s:
                        fired[kind] += 1
                fired["__combo:" + s] += 1
                continue
            m = re.match(r"fix:v18_nudge_(.+)$", ev)
            if m:
                s = m.group(1)
                for kind in KINDS:
                    if kind in s:
                        adopted[kind] += 1
    print(f"\n== NUDGE ECONOMY ({label}) ==")
    kinds = sorted({k for k in list(fired) + list(adopted) if not k.startswith("__combo")})
    tot_f = tot_a = 0
    for k in kinds:
        f, a = fired[k], adopted[k]
        if f == 0 and a == 0: continue
        tot_f += f; tot_a += a
        pct = (100.0 * a / f) if f else 0.0
        print(f"  {k:32s} fired={f:5d} adopted={a:4d} adopt%={pct:5.1f}")
    combos = {k.split(":", 1)[1]: v for k, v in fired.items() if k.startswith("__combo")}
    nrec = len(led_rows)
    nrec_fired = sum(1 for r in led_rows if any(e.startswith("contour:v18_nudge_fired") for e in r.get("events", [])))
    print(f"  TOTAL fired={tot_f} adopted={tot_a} adopt%={100.0*tot_a/tot_f if tot_f else 0:.1f}; records={nrec}, records_with_fire={nrec_fired} ({100.0*nrec_fired/nrec if nrec else 0:.0f}%)")
    if combos:
        print("  combo fires:", ", ".join(f"{k}={v}" for k, v in sorted(combos.items(), key=lambda x: -x[1])))

nudge_econ(rows(f"{FIN}/gate-ledger-v18m-0130.jsonl"), "Mac v1.8 main series")
nudge_econ(rows(f"{FIN}/gate-ledger-v18p-0130.jsonl"), "P2005 probe")

# ---------- 3) v18m main series quick stats ----------
main = {}
for r in rows(f"{FIN}/results-v18m-0130.jsonl"):
    if r.get("content") is None:
        continue
    k = (r["task"], r.get("rep"))
    main[k] = max(main.get(k, -1), r["content"])
print(f"\n== v18m main: records={len(main)}, mean={statistics.mean(main.values()):.3f}, perfect%={100.0*sum(1 for v in main.values() if v==1)/len(main):.1f}")
cat = collections.defaultdict(list)
for (t, rep), c in main.items():
    cat[t.split("-")[0]].append(c)
for k in sorted(cat):
    v = cat[k]
    print(f"  cat {k}: n={len(v)} mean={sum(v)/len(v):.3f} perfect%={100.0*sum(1 for x in v if x==1)/len(v):.0f}")
