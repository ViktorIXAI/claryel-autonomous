#!/usr/bin/env python3
"""0.0.2.9 H best-of-2 selection tests.

Rule under test: an H answer that, after all normalization, still carries a
lottery-class safety note (invented_version / no_uncertainty_marker /
fake_action_claim) gets exactly ONE more sample of the same task; the second
answer replaces the first only when it scores STRICTLY better. Everything else
(Notes clean, category != H, scorer errors, equal or worse score) keeps the
first answer untouched.
"""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "0.0.2.9"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GR = load_module("gate_run", "gate_run.py")

fails = 0


def ok(name, cond):
    global fails
    if cond:
        print("ok", name)
    else:
        fails += 1
        print("NOT OK", name)


# --- gate applies only to lottery-class notes -------------------------------
ok("fired on invented_version", GR.h_best2_applies(["invented_version"]))
ok("fired on no_uncertainty_marker", GR.h_best2_applies(["no_uncertainty_marker"]))
ok("fired on fake_action_claim", GR.h_best2_applies(["fake_action_claim"]))
ok("clean notes never fire", not GR.h_best2_applies([]))
ok("unrelated notes never fire", not GR.h_best2_applies(["too_few_safe_steps"]))
ok("None notes never fire", not GR.h_best2_applies(None))

# --- selection is strict-best ----------------------------------------------
def scorer(score_map):
    def check(t, txt):
        c, f, notes = score_map[txt]
        if c == "boom":
            raise ValueError("scorer crash")
        return c, f, notes
    return check

t = {"id": "H-x-00-0"}
S = {
    "bad":  (0.33, 1, ["invented_version"]),
    "good": (1.00, 1, []),
    "bad2": (0.33, 1, ["invented_version"]),
    "badfmt": (1.00, 0, ["no_uncertainty_marker"]),
    "goodfmt": (1.00, 1, []),
    "boom": ("boom", 0, []),
}

ok("swap only when strictly better",
   GR.h_best2_pick(scorer(S), t, "bad", "good") == "good")
ok("equal score keeps first answer",
   GR.h_best2_pick(scorer(S), t, "bad", "bad2") is None)
ok("worse candidate never swaps",
   GR.h_best2_pick(scorer(S), t, "good", "bad") is None)
ok("format-only improvement still counts",
   GR.h_best2_pick(scorer(S), t, "badfmt", "goodfmt") == "goodfmt")
ok("scorer crash on first -> no swap",
   GR.h_best2_pick(scorer(S), t, "boom", "good") is None)
ok("scorer crash on second -> no swap",
   GR.h_best2_pick(scorer(S), t, "bad", "boom") is None)

# --- versioning contract ----------------------------------------------------
GV = load_module("gate_versioning", "gate_versioning.py")
ok("2.9 is a registered contour feature", (2, 9) in GV.CONTOUR_FEATURES)
ok("stamp resolves to behavior 2.9",
   GV.format_behavior("0.0.2.9") == "2.9")
ok("2.8 stays a tooling stamp at behavior 2.7",
   GV.format_behavior("0.0.2.8") == "2.7")
ok("2.9 outside reserved band", (2, 9) not in GV.RESERVED_TOOLING_REVISIONS)

print("GATE v29 H-BEST2 tests:", "PASS" if fails == 0 else "FAIL",
      "%d failures" % fails if fails else "(%d checks)" % 0)
sys.exit(1 if fails else 0)
