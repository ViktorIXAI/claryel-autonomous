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
print("gate_v50 PASS: %d checks | A tariff-table coverage: %s" % (CHECKS, dict(cov)))
