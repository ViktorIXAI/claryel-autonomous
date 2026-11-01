# -*- coding: utf-8 -*-
"""План испытания: фиксируется до прогона (plan.json + plan_hash).
Позиция = (задача, повтор, серия). Этапы имеют временные боксы от фактического старта.
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

    # этап 1: базовая диагностика и разогрев (короткие задачи, результаты идут в свои категории)
    warm = [t["id"] for t in tasks if t["level"] == "easy" and t["cat"] in "ABCFHIJK"][:10]
    for tid in warm:
        add(tid, 0, "main", 1, "warmup")
    # этапы 2..5: чередование категорий, чтобы не мерить всё одним блоком
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
    # этап 6: повторяемость (L) — заранее зафиксированная выборка
    for lvl, nrep, ntask in LADDER:
        cand = [t["id"] for t in tasks if t["stage"] in (2, 3, 4, 5) and t["level"] == lvl and
                t["kind"] != "loop"][:ntask]
        for tid in cand:
            for rep in range(nrep):
                add(tid, 100 + rep, "main", 6, "L-" + lvl)
    # этап 6/7 стресс-задачи программирования (100 и 200 тестов), если они есть в банке
    for st in (6, 7):
        for t in tasks:
            if t["stage"] == st and t["cat"] == "E":
                for rep in range(2 if st == 6 else 1):
                    add(t["id"], rep, "main", st, "stress-E")
    # этап 7 контрольный срез: по задаче каждой категории + добор сложных
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
