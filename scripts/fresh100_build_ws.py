#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the FRESH100 run workspace (issue #13): bank.json with independent
oracle refs embedded, plan.json (100 x rep0), scorer shim over the frozen
parb_check. Deterministic; hashes printed."""
import json, os, re, sys, shutil, hashlib

SRC = "/tmp/fresh100.jsonl"
HARNESS = os.path.expanduser("~/projects/strata-autonomous-harness/harness")
SCRIPTS = os.path.expanduser("~/projects/strata-autonomous-harness/scripts")
WS = os.path.expanduser("~/parb-2005-fresh")
sys.path.insert(0, SCRIPTS)
import fresh100_oracles as OR

os.makedirs(WS, exist_ok=True)
rows = [json.loads(l) for l in open(SRC)]

# E battery: shared contract of the normalize_prices family (all 10 tasks)
E_TESTS = [
    "assert normalize_prices([(10,2)]) == [2000]",
    "assert normalize_prices([(12.5,2)]) == [2500]",
    "assert normalize_prices([(10000,1)]) == [1000000]",
    "assert normalize_prices([(0,5)]) == []",
    "assert normalize_prices([(-3,4)]) == []",
    "assert normalize_prices([(10,0)]) == []",
    "assert normalize_prices([(12,-2)]) == []",
    "assert normalize_prices([('7',3)]) == []",
    "assert normalize_prices([(True,3)]) == []",
    "assert normalize_prices([(1,True)]) == []",
    "assert normalize_prices([(float('nan'),2)]) == []",
    "assert normalize_prices([(float('inf'),2)]) == []",
    "assert normalize_prices([(2,2.5)]) == []",
    "assert normalize_prices([(2,'3')]) == []",
    "assert normalize_prices([(1,1),(2,2)]) == [100,400]",
    "assert normalize_prices([(100,3),(1,1)]) == [30000,100]",
    "assert normalize_prices([(0.01,1)]) == [1]",
    "assert normalize_prices([(0.014,1)]) == [1]",
    "assert normalize_prices([(0.015,1)]) == [2]",
    "assert normalize_prices([(1.005,1)]) == [101]",
    "assert normalize_prices([(2.675,2)]) == [535]",
    "assert normalize_prices([(10,2),(10,2)]) == [2000,2000]",
    "assert normalize_prices([(5000,2),(250,4)]) == [1000000,100000]",
    "assert normalize_prices([(9.99,7)]) == [6993]",
    "assert all(type(x) is int for x in normalize_prices([(1,1)]))",
]

bank, plan = [], []
invalid = []
for t in rows:
    cat = t["id"].split("-")[1]
    ref = {}
    if cat in OR.ORACLES:
        exp = OR.ORACLES[cat](t)
        if exp is None:
            invalid.append(t["id"])
            ref = {"oracle_invalid": True}
        else:
            ref = {"expected": exp}
            if cat == "D":
                data = OR.extract_json(t["prompt"], "Dependencies")
                ref["expected"]["_req"] = {s["id"]: s["requires"] for s in data["steps"]}
    elif cat == "E":
        ref = {"tests": "\n".join(E_TESTS)}   # base run_py contract: one string
    # H: rules-only scorer, no ref data needed
    bank.append({"id": t["id"], "cat": cat, "level": "fresh100",
                 "prompt": t["prompt"],
                 "seed": t.get("seed", 0), "ref": ref, "fresh100": True})
    plan.append({"task": t["id"], "rep": 0, "series": "main", "stage": 1,
                 "rep_group": "fresh",
                 "gseed": int(hashlib.sha256(("%s|0" % t["id"]).encode()).hexdigest()[:8], 16) % 999983})

json.dump(bank, open(os.path.join(WS, "bank.json"), "w"), ensure_ascii=False, indent=1)
json.dump(plan, open(os.path.join(WS, "plan.json"), "w"), indent=1)

# harness deployment (explicit, no CLI-flag illusions)
for f in ("gate_run.py", "gate_versioning.py", "gate_fixers.py", "parb_loop.py",
          "gate_engine_guard.py", "parb_bank.py", "parb_bank_hard.py"):
    shutil.copy(os.path.join(HARNESS, f), WS)
shutil.copy(os.path.join(SCRIPTS, "fresh100_check.py"), WS)
shutil.copy(os.path.join(SCRIPTS, "fresh100_oracles.py"), WS)

# parb_check SHIM: frozen base scorers stay intact for helper functions
# (run_py, strip_fence, check_E, want_format...), category CHECK and check_*
# names are replaced by the independent fresh100 oracles.
shim = '''# parb_check shim for the FRESH100 workspace (issue #13).
# Loads the frozen base parb_check (hash-pinned upstream) and rebinds the
# ten category check_* names + CHECK dict to independent fresh100 oracles.
import importlib.util as _iu, os as _os
_BASE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_parb_check_base.py")
_spec = _iu.spec_from_file_location("_parb_check_base", _BASE)
_base = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_base)
for _k in dir(_base):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_base, _k)
import fresh100_check as _F
import fresh100_oracles as _O
check_A, check_B, check_C = _F.check_A, _F.check_B, _F.check_C
check_D = _F.check_D
check_F, check_G, check_H = _F.check_F, _F.check_G, _F.check_H
check_I, check_J = _F.check_I, _F.check_J
CHECK = dict(_base.CHECK)
CHECK.update({"A": check_A, "B": check_B, "C": check_C, "D": check_D,
              "F": check_F, "G": check_G, "H": check_H, "I": check_I, "J": check_J})
'''
shutil.copy(os.path.join(HARNESS, "parb_check.py"), os.path.join(WS, "_parb_check_base.py"))
open(os.path.join(WS, "parb_check.py"), "w").write(shim)

# parb_loop shim: loop scorer for fresh D must use the fresh D core
loop_shim = '''import importlib.util as _iu, os as _os
_BASE = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "_parb_loop_base.py")
_spec = _iu.spec_from_file_location("_parb_loop_base", _BASE)
_m = _iu.module_from_spec(_spec)
_spec.loader.exec_module(_m)
for _k in dir(_m):
    if not _k.startswith("__"):
        globals()[_k] = getattr(_m, _k)
import fresh100_check as _F
check_D_loop = _F.check_D_loop
'''
shutil.copy(os.path.join(HARNESS, "parb_loop.py"), os.path.join(WS, "_parb_loop_base.py"))
open(os.path.join(WS, "parb_loop.py"), "w").write(loop_shim)

print("bank=%d plan=%d oracle_invalid=%s" % (len(bank), len(plan), invalid))
for f in ("bank.json", "plan.json"):
    h = hashlib.sha256(open(os.path.join(WS, f), "rb").read()).hexdigest()
    print("sha256(%s)=%s" % (f, h))
