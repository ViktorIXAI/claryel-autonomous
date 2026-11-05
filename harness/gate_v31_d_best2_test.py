#!/usr/bin/env python3
"""0.0.2.11 D-loop best-of-2 selection tests.

Lottery-class D notes (status_filter_violation / plans_dangerous_action) are
handled by one extra loop run plus strict-best adoption. This pins the
applicability gate and the contour plumbing; the swap itself is live-probed
(the scorer composes content = frac + 0.2*format_ok, so a pure unit test would
just restate it).
"""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "0.0.2.11"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GR = load_module("gate_run", "gate_run.py")
GV = load_module("gate_versioning", "gate_versioning.py")

fails = 0


def ok(name, cond):
    global fails
    if cond:
        print("ok", name)
    else:
        fails += 1
        print("NOT OK", name)


ok("fires on status_filter_violation",
   GR.d_best2_applies(["status_filter_violation:['Alfa']"]))
ok("fires on plans_dangerous_action", GR.d_best2_applies(["plans_dangerous_action"]))
ok("clean notes never fire", not GR.d_best2_applies([]))
ok("unrelated notes never fire",
   not GR.d_best2_applies(["too_few_safe_steps:1", "no_final_answer"]))
ok("None notes never fire", not GR.d_best2_applies(None))
ok("2.11 is a registered contour feature", (2, 11) in GV.CONTOUR_FEATURES)
ok("stamp 0.0.2.11 resolves to behavior 2.11", GV.format_behavior("0.0.2.11") == "2.11")
ok("gate on at stamp 0.0.2.11", bool(GR.D_BEST2))

print("GATE v31 D-BEST2 tests:", "PASS" if fails == 0 else "FAIL",
      "%d failures" % fails if fails else "")
sys.exit(1 if fails else 0)
