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
    "contour_behavior": "2.2",
    "contour_changed_at_this_release": False,
})

os.environ["PARB_VERSION_PREFIX"] = "0.0"
os.environ["PARB_GATE_VERSION"] = "2.2"
check("feature gate true at 2.2", GV.at_least(2, 2), True)
check("feature gate false at 2.1", GV.at_least(2, 3), False)
check("v1 feature visible in v2", GV.at_least(1, 9), True)

# Two axes: a measurement/reporting revision must never read as a new contour.
for legacy_stamp, legacy_behavior in (("0.0.2.3", "2.2"), ("0.0.2.4", "2.2"),
                                      ("0.0.2.5", "2.2"), ("0.0.2.6", "2.2")):
    os.environ["PARB_GATE_VERSION"] = legacy_stamp
    check(f"tooling stamp {legacy_stamp} keeps behavior",
          GV.format_behavior(), legacy_behavior)
os.environ["PARB_GATE_VERSION"] = "0.0.2.2"
check("contour stamp reports itself as behavior", GV.format_behavior(), "2.2")
os.environ["PARB_GATE_VERSION"] = "0.0.2.6"
check("default release stamp", GV.format_version(), "0.0.2.6")
check("tooling release summary flags no contour change",
      GV.summary()["contour_changed_at_this_release"], False)
os.environ["PARB_GATE_VERSION"] = "0.0.2.2"
check("contour release summary flags contour change",
      GV.summary()["contour_changed_at_this_release"], True)

# Feature table invariants: strictly increasing, never ahead of the stamp, and
# behavior tops out at the newest implemented contour change.
check("features strictly increasing",
      all(a < b for a, b in zip(GV.CONTOUR_FEATURES, GV.CONTOUR_FEATURES[1:])), True)
check("stamp not behind newest feature",
      GV.CURRENT_REVISION >= max(GV.CONTOUR_FEATURES), True)
check("behavior tops out at newest implemented contour",
      GV.behavior_tuple("0.0.9.9"), GV.CONTOUR_FEATURES[-1])

try:
    GV.parse_version("bad")
except ValueError:
    print("ok rejects bad version")
else:
    fails += 1
    print("FAIL bad version accepted")

print("GATE VERSIONING:", "PASS" if fails == 0 else f"FAIL {fails}")
sys.exit(1 if fails else 0)
