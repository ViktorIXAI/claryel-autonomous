# -*- coding: utf-8 -*-
"""Test plan: frozen before the run (plan.json + plan_hash).
A position = (task, rep, series). Stages have time boxes measured from actual start.
"""
import random, hashlib

REPS = {"easy": 3, "medium": 3, "hard": 2, "veryhard": 2}
REPS_LOOP = 2
STAGE_BOX = {1: (0, 600), 2: (600, 3300), 3: (3300, 5700), 4: (5700, 8400),
             5: (8400, 11100), 6: (11100, 13800), 7: (13800, 14400)}
LADDER = [("easy", 10, 6), ("medium", 10, 6), ("hard", 20, 5)]
CONTROL = 12


def build(tasks, seed=4242):
    rng = random.Random(seed)
    byid = {t["id"]: t for t in tasks}
    plan = []

    def add(tid, rep, series, stage, group):
        plan.append({"task": tid, "rep": rep, "series": series, "stage": stage,
                     "gseed": rng.randint(10000, 999999), "rep_group": group})

    # stage 1: baseline diagnostics and warm-up (short tasks; results go to their categories)
    warm = [t["id"] for t in tasks if t["level"] == "easy" and t["cat"] in "ABCFHIJK"][:10]
    for tid in warm:
        add(tid, 0, "main", 1, "warmup")
    # stages 2..5: category interleaving so nothing is measured as one block
    for st in (2, 3, 4, 5):
        buckets = {}
        for t in tasks:
            if t["stage"] == st:
                buckets.setdefault(t["cat"], []).append(t["id"])
        seq = []
        while any(buckets.values()):
            for c in sorted(buckets):
                if buckets[c]:
                    seq.append(buckets[c].pop(0))
        for tid in seq:
            t = byid[tid]
            n = REPS_LOOP if t["kind"] == "loop" else REPS[t["level"]]
            for rep in range(n):
                for s in ["main"] + t.get("extra_series", []):
                    add(tid, rep, s, st, None)
    # stage 6: repeatability (L) — a pre-frozen sample
    for lvl, nrep, ntask in LADDER:
        cand = [t["id"] for t in tasks if t["stage"] in (2, 3, 4, 5) and t["level"] == lvl and
                t["kind"] != "loop"][:ntask]
        for tid in cand:
            for rep in range(nrep):
                add(tid, 100 + rep, "main", 6, "L-" + lvl)
    # stage 6/7 programming stress tasks (100 and 200 tests), if present in the bank
    for st in (6, 7):
        for t in tasks:
            if t["stage"] == st and t["cat"] == "E":
                for rep in range(2 if st == 6 else 1):
                    add(t["id"], rep, "main", st, "stress-E")
    # stage 7 final cut: one task per category plus extra hard ones
    ctrl = []
    for c in sorted({t["cat"] for t in tasks}):
        cand = [t["id"] for t in tasks if t["cat"] == c and t["kind"] != "loop"]
        if cand:
            ctrl.append(rng.choice(cand))
    extra = [t["id"] for t in tasks if t["level"] == "hard" and t["kind"] != "loop"]
    rng.shuffle(extra)
    for tid in (ctrl + extra)[:CONTROL]:
        add(tid, 200, "main", 7, "control-end")
    return plan


def plan_hash(plan):
    h = hashlib.sha256()
    for p in plan:
        h.update(("%s|%s|%s|%s" % (p["task"], p["rep"], p["series"], p["stage"])).encode())
    return h.hexdigest()[:16]
