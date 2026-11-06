#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.35 contract: B markdown-table totals recomputed ONLY from the prompt's own table.

pair-234 (PAIR-234-V61.md) closed the two earlier B grammars with a hard number: zero live fires, and the
two B cells that actually lose sit outside both grammars. One of them (B-ex6-06) is a genuine content
gap the task text fully answers: the prompt ships a markdown table, the JSON field spec states the
field as a formula over that table's own column names with an exclusion the table's own footnote declares
(`"available_total": (остаток без transite минус резерв)` + `[1] включает 8 в_transit`), and the model
returns one row's subtotal. Like every grounded repair this must fail closed: an unnamed column, a column
matching two terms, an unaccounted footnote, a non-numeric cell or a ragged table means refuse and touch
nothing, and the model's key set is never changed. The reference is never read.

Checks:
1. flag matrix: B_TABLE_AGGREGATE at 2.35 only; the unadopted 2.30-2.34 features stay off at 2.35
2. synthetic grammar with INVENTED column/field names reproduces the total (grammar is not bank-specific)
3. refusal classes: unnamed column, ambiguous column, footnote on the wrong column, footnote with two
   numbers, unaccounted footnote, no footnote when the spec asks for one, non-numeric cell, ragged table,
   missing field (no key invented), prose answer, no table in the prompt
4. no-op safety: an already-correct total returns byte-identical text with no event; other keys untouched
5. bank coverage: B-ex6-06 repairs into an answer the frozen v6 scorer accepts, every other bank B task
   is scanned and left byte-identical
6. call-site wiring: a scripted wrong answer through run_one must come out repaired, with the
   contour:v235_* event on the ledger row
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# run_one must never touch a real workspace state file: pin all artifact env paths to a temp dir
# before the module is imported (PARB_* resolve at import time).
import tempfile
_TMP = tempfile.mkdtemp(prefix="gate-v52-")
os.environ["PARB_ROOT"] = _TMP
os.environ["PARB_STATE"] = os.path.join(_TMP, "state.json")
os.environ["PARB_RESULTS"] = os.path.join(_TMP, "results.jsonl")
os.environ["PARB_LEDGER"] = os.path.join(_TMP, "ledger.jsonl")

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp (a shadowed copy measures dead code)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_feature_adoption", "gate_engine_guard"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


# --- 1. flag matrix -------------------------------------------------------------------------------
g233 = load("0.0.2.33")
ck(not g233.B_FIELD_COMPLETE and not g233.B_TABLE_AGGREGATE, "2.33 has neither B feature")
g234 = load("0.0.2.34")
ck(g234.B_FIELD_COMPLETE and not g234.B_TABLE_AGGREGATE, "2.34 keeps its own B field completeness only")
g235 = load("0.0.2.35")
ck(g235.B_TABLE_AGGREGATE and not g235.B_FIELD_COMPLETE,
   "2.35 adds the table aggregation and does NOT inherit the unadopted 2.34 grammar")
ck(not g235.CONTRACT_GUARANTEE and not g235.SELFCONSIST and not g235.J_RERANK and not g235.A_TABLE_ARITH,
   "2.35 inherits no rejected or unadopted behaviour")
ck(g235.A_ARITH_CODE and g235.COVERAGE_FROM_PROMPT and g235.FORMAT_REPAIR and g235.D_PLAIN_SCORE,
   "2.35 keeps the ADOPTED contour (2.21/2.17/2.27/2.29) — only rejected/unadopted features are frozen out")
ck(g235.contour_at_least(2, 29) and not g235.contour_at_least(2, 36), "stamp parsing still exact at 2.35")

SYN = {"id": "B-syn-t1", "cat": "B", "prompt": (
    "| Depot | Crates | Held |\n"
    "| D1 | 40[1] | 9 |\n"
    "| D2 | 15 | 4 |\n"
    "[1] включает 6 en_route.\n"
    'JSON: {"crates_total": (Crates без en_route минус Held), "d2_ok"}. Только JSON.')}

# --- 2. synthetic grammar with invented names ------------------------------------------------------
new, ev = g235.b_table_aggregate(SYN, '{"crates_total": 25, "d2_ok": 11}')
ck(ev == ["v235_b_table_total:crates_total"], "synthetic table total must fire: %r" % (ev,))
out = json.loads(new)
ck(out["crates_total"] == 36, "total = (40-6-9)+(15-4) = 36, got %r" % out["crates_total"])
ck(out["d2_ok"] == 11 and set(out) == {"crates_total", "d2_ok"},
   "the repair is a value change only, never a key-set change: %r" % out)

# --- 3. refusal classes ----------------------------------------------------------------------------
NEG = {
    "unnamed column": (
        "| Depot | Crates | Held |\n| D1 | 40 | 9 |\n"
        'JSON: {"crates_total": (Boxes без en_route минус Held)}. Только JSON.'),
    "ambiguous column": (
        "| Depot | Crates | CratesOld |\n| D1 | 40 | 9 |\n"
        'JSON: {"crates_total": (Crates минус Held)}. Только JSON.'),
    "footnote on the wrong column": (
        "| Depot | Crates | Held |\n| D1 | 40 | 9[1] |\n| D2 | 15 | 4 |\n"
        "[1] включает 6 en_route.\n"
        'JSON: {"crates_total": (Crates без en_route минус Held)}. Только JSON.'),
    "footnote with two numbers": (
        "| Depot | Crates | Held |\n| D1 | 40[1] | 9 |\n| D2 | 15 | 4 |\n"
        "[1] включает 6 en_route и 3 broken.\n"
        'JSON: {"crates_total": (Crates без en_route минус Held)}. Только JSON.'),
    "footnote not accounted for by the spec": (
        "| Depot | Crates | Held |\n| D1 | 40[1] | 9 |\n| D2 | 15 | 4 |\n"
        "[1] включает 6 en_route.\n"
        'JSON: {"crates_total": (Crates минус Held)}. Только JSON.'),
    "exclusion asked for, no footnote in the table": (
        "| Depot | Crates | Held |\n| D1 | 40 | 9 |\n| D2 | 15 | 4 |\n"
        'JSON: {"crates_total": (Crates без en_route минус Held)}. Только JSON.'),
    "non-numeric cell": (
        "| Depot | Crates | Held |\n| D1 | many | 9 |\n| D2 | 15 | 4 |\n"
        'JSON: {"crates_total": (Crates минус Held)}. Только JSON.'),
    "ragged table": (
        "| Depot | Crates | Held |\n| D1 | 40 | 9 | x |\n| D2 | 15 | 4 |\n"
        'JSON: {"crates_total": (Crates минус Held)}. Только JSON.'),
    "no table at all": (
        'Depot D1 держит 40 ящиков, 9 занято. JSON: {"crates_total": (Crates минус Held)}. Только JSON.'),
}
ANS = '{"crates_total": 25, "d2_ok": 11}'
for label, prompt in NEG.items():
    got, ev = g235.b_table_aggregate({"id": "B-syn-neg", "cat": "B", "prompt": prompt}, ANS)
    ck(got == ANS and ev is None, "refusal class '%s' must touch nothing: %r" % (label, ev))

MISSING_FIELD = {"id": "B-syn-nf", "cat": "B", "prompt": SYN["prompt"]}
got, ev = g235.b_table_aggregate(MISSING_FIELD, '{"d2_ok": 11}')
ck(got == '{"d2_ok": 11}' and ev is None, "a field the model never listed must NOT be invented")
got, ev = g235.b_table_aggregate(MISSING_FIELD, "Всего 36 ящиков.")
ck(ev is None, "a prose answer is not a table total to repair")
got, ev = g235.b_table_aggregate(MISSING_FIELD, '{"crates_total": "тридцать шесть", "d2_ok": 11}')
ck(ev is None, "a non-numeric model value is not repaired by arithmetic")

# --- 4. no-op safety -------------------------------------------------------------------------------
ok_answer = '{"crates_total": 36, "d2_ok": 11}'
got, ev = g235.b_table_aggregate(MISSING_FIELD, ok_answer)
ck(got == ok_answer and ev is None, "an already-correct total returns byte-identical text with no event")

# --- 5. bank coverage ------------------------------------------------------------------------------
import parb_check_v6 as V6
bank = {t["id"]: t for t in json.load(
    open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))}

t6 = bank["B-ex6-06"]
new, ev = g235.b_table_aggregate(t6, '{"available_total": 30, "w2_available": 30}')
ck(ev == ["v235_b_table_total:available_total"], "bank B-ex6-06 subtotal answer must repair: %r" % (ev,))
scored = json.loads(new)
ck(scored["available_total"] == 60 and scored["w2_available"] == 30,
   "repaired B-ex6-06 total must be 60: %r" % scored)
c, f = V6.check(t6, new)[:2]
ck(c == 1.0 and bool(f), "repaired B-ex6-06 must pass the frozen scorer: %r" % new)

fired, kept = [], []
for tid in sorted(k for k in bank if bank[k]["cat"] == "B" and k != "B-ex6-06"):
    got, ev = g235.b_table_aggregate(bank[tid], json.dumps(bank[tid]["ref"], ensure_ascii=False))
    (fired if ev else kept).append(tid)
    ck(got == json.dumps(bank[tid]["ref"], ensure_ascii=False),
       "%s must be byte-identical under the table grammar" % tid)
ck(not fired, "the table grammar must fire on no other bank B task: %s" % fired)
ck(len(kept) == len([k for k in bank if bank[k]["cat"] == "B"]) - 1,
   "every non-target B task must be scanned, not silently skipped: %s" % kept)

cov = {"fires": ["B-ex6-06"], "refuses_or_noops": kept}
ck(len(kept) == 6, "honest bank coverage (1 of 7 B prompts): %s" % cov)

# --- 6. call-site wiring through run_one ------------------------------------------------------------
# A green unit test plus zero live ledger events once hid a broken pipeline path (the 2.32-era pitfall),
# so the call site itself is pinned here: with the model forced to answer wrong, run_one must come out
# repaired and the event must reach the ledger row. gate_run scores through `parb_check as CK`; the
# harness copy is the LEGACY v5 module, so the test mirrors the generated workspace's v6 adapter.
class _V6Adapter:
    check = V6.check
    CHECK = {"A": V6.check_json_obj, "B": V6.check_json_obj, "C": V6.check_C_v6,
             "D": V6.check_D_plain_v6, "E": V6.run_battery, "F": V6.check_F_v6,
             "G": V6.check_G_v6, "H": V6.check_H_v6, "I": V6.check_json_obj,
             "J": V6.check_J_v6, "K": V6.check_K_v6}


rows = []
_orig_acct = g235.Acct


class CapAcct(_orig_acct):
    def row(self, task, rep):
        r = _orig_acct.row(self, task, rep)
        rows.append(r)
        return r


def _bad_model(acct, t, seed, msgs):
    return {"text": '{"available_total": 30, "w2_available": 30}', "ptok": 60, "ctok": 25,
            "ttft": 0.1, "finish": "stop", "err": None, "el": 0.5}


_orig_fg = g235.format_gate
_orig_ck = g235.CK
_orig_res = g235.gate_res
# `run_one` starts with a host/engine gate (`gate_res` curls /health); a CI runner has no inference
# endpoint and would pause 90 s then exit 3. That gate is not what this test measures, so it is pinned
# open for the duration and restored in `finally`.
g235.gate_res = lambda: None
g235.Acct = CapAcct
g235.CK = _V6Adapter
g235.format_gate = _bad_model
try:
    rec = g235.run_one(bank["B-ex6-06"], {"rep": 9201, "series": "wiring", "rep_group": "wiring",
                                          "gseed": 11, "stage": 9}, set(), {})
finally:
    g235.format_gate = _orig_fg
    g235.CK = _orig_ck
    g235.Acct = _orig_acct
    g235.gate_res = _orig_res
ck(rec and rec.get("content") == 1.0 and bool(rec.get("format_ok")),
   "run_one with a scripted wrong B total must end up scored-pass after the 2.35 repair: %r"
   % (rec or {}).get("notes"))
ck(rows and any("contour:v235_b_table_total" in e for r in rows
                for e in (r.get("events") or [])),
   "the v235 event must reach the ledger row through the pipeline, not only the unit function")

# and the stamp gate itself: the same scripted answer at 2.34 must NOT be repaired
g234b = load("0.0.2.34")
got, ev = g234b.b_table_aggregate(bank["B-ex6-06"], '{"available_total": 30, "w2_available": 30}')
ck(ev is None and got == '{"available_total": 30, "w2_available": 30}',
   "0.0.2.34 must not run the 2.35 table repair")

# 0.0.2.37 re-lands the repair (PAIR-236 decision): the gate must be ON at 2.37 and produce the exact
# same evented transformation as at 2.35, and the 2.36 lottery must stay frozen OUT at 2.37.
g237 = load("0.0.2.37")
ck(g237.B_TABLE_AGGREGATE and not g237.G4_LOTTERY and not g237.B_FIELD_COMPLETE,
   "2.37 re-adopts the table repair only; the measured-negative 2.36 lottery stays frozen to 2.36")
new37, ev37 = g237.b_table_aggregate(SYN, '{"crates_total": 25, "d2_ok": 11}')
ck(ev37 == ["v235_b_table_total:crates_total"] and json.loads(new37)["crates_total"] == 36,
   "the re-landed grammar must repair the synthetic total identically at 2.37: %r %r" % (new37, ev37))
got37, ev37 = g237.b_table_aggregate(bank["B-ex6-06"], '{"available_total": 30, "w2_available": 30}')
ck(ev37 and "v235_b_table_total" in "".join(ev37),
   "the bank target cell must be repaired at 2.37 with its mechanism event: %r" % (ev37,))

print("gate_v52_b_table_test: ALL PASS (%d checks) | B table coverage %d/%d B tasks (fires on B-ex6-06 only)"
      % (CHECKS, 1, len([k for k in bank if bank[k]["cat"] == "B"])))
