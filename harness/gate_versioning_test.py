#!/usr/bin/env python3
"""Version scheme contract tests."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gate_versioning as GV

fails = 0


def check(name, actual, expected):
    global fails
    if actual != expected:
        fails += 1
        print(f"FAIL {name}: {actual!r} != {expected!r}")
    else:
        print(f"ok {name}")


os.environ.pop("PARB_VERSION_PREFIX", None)
os.environ["PARB_GATE_VERSION"] = "v2.2"
check("legacy v-prefix", GV.parse_version(), (0, 0, 2, 2))
check("legacy formatted", GV.format_version(), "0.0.2.2")

os.environ["PARB_GATE_VERSION"] = "2.1"
check("legacy short", GV.parse_version(), (0, 0, 2, 1))
check("legacy short formatted", GV.format_version(), "0.0.2.1")

os.environ["PARB_GATE_VERSION"] = "1.3.2.2"
check("operator line preserved", GV.parse_version(), (1, 3, 2, 2))
check("operator line formatted", GV.format_version(), "1.3.2.2")
check("feature ignores operator line", GV.at_least(2, 2), True)

os.environ["PARB_VERSION_PREFIX"] = "0.1"
os.environ["PARB_GATE_VERSION"] = "2.2"
check("env prefix applies to legacy short", GV.parse_version(), (0, 1, 2, 2))
check("env prefix formatted", GV.format_version(), "0.1.2.2")

os.environ["PARB_VERSION_PREFIX"] = "1.0"
os.environ["PARB_GATE_VERSION"] = "1.0.2.3"
check("full wins over env prefix", GV.parse_version(), (1, 0, 2, 3))
check("summary", GV.summary(), {
    "canonical_version": "1.0.2.3",
    "release_line": "1.0",
    "contour_version": "2.3",
})

os.environ["PARB_VERSION_PREFIX"] = "0.0"
os.environ["PARB_GATE_VERSION"] = "2.2"
check("feature gate true at 2.2", GV.at_least(2, 2), True)
check("feature gate false at 2.1", GV.at_least(2, 3), False)
check("v1 feature visible in v2", GV.at_least(1, 9), True)

try:
    GV.parse_version("bad")
except ValueError:
    print("ok rejects bad version")
else:
    fails += 1
    print("FAIL bad version accepted")

print("GATE VERSIONING:", "PASS" if fails == 0 else f"FAIL {fails}")
sys.exit(1 if fails else 0)
