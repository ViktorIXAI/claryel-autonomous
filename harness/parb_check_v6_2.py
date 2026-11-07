#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorer contract v6.2 — the frozen v6.1 checkers, plus identity and decomposition.

WHAT THIS MODULE IS
-------------------
`harness/parb_check_v6.py` (sha16 pinned by `gate_scorer_contract.CONTRACT_PINS`)
decides every hard-v6 number ever published. Those bytes are immutable. This
module does not re-implement a single check — a re-implementation is precisely how
"the same scorer" quietly stops meaning the same thing. It loads the pinned v6.1
module by path, fails closed if its bytes moved, and re-exports the very same
callables.

WHAT v6.2 ADDS (all additive; strict pass/fail is bit-identical)
---------------------------------------------------------------
1. `SCORER_CONTRACT` / `contract_identity()` — the number carries its scorer.
2. `typed_codes(notes)` — every failure note becomes a typed code in a published
   class (content / protocol / integrity / marker / infra), which is what lets the
   instability map and the bank-defect queue be computed instead of hand-read.
3. `axes(...)` — the two published axes (answer quality vs protocol compliance).
   A loop-D cell that answered correctly after a banned tool attempt stops hiding
   two opposite facts inside one blended number.
4. `score_row(task, answer)` — one call returning the full scored record, so any
   future arm writes the stack with its scores instead of reconstructing it later.

Proven by `harness/gate_v59_scorer_contract_v62_test.py`: v6.1 and v6.2 produce
identical (content, format_ok, notes) on published answer bytes, and the axis
decomposition reproduces the frozen loop scorer's own criterion weights.
"""
from __future__ import annotations

import importlib.util
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

import gate_scorer_contract as SC  # noqa: E402

SCORER_CONTRACT = "v6.2"
STRICT_RULE = SC.STRICT_RULE
BASE_CONTRACT = "v6.1"
BASE_MODULE = "parb_check_v6.py"


def _load_base(extra=None):
    """Load the frozen v6.1 scorer BY PATH, after verifying its pinned bytes."""
    SC.verify_contract(BASE_CONTRACT, extra)          # fail closed on any drift
    path = SC.module_path(BASE_MODULE, extra)
    spec = importlib.util.spec_from_file_location("parb_check_v6_frozen", path)
    if not (spec and spec.loader):
        raise ImportError("cannot load frozen scorer %s" % path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__ == path, "frozen scorer shadowed by %s" % mod.__file__
    return mod


V6 = _load_base()

# The frozen dispatch, re-exported unchanged. Kept in one place so an arm and an
# offline re-score cannot drift apart (the D-plain vs loop routing bug of 0.0.2.20
# was exactly two dispatch tables disagreeing).
CHECK = {"A": V6.check_json_obj, "B": V6.check_json_obj, "C": V6.check_C_v6,
         "D": V6.check_D_plain_v6, "E": V6.run_battery, "F": V6.check_F_v6,
         "G": V6.check_G_v6, "H": V6.check_H_v6, "I": V6.check_json_obj,
         "J": V6.check_J_v6, "K": V6.check_K_v6}
check = V6.check
check_D_loop_v6 = V6.check_D_loop_v6
check_C_v6 = V6.check_C_v6
check_D_plain_v6 = V6.check_D_plain_v6
check_json_obj = V6.check_json_obj
run_battery = V6.run_battery


def scorer_for(task):
    """Which frozen checker scores this task, including the loop/plain D split."""
    cat = task["cat"]
    if cat == "D" and task.get("mode") == "loop":
        return check_D_loop_v6
    return CHECK[cat]


def score_row(task, answer, notes=None, content=None, format_ok=None):
    """Score (or re-attach) one row and return the full v6.2 record.

    Pass `answer` for a fresh score. Pass `content`/`format_ok`/`notes` from a
    published ledger instead when re-labelling stored results: the contract then
    adds identity and decomposition without re-judging a byte.
    """
    loop = task.get("cat") == "D" and task.get("mode") == "loop"
    if notes is None:
        checker = scorer_for(task)
        if loop:
            rows = answer if isinstance(answer, list) else (answer or {}).get("_loop_rows", [])
            content, format_ok, notes = checker(task, rows)
        else:
            content, format_ok, notes = checker(task, answer or "")
    return {
        "task": task["id"], "rep": task.get("rep"),
        "content": content, "format_ok": bool(format_ok),
        "strict": 1 if (content is not None and float(content) == 1.0 and format_ok) else 0,
        "notes": list(notes or []),
        "codes": SC.typed_codes(notes),
        "code_classes": sorted(SC.code_classes(notes)),
        "axes": SC.axes(content, format_ok, notes, loop=loop, ref=task.get("ref") or {}),
        "scorer_contract": SCORER_CONTRACT,
        "contract_sha16": SC.contract_identity(SCORER_CONTRACT)["contract_sha16"],
        "strict_rule": STRICT_RULE,
        "seed_protocol": SC.SEED_PROTOCOL,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(SC.contract_identity(SCORER_CONTRACT), ensure_ascii=False, indent=1))
    print("frozen base:", BASE_CONTRACT, BASE_MODULE,
          SC.CONTRACT_PINS[BASE_CONTRACT][BASE_MODULE])
