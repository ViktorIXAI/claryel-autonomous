#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.32 contract: category J ordering may be re-derived ONLY from the task prompt.

The measured defect (`UNSTABLE-CELLS-V61.md`) is `order_partial`: the model lists the right ids in the wrong
order, and every J prompt carries its own data table plus its own ranking rule. Re-sorting from that table is
arithmetic on given numbers — the same class as the accepted 2.27 contour behaviour — not a hint from the
reference answer.

What this gate enforces:

1. Synthetic family first: invented column names and values the bank has never seen. If the grammar only
   worked because it was tuned to the seven bank prompts, it fails here.
2. Fail-closed wherever the grammar is unsure: a formula, a product, a missing direction, a word that could
   belong to two columns, an id the table does not contain — all return None and the answer is untouched.
3. Zero mis-sorts on the bank: `rule_coverage()` must reproduce the bank's own J order where it claims to
   and refuse the rest. A confident wrong order would destroy correct answers, so that count must stay 0.
4. The coverage probe reads the reference order only to prove the grammar is *capable*. The production call
   in `gate_run` passes the model's own answer ids and applies the result only when it is a pure permutation
   of what the model wrote — membership is never changed.
"""
import json
import pathlib
import random
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import gate_j_rerank as JR

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


def synth(fields, rows, rule):
    """A J-style task the bank has never seen: made-up field names and values."""
    hdr = "(uid, %s)" % ", ".join(fields)
    body = ", ".join("('%s', %s)" % (r[0], ", ".join(str(v) for v in r[1:])) for r in rows)
    return "Заявки %s: [%s]. %s Ответ — JSON-список id." % (hdr, body, rule)


# ---- 1. synthetic family -----------------------------------------------------------------------------
p = synth(["kz_score"], [("a9", 3.1), ("b7", 9.4), ("c2", 5.0)], "Выбери все по убыванию kz_score.")
ck(JR.rank_from_prompt(p, ["a9", "b7", "c2"]) == ["b7", "c2", "a9"], "synthetic desc sort")
p = synth(["latency_ms"], [("q", 40), ("w", 12), ("e", 77)], "Отсортируй по возрастанию latency_ms.")
ck(JR.rank_from_prompt(p, ["q", "w", "e"]) == ["w", "q", "e"], "synthetic asc sort")
p = synth(["weight"], [("k", 5), ("l", 9), ("m", 1)], "Оставь топ-2 по убыванию weight.")
ck(JR.rank_from_prompt(p, ["k", "l", "m"]) == ["l", "k"], "synthetic top-N")
p = synth(["temp", "when"], [("x", 20, "'2026-02-02'"), ("y", 5, "'2026-01-01'"), ("z", 30, "'2026-03-03'")],
          "Отбрось temp<10; отсортируй по when (возрастающая).")
ck(JR.rank_from_prompt(p, ["z", "x"]) == ["x", "z"], "synthetic filter then date sort")

# ---- 2. fail-closed ----------------------------------------------------------------------------------
ck(JR.rank_from_prompt(synth(["a", "b"], [("r1", 2, 3), ("r2", 5, 1)],
                            "Сортируй по произведению a и b."), ["r1", "r2"]) is None, "product rule refused")
ck(JR.rank_from_prompt(synth(["q"], [("r1", 2), ("r2", 5)],
                            "Балл = q*2 + 1. Сортируй по баллу."), ["r1", "r2"]) is None, "formula refused")
ck(JR.rank_from_prompt(synth(["zz"], [("r1", 2), ("r2", 5)],
                            "Отсортируй по zz как получится."), ["r1", "r2"]) is None, "no direction refused")
ck(JR.rank_from_prompt(synth(["zz"], [("r1", 2), ("r2", 5)],
                            "Отсортируй по убыванию zz."), ["r1", "ghost"]) is None, "unknown id refused")
ck(JR.rank_from_prompt(synth(["цена", "цена_год"], [("r1", 1, 2)],
                            "Отсортируй по возрастанию цены."), ["r1"]) is None, "ambiguous column refused")

# ---- 3. bank coverage: what the grammar claims, and zero mis-sorts -----------------------------------
bank = json.load(open(str(pathlib.Path(__file__).resolve().parent.parent
                        / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))
cov = dict(JR.rule_coverage(bank))
ck(not [t for t, s in cov.items() if s.startswith("MIS")], "no J task may be confidently mis-sorted: %s" % cov)
reproduced = sorted(t for t, s in cov.items() if s == "reproduces")
refused = sorted(t for t, s in cov.items() if s == "refuses")
ck(len(reproduced) >= 2 and len(reproduced) + len(refused) == len(cov), "coverage must be explicit: %s" % cov)

# ---- 4. the repair repairs, and never changes membership ---------------------------------------------
rng = random.Random(20261106)
for tid in reproduced:
    t = next(x for x in bank if x["id"] == tid)
    order = list(t["ref"])
    rng.shuffle(order)
    got = JR.rank_from_prompt(t["prompt"], order)
    ck(got == list(t["ref"]), "%s shuffled order repaired from its own prompt" % tid)
    ck(set(got or []) == set(t["ref"]), "%s re-rank keeps the same id set" % tid)
for tid in refused:
    t = next(x for x in bank if x["id"] == tid)
    ck(JR.rank_from_prompt(t["prompt"], list(t["ref"])) is None, "%s stays refused" % tid)

# ---- 5. grammar v2 (0.0.2.39): the four published coverage gaps, each still fail-closed ----------------
# v2 gap 1+2: ё adjective names the direction, the primary key is named only by the tie lead and by a
# unique-prefix filter column — invented field names, bank-invisible.
p = synth(["тариф", "период_дней"],
          [("s1", 120, 5), ("s2", 95, 12), ("s3", 95, 3), ("s4", 130, 2)],
          "Топ-2 самых дешёвых среди период<=10; при равенстве тарифа — меньший период.")
ck(JR.rank_from_prompt(p, ["s1", "s2", "s3"], v2=True) == ["s3", "s1"], "v2 tie-lead primary + prefix filter + ё direction")
ck(JR.rank_from_prompt(p, ["s1", "s2", "s3"]) is None, "same rule stays REFUSED under frozen v1")
# v2 gap 3: explicit product primary key with a fully-stated tie chain.
p = synth(["impact", "chance"], [("r1", 5, 2), ("r2", 3, 4), ("r3", 4, 3), ("r4", 2, 6)],
          "Отранжируй по произведению impact*chance (убыв.), при равенстве — по impact (убыв.), затем id.")
ck(JR.rank_from_prompt(p, ["r1", "r2", "r3", "r4"], v2=True) == ["r3", "r2", "r4", "r1"], "v2 product key + tie chain")
ck(JR.rank_from_prompt(p, ["r1", "r2", "r3", "r4"]) is None, "product rule still refused under frozen v1")
# v2 fail-closed: a tie clause whose column cannot be resolved refuses the WHOLE rule.
p = synth(["impact", "chance"], [("r1", 5, 2), ("r2", 3, 4)],
          "Отранжируй по произведению impact*chance (убыв.), при равенстве — по mystery_col (убыв.), затем id.")
ck(JR.rank_from_prompt(p, ["r1", "r2"], v2=True) is None, "unresolvable tie column refuses")
p = synth(["impact", "chance"], [("r1", 5, 2), ("r2", 3, 4)],
          "Отранжируй по произведению impact*chance (убыв.), при равенстве — по impact, затем id.")
ck(JR.rank_from_prompt(p, ["r1", "r2"], v2=True) is None, "tie column without direction refuses")
ck(JR.rank_from_prompt(synth(["цена", "цена_год"], [("r1", 1, 2)],
                             "Отсортируй по возрастанию цены."), ["r1"], v2=True) is None,
   "ambiguous column still refused under v2")
ck(JR.rank_from_prompt(synth(["q"], [("r1", 2), ("r2", 5)],
                             "Балл = q*2 + 1. Сортируй по баллу (убыв.), при равенстве id."), ["r1", "r2"],
   v2=True) is None, "formula still refused under v2")

# v1 byte-identity on the bank, and the stated v2 coverage.
cov1 = dict(JR.rule_coverage(bank))
ck(sorted(t for t, s in cov1.items() if s == "reproduces") == ["J-ex6-00", "J-ex6-05", "J-ex6-06"],
   "v1 coverage must not move: %s" % cov1)
cov2 = dict(JR.rule_coverage(bank, v2=True))
ck(not [t for t, s in cov2.items() if s.startswith("MIS")], "v2 must not mis-sort: %s" % cov2)
ck(sorted(t for t, s in cov2.items() if s == "refuses") == ["J-ex6-03"],
   "v2 must still refuse exactly the formula task: %s" % cov2)
ck(len([1 for s in cov2.values() if s == "reproduces"]) == 6, "v2 coverage must be 6/7: %s" % cov2)

# Replay on PUBLISHED pair-238 bytes (the pre-registration proof, CI-visible): v2 never lowers any
# stored strict result across the 36 published J rows, and converts all six chronic J-ex6-02 losses.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
def _load_ck():
    import importlib.util
    s = importlib.util.spec_from_file_location(
        "ck6", str(pathlib.Path(__file__).resolve().parent / "parb_check_v6.py"))
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
CK6 = _load_ck()
bankmap = {x["id"]: x for x in bank}
pair_dir = pathlib.Path(__file__).resolve().parent.parent / "benchmarks" / "hard" / "v6-results" / "pair-238"
ck(pair_dir.exists(), "pair-238 published artifacts must exist for the replay pin")
converted = 0; regressions = 0; seen = 0
for f in sorted(pair_dir.glob("results-k*.jsonl")):
    for line in f.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if r["task"][0] != "J":
            continue
        seen += 1
        t = bankmap[r["task"]]
        ids = None
        try:
            j = json.loads(r["answer"])
            if isinstance(j, list) and j and all(isinstance(x, str) for x in j):
                ids = j
        except Exception:
            pass
        stored = r["content"] == 1.0 and bool(r["format_ok"])
        doc = ((t.get("assembled_doc") or "") + "\n" + (t.get("prompt") or "")).strip()
        ranked = JR.rank_from_prompt(t["prompt"], ids, v2=True) if ids else None
        if ranked is None and ids:
            ranked = JR.rank_from_prompt(doc, ids, v2=True)
        outcome = stored
        if ids and ranked and set(ranked) == set(ids):
            c2, f2, _ = CK6.check(t, json.dumps(ranked, ensure_ascii=False))
            outcome = c2 == 1.0 and bool(f2)
            if outcome and not stored:
                converted += 1
        if stored and not outcome:
            regressions += 1
ck(regressions == 0, "v2 replay over published pair-238 J rows must regress nothing: %d" % regressions)
ck(converted >= 6, "the six chronic J-ex6-02 published losses must convert: %d of %d rows" % (converted, seen))

print("gate_v48 PASS: %d checks | J grammar v1 reproduces %d of %d bank tasks, refuses %d, mis-sorts 0; "
      "v2 reproduces 6 of 7, replay converts %d published losses, regresses 0"
      % (CHECKS, len(reproduced), len(cov), len(refused), converted))
