#!/usr/bin/env python3
"""Contract for contour 0.0.2.29 bookkeeping — stamp validation (measurement validity).

A C-only paired arm was launched with PARB_GATE_VERSION=0.0.2.228 and 0.0.2.229 (the shell prefix
"0.0.2." plus 228/229). Both parsed successfully — as contour 2.228 and 2.229 — so both arms ran
EVERY shipped feature, exited 0, wrote healthy-looking ledgers, and produced a "pair" of two
identical behaviours with zero flips. The tolerant parse stays (a stamp ahead of the newest
implemented feature is a reporting release, and behavior_tuple tops out — that is a separate
contract in gate_versioning_test), but an official arm run now dies at import on an unknown stamp.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

fails = []


def check(name, cond, detail=""):
    print("%-58s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(name)


import gate_versioning as GV

check("registered stamp 0.0.2.28 accepted", GV.registered_stamp("0.0.2.28")[2:] == (2, 28))
check("registered stamp 0.0.2.29 accepted", GV.registered_stamp("0.0.2.29")[2:] == (2, 29))
check("historical shorthand v2.6 accepted", GV.registered_stamp("v2.6")[2:] == (2, 6))
check("reserved tooling band accepted", GV.registered_stamp("0.0.2.3")[2:] == (2, 3))

for bad in ("0.0.2.228", "0.0.2.229", "0.0.2.99"):
    try:
        got = GV.registered_stamp(bad)
        check("future stamp %s rejected" % bad, False, "accepted as %s" % (got,))
    except ValueError as exc:
        check("future stamp %s rejected" % bad, "unknown contour stamp" in str(exc),
              str(exc)[:56])

check("unparseable stamp 0.0.218 rejected", GV.registered_stamp.__name__ == "registered_stamp")
try:
    GV.registered_stamp("0.0.218")
    check("unparseable stamp 0.0.218 rejected", False, "accepted")
except ValueError as exc:
    check("unparseable stamp 0.0.218 rejected", "unsupported contour version" in str(exc),
          str(exc)[:56])

# tolerance kept where it is intentional: reporting releases top out at the newest behaviour
check("behavior_tuple still tolerates a far-future stamp",
      GV.behavior_tuple("0.0.9.9") == GV.CONTOUR_FEATURES[-1], str(GV.behavior_tuple("0.0.9.9")))

# integration: the runner refuses to start under an unknown stamp, before touching the serve
env = dict(os.environ, PARB_GATE_VERSION="0.0.2.228")
r = subprocess.run([sys.executable, "-c", "import gate_run"], cwd=HERE, env=env,
                   capture_output=True, text=True)
check("gate_run import dies on an unknown stamp",
      r.returncode != 0 and "unknown contour stamp" in (r.stderr or ""),
      "rc=%s %s" % (r.returncode, str((r.stderr or "").strip().splitlines()[-1:])))
env = dict(os.environ, PARB_GATE_VERSION="0.0.2.29")
r2 = subprocess.run([sys.executable, "-c", "import gate_run"], cwd=HERE, env=env,
                    capture_output=True, text=True)
check("gate_run imports fine on a registered stamp", r2.returncode == 0,
      str((r2.stderr or "").strip().splitlines()[-1:]))
print("ALL PASS" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
