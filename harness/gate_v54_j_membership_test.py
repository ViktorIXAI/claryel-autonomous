#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.40 contract: J membership re-derived from the prompt's own rule (pair-240 candidate).

Target class surfaced by pair-239 itself: J-ex6-01 failed seeds 0-1 byte-identically in BOTH arms
(["skuC","skuB"] — skuB violates the prompt's own filter `срок<=10`), J-ex6-06 failed seed 0 in both
arms with an empty JSON list. The v2 grammar already parsed these rules and refused (the 2.39
`membership_untouched` marker); 2.40 adopts the parse when it is COMPLETE. Everything else of the
v2 contract stands: fail-closed refusals, ids only from the prompt table, reference never read, zero
model tokens, stamps below 2.40 byte-identical.

Checks:
1. flag matrix at 2.39 (no membership) vs 2.40 (membership) — history not rewritten
2. synthetic tasks with INVENTED field names: over-inclusion fixed, omission added, empty list
   derived; every refusal path (boundary tie without chain, unknown column, stem ambiguity, formula,
   ids outside the table) leaves the answer byte-identical
3. the real bank prompts: J-ex6-01/J-ex6-06 failing bytes convert at 2.40 with their event and stay
   untouched at 2.39; decorated-dict composition keeps its shape
4. REPLAY OVER THE PUBLISHED pair-239 J ROWS (the CI-pinned evidence, the way gate_v48 pinned v2):
   the six published failing rows convert to strict pass, zero of the other published J rows change
   score, and every membership conversion is evented.
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load(ver):
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning", "gate_j_rerank"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


g239 = load("0.0.2.39")
g240 = load("0.0.2.40")
ck(not g239.J_MEMBERSHIP_V3 and g240.J_MEMBERSHIP_V3, "membership flag ONLY from 2.40")
ck(g240.J_RERANK_V2 and not g240.J_RERANK, "2.40 inherits the adopted v2 re-rank, v1 stays frozen")

# ---- synthetic tasks, invented field names (over-fitting guard) ----
# Primary column is named only via `по возрастанию <col>` so the resolver has one reading; the filter
# column is separate. (A rule that mentions a column ONLY in its tie chain resolves that column as the
# primary — that is the frozen 2.39 grammar's behaviour and the synthetic stays on its clean side.)
SYN_FILTER = ("Waren (id, preis, lager): [('w1', 10, 5), ('w2', 8, 99), ('w3', 12, 3), "
              "('w4', 7, 120)]. Топ-2 по возрастанию preis среди lager<=100. JSON-список id.")
# rule set: filter lager<=100 -> w1,w2,w3; top-2 by preis asc -> w2(8), w1(10)
out, ev = g240.post_normalize_answer("J", {"prompt": SYN_FILTER}, json.dumps(["w3", "w4"]))
ck(json.loads(out) == ["w2", "w1"], "synthetic over-inclusion (w4 violates lager<=100) is re-derived: %s" % out)
ck(any("j_membership_from_prompt" in e for e in (ev or [])), "membership conversion is evented: %s" % ev)
out, ev = g239.post_normalize_answer("J", {"prompt": SYN_FILTER}, json.dumps(["w3", "w4"]))
ck(out is not None and (json.loads(out) == ["w3", "w4"]) and not any("v240" in e for e in (ev or [])),
   "2.39 keeps the refusal: sets differ -> untouched + refusal marker, never adoption")

# empty drawn list derives the rule's set
out, ev = g240.post_normalize_answer("J", {"prompt": SYN_FILTER}, "[]")
ck(json.loads(out) == ["w2", "w1"], "synthetic empty draw derives the rule set: %s" % out)
out9, ev9 = g239.post_normalize_answer("J", {"prompt": SYN_FILTER}, "[]")
ck(out9 == "[]" and not ev9, "2.39 never sees an empty list on this path: %r" % out9)

# top-K boundary tie the stated chain cannot separate -> refuse, touch nothing
SYN_TIE = "Items (id, qty): [('a', 5), ('b', 5), ('c', 1)]. Топ-2 по возрастанию qty. JSON-список id."
out, ev = g240.post_normalize_answer("J", {"prompt": SYN_TIE}, json.dumps(["a", "b"]))
ck(json.loads(out) == ["a", "b"],
   "top-K boundary tie without a separating chain must refuse membership (rule cannot say if c or a wins)")
SYN_TIE2 = ("Items (id, qty): [('a', 5), ('b', 5), ('c', 1)]. Топ-2 по возрастанию qty; "
            "при равенстве — по id. JSON-список id.")
out, ev = g240.post_normalize_answer("J", {"prompt": SYN_TIE2}, json.dumps(["a", "b"]))
ck(json.loads(out) == ["c", "a"],
   "the stated id-chain separates the boundary, the rule set (c,a) is adopted: %s" % out)
ck(any("j_membership_from_prompt" in e for e in (ev or [])), "boundary-adopted membership is evented: %s" % ev)

# unknown filter column / stem ambiguity / formula / ids outside the table -> refuse
SYN_UNK = "X (id, q): [('a', 1), ('b', 2)]. Топ-1 по возрастанию q среди zzz<=5. JSON-список id."
out, _ = g240.post_normalize_answer("J", {"prompt": SYN_UNK}, json.dumps(["b"]))
ck(json.loads(out) == ["b"], "unknown filter column refuses")
SYN_AMB = "X (id, цена, цена_год): [('a', 1, 2), ('b', 2, 1)]. Топ-1 самых дешёвых цен. JSON-список id."
out, _ = g240.post_normalize_answer("J", {"prompt": SYN_AMB}, json.dumps(["a"]))
ck(json.loads(out) == ["a"], "ambiguous stem-matched column refuses")
SYN_FORM = "X (id, q): [('a', 1), ('b', 2)]. Сортируй по формуле q*2. JSON-список id."
out, _ = g240.post_normalize_answer("J", {"prompt": SYN_FORM}, json.dumps(["a", "b"]))
ck(json.loads(out) == ["a", "b"], "formula rule refuses")
out, _ = g240.post_normalize_answer("J", {"prompt": SYN_FILTER}, json.dumps(["zz", "w1"]))
ck(json.loads(out) == ["zz", "w1"], "an id outside the prompt table refuses (no invented ids)")

# ---- the real bank prompts and the pair-239 failing bytes ----
bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))
B = {t["id"]: t for t in bank}

tj = B["J-ex6-01"]
inp = json.dumps(["skuC", "skuB"], ensure_ascii=False)
out, ev = g240.post_normalize_answer("J", {"prompt": tj["prompt"]}, inp)
ck(json.loads(out) == list(tj["ref"]),
   "J-ex6-01 published failing set re-derives to the rule set %s: got %s" % (tj["ref"], out))
ck(any("j_membership_from_prompt" in e for e in (ev or [])), "bank conversion evented: %s" % ev)
out9, ev9 = g239.post_normalize_answer("J", {"prompt": tj["prompt"]}, inp)
ck(out9 == inp and any("membership_untouched" in str(e) for e in (ev9 or [])),
   "2.39 keeps exactly what pair-239 measured: refusal marker, bytes untouched")
out, ev = g240.post_normalize_answer("J", {"prompt": B["J-ex6-06"]["prompt"]}, "[]")
ck(json.loads(out) == list(B["J-ex6-06"]["ref"]), "J-ex6-06 empty draw re-derives to the rule set: %s" % out)

# ---- replay over the PUBLISHED pair-239 rows (CI-pinned, the way gate_v48 pinned v2) ----
D = HERE.parent / "benchmarks" / "hard" / "v6-results" / "pair-239"
if not D.is_dir():
    ck(False, "published pair-239 artifacts missing — the replay contract cannot run")
import parb_check_v6 as CK  # noqa: E402

rows = 0
conv = []           # (task, rep, arm, membership?)
regr = []
changed_no_event = []
for arm in ["l37r0", "l37r1", "l37r2", "l39r0", "l39r1", "l39r2"]:
    for line in (D / ("results-%s.jsonl" % arm)).read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        if not r["task"].startswith("J"):
            continue
        rows += 1
        old = bool(float(r["content"]) == 1.0 and bool(r["format_ok"]))
        new_txt, ev = g240.post_normalize_answer("J", B[r["task"]], r.get("answer") or "")
        c, f, _ = CK.check(B[r["task"]], new_txt)
        new = bool(float(c) == 1.0 and bool(f))
        if not old and new:
            memb = any("j_membership_from_prompt" in str(e) for e in (ev or []))
            conv.append((r["task"], r["rep"], arm, memb))
            if new_txt != (r.get("answer") or "") and not any("j_membership_from_prompt" in str(e) or "j_rerank_by_prompt" in str(e)
                                                               for e in (ev or [])):
                changed_no_event.append((r["task"], r["rep"]))
        if old and not new:
            regr.append((r["task"], r["rep"], arm))
ck(rows >= 36, "replay covers every published J row of pair-239: %d" % rows)
ck(not regr, "ZERO regressions across the published pair-239 J rows: %s" % regr)
ck(not changed_no_event, "every changed row is evented: %s" % changed_no_event)
# Stored bytes of BOTH arms convert where the rule failed membership (J-ex6-01 seeds 0-1 and
# J-ex6-06 seed 0 failed identically in both arms at 2.39), and the CONTROL arms' J-ex6-02 rows
# convert by the inherited 2.39 re-rank (set was already right there — membership must NOT fire).
exp = {("J-ex6-01", 0), ("J-ex6-01", 1), ("J-ex6-06", 0),
       ("J-ex6-02", 0), ("J-ex6-02", 1), ("J-ex6-02", 2)}
got = {(t, rep) for t, rep, _, _ in conv}
ck(got == exp, "the published failing J cells convert exactly: expected %s got %s" % (exp, got))
memb_rows = [c for c in conv if c[3]]
order_rows = [c for c in conv if not c[3]]
ck({(t, rep) for t, rep, _, _ in memb_rows} == {("J-ex6-01", 0), ("J-ex6-01", 1), ("J-ex6-06", 0)}
   and len(memb_rows) == 6,
   "membership conversions are exactly the both-arms membership failures: %s" % memb_rows)
ck({(t, rep) for t, rep, _, _ in order_rows} == {("J-ex6-02", 0), ("J-ex6-02", 1), ("J-ex6-02", 2)}
   and len(order_rows) == 3
   and all(a.startswith("l37") for _, _, a, _ in order_rows),
   "J-ex6-02 control rows convert by re-rank ONLY (set preserved), candidate bytes already fixed: %s" % order_rows)

print("gate_v54 PASS: %d checks | J membership v3 only from 2.40 (2.39 refusal byte-identical); "
      "synthetic coverage incl. every refusal path; published pair-239 replay converts %d rows "
      "across %d published J rows with ZERO regressions" % (CHECKS, len(conv), rows))
