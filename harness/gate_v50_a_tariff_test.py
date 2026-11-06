#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.33 contract: A threshold-table arithmetic, fail-closed and grammar-proven.

The corrected stability map (UNSTABLE-CELLS-V61.md, group 3) shows A cells failing with
fields_mismatch because VALUES are wrong, not because fields are missing: the model mis-evaluates a
tariff chain like «Тариф: 250 если вес>=10кг, иначе 120 если вес>=2кг и габарит>=100см, иначе 0».
Every number and every attribute needed by that chain sits in the task prompt, so the map and the
total are recomputed by code — the adopted 2.27 family, one step further. The reference is never
read, no model call is spent, and anything the grammar does not fully understand is refused.

Proven here on SYNTHETIC prompts with invented field names (over-fitting guard), then the bank
coverage is stated: reproduces / refuses, and a mis-computed bank task must be zero.
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load(ver):
    """Import THIS harness copy at a given stamp; a shadowed workspace copy fails the gate."""
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


g233 = load("0.0.2.33")
g232 = load("0.0.2.32")

SYN = (
    "Прайс-лист на фрахт.\n"
    "Тариф: наценка 700 если багаж >=30кг и ширина >=120см, иначе 300 если багаж >=10кг, иначе 0.\n"
    "Отгрузки:\n"
    "id=X-01 багаж=40.5кг ширина=130см\n"
    "id=X-02 багаж=12кг ширина=50см\n"
    "id=X-03 багаж=9.9кг ширина=200см\n"
    'Верни JSON: {"fees": {id: наценка}}, {"total": сумма}.'
)

# 1. wrong model values are recomputed; correct ones are left byte-identical
wrong = json.dumps({"fees": {"X-01": 300, "X-02": 0, "X-03": 0}, "total": 300})
out, ev = g233.a_arith_by_code({"id": "A-syn", "cat": "A", "prompt": SYN}, wrong)
ck(json.loads(out) == {"fees": {"X-01": 700, "X-02": 300, "X-03": 0}, "total": 1000},
   "synthetic tariff chain repaired: %s" % out)
ck(ev == ["v233_a_tariff_table"], "the repair is evented with its own stamp: %s" % ev)

good = json.dumps({"fees": {"X-01": 700, "X-02": 300, "X-03": 0}, "total": 1000})
out, ev = g233.a_arith_by_code({"id": "A-syn", "cat": "A", "prompt": SYN}, good)
ck(out is good or json.loads(out) == json.loads(good), "correct answer untouched")
ck(ev is None, "a no-op fires no event: %s" % ev)

# 2. the stamp gate: at 2.32 the branch is off, the answer stays as the model wrote it
out, ev = g232.a_arith_by_code({"id": "A-syn", "cat": "A", "prompt": SYN}, wrong)
ck(out is wrong and ev is None, "2.32 does not run the 2.33 branch")

# 3. refusals: unknown chain variable, unit clash, ambiguous attribute, extra model key,
#    chain without a tail default
BAD = {
    "unknown var": SYN.replace("багаж >=", "объём >=").replace("багаж >", "объём >"),
    "unit clash": SYN.replace("багаж >=30кг", "багаж >=30lb"),
    "ambiguous attr": SYN.replace("и ширина >=120см", "и размер >=120см")
                      .replace("ширина=130см", "размер_внешн=130см размер_внутр=110см")
                      .replace("ширина=50см", "размер_внешн=50см размер_внутр=40см")
                      .replace("ширина=200см", "размер_внешн=200см размер_внутр=150см"),
    "no tail default": SYN.replace(", иначе 0.", "."),
}
for why, prompt in BAD.items():
    out, ev = g233.a_arith_by_code({"id": "A-syn", "cat": "A", "prompt": prompt}, wrong)
    ck(out is wrong and ev is None, "%s: refuse, touch nothing (%s)" % (why, ev))

extra = json.dumps({"fees": {"X-01": 300, "X-02": 0, "X-03": 0, "X-99": 5}, "total": 300})
out, ev = g233.a_arith_by_code({"id": "A-syn", "cat": "A", "prompt": SYN}, extra)
ck(out is extra and ev is None, "map keys must equal the prompt rows; X-99 -> refuse")

# 4. category guard: B with the same prompt is not touched
out, ev = g233.a_arith_by_code({"id": "B-syn", "cat": "B", "prompt": SYN}, wrong)
ck(out is wrong and ev is None, "non-A category untouched")

# 5. bank coverage: reproduce/refuse, zero mis-computes allowed
bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))
bank_by_id = {t["id"]: t for t in bank}
cov = []
for t in bank:
    if t["cat"] != "A":
        continue
    parsed = g233._a_tariff_table(t["prompt"])
    if not parsed or not isinstance(t.get("ref"), dict):
        cov.append((t["id"], "refuses"))
        continue
    mapkey, totalkey, rows, chain, tail = parsed
    vals = {rid: g233._a_tariff_eval(chain, tail, at) for rid, at in rows.items()}
    if any(v is None for v in vals) or set(t["ref"]) != {mapkey, totalkey} \
            or set(vals) != set(t["ref"][mapkey]):
        cov.append((t["id"], "refuses"))
        continue
    ok = all(abs(float(t["ref"][mapkey][rid]) - vals[rid]) < 1e-9 for rid in vals) \
        and abs(float(t["ref"][totalkey]) - sum(vals.values())) < 1e-9
    cov.append((t["id"], "reproduces" if ok else "MIS-COMPUTES"))
ck(not [t for t, s in cov if s.startswith("MIS")], "the grammar must never mis-compute: %s" % cov)
reproduced = [t for t, s in cov if s == "reproduces"]

# 6. 0.0.2.38 re-adoption (pair-237 decision, PAIR-237-V61.md): the flag is OFF at 2.37 (the 2.37 arms
# ran without it — history unchanged) and ON at 2.38, and it must repair the EXACT bytes that pair-237's
# adopted control line lost: A-ex6-00 seeds 1-2 carry fields_mismatch:surcharges,total in
# benchmarks/hard/v6-results/pair-237/results-j29r*.jsonl, and the re-landed grammar must reproduce the
# bank reference values from those stored answers with its own event. The two passing candidate bytes
# must come back untouched, eventless.
g238 = load("0.0.2.38")
g237c = load("0.0.2.37")
ck(g238.A_TABLE_ARITH and g238.B_TABLE_AGGREGATE and not g238.G4_LOTTERY,
   "2.38 runs adopted behaviour + B table repair + A threshold arithmetic, nothing rejected")
ck(not g237c.A_TABLE_ARITH, "2.37 must still run WITHOUT the A arithmetic (history not rewritten)")
p237 = HERE.parent / "benchmarks" / "hard" / "v6-results" / "pair-237"
t_a = bank_by_id["A-ex6-00"]
lost, passed = 0, 0
for fn, want_fix in (("results-j29r1.jsonl", True), ("results-j29r2.jsonl", True),
                     ("results-j37r1.jsonl", False), ("results-j37r2.jsonl", False)):
    fp = p237 / fn
    assert fp.exists(), "pair-237 published answers missing: %s" % fp
    row = next(json.loads(l) for l in open(fp, encoding="utf-8")
               if json.loads(l).get("task") == "A-ex6-00")
    out, ev = g238.a_arith_by_code(t_a, row["answer"])
    got37, ev37 = g237c.a_arith_by_code(t_a, row["answer"])
    ck(ev37 is None and got37 is row["answer"],
       "%s: stamp 2.37 must leave these bytes byte-identical: %r" % (fn, ev37))
    if want_fix:
        got = json.loads(out)
        ref = t_a["ref"]
        mapkey = next(k for k in ref if isinstance(ref[k], dict))
        ck(ev == ["v233_a_tariff_table"], "%s: the pair-237 loss must fire the grammar: %r" % (fn, ev))
        ck(all(abs(float(got[mapkey][rid]) - float(ref[mapkey][rid])) < 1e-9 for rid in ref[mapkey])
           and abs(float(got[next(k for k in ref if k != mapkey)])
                   - float(ref[next(k for k in ref if k != mapkey)])) < 1e-9,
           "%s: replay must reproduce the bank reference: %s vs %s" % (fn, out, ref))
        lost += 1
    else:
        ck(ev is None, "%s: a passing answer must fire no event: %r" % (fn, ev))
        passed += 1
ck(lost == 2 and passed == 2, "pair-237 replay coverage must be 2 repaired + 2 untouched: %d/%d" % (lost, passed))

print("gate_v50 PASS: %d checks | A tariff-table coverage: %s | pair-237 replay: 2 repaired, 2 untouched" % (CHECKS, dict(cov)))
