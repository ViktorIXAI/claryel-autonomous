#!/usr/bin/env python3
"""0.0.2.10 E multi-failure repair feedback tests.

Rule under test: the code gate may ask the runner for up to FOUR distinct
failing tests with their source lines (detail=True) — but ONLY behind contour
2.10. The scorer (check_E, default call) must keep the old byte-compatible
single-failure error text, and scores must not move at all.
"""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "0.0.2.10"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


CK = load_module("parb_check", "parb_check.py")
GV = load_module("gate_versioning", "gate_versioning.py")

fails = 0


def ok(name, cond):
    global fails
    if cond:
        print("ok", name)
    else:
        fails += 1
        print("NOT OK", name)


CODE = "def f(x):\n    return x + 1\n"
TESTS = "\n".join([
    "assert f(1) == 2",        # pass
    "assert f(2) == 99",       # fail 1
    "assert f(3) == 98",       # fail 2
    "assert f(4) == 97",       # fail 3
    "assert f(5) == 96",       # fail 4
    "assert f(6) == 95",       # fail 5 (beyond the cap)
    "raise KeyError('boom')",  # fail 6
])

ok("2.10 is a registered contour feature", (2, 10) in GV.CONTOUR_FEATURES)
ok("stamp 0.0.2.10 resolves to behavior 2.10", GV.format_behavior("0.0.2.10") == "2.10")
ok("2.10 outside reserved band", (2, 10) not in GV.RESERVED_TOOLING_REVISIONS)

# default (scorer) path: single first failure, old text style
okc, totc, err = CK.run_py(CODE, TESTS, {})
ok("scorer counts unchanged (1/7)", (okc, totc) == (1, 7))
ok("scorer keeps old-style single error",
   err.startswith("AssertionError") and "тест" not in err and "|" not in err)

# gate (detail) path: up to 4 distinct failures with test lines
okc2, totc2, err2 = CK.run_py(CODE, TESTS, {}, fails=4, detail=True)
ok("detail counts identical", (okc2, totc2) == (1, 7))
ok("detail carries test source lines", "тест 2:" in err2 and "assert f(2) == 99" in err2)
ok("detail carries multiple failures", err2.count("тест ") >= 4)
ok("detail capped at 4 failures", err2.count("тест ") <= 4)
ok("detail caps at first four failing tests", "тест 5:" in err2 and "тест 6:" not in err2)

# check_E untouched: score + old-style note
t = {"id": "E-x-00-0", "ref": {"tests": TESTS}, "env": {}}
frac, fok, notes = CK.check_E(t, "```python\n" + CODE + "```")
ok("check_E fraction from counts", abs(frac - 1 / 7.0) < 1e-9)
ok("check_E note keeps old format", notes and notes[0].startswith("tests_failed:AssertionError"))

print("GATE v30 E-FEEDBACK tests:", "PASS" if fails == 0 else "FAIL",
      "%d failures" % fails if fails else "")
sys.exit(1 if fails else 0)
