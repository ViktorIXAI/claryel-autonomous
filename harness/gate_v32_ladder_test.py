#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for contour 2.12: the max_tokens ladder gains an 8192 top
rung only at stamps >= 2.12, and PARB_LADDER overrides still win.
Each check runs gate_run in a clean subprocess because LADDER is fixed at
import time."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SNIP = ("import gate_run as GR; print(GR.LADDER)")


def ladder(env_extra):
    env = dict(os.environ, PYTHONPATH=HERE, **env_extra)
    out = subprocess.run([sys.executable, "-c", SNIP], cwd=HERE, env=env,
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr[-400:]
    return eval(out.stdout.strip())


ok = 0


def ck(name, cond):
    global ok
    print("ok " + name if cond else "FAIL " + name)
    if not cond:
        sys.exit(1)
    ok += 1


base = {"PARB_GATE_VERSION": "0.0.2.11"}
ck("2.11 keeps ceiling 2048", ladder(base) == [512, 1024, 2048])
ck("2.12 adds 8192", ladder({"PARB_GATE_VERSION": "0.0.2.12"}) == [512, 1024, 2048, 8192])
ck("2.13+ keeps one 8192 rung", ladder({"PARB_GATE_VERSION": "0.0.2.13"}) == [512, 1024, 2048, 8192])
ck("explicit PARB_LADDER wins",
   ladder({"PARB_GATE_VERSION": "0.0.2.12", "PARB_LADDER": "256,512"}) == [256, 512])
ck("explicit ladder above top is not padded",
   ladder({"PARB_GATE_VERSION": "0.0.2.12", "PARB_LADDER": "512,16384"}) == [512, 16384])

import gate_versioning as GV
ck("2.12 registered as contour feature", (2, 12) in GV.CONTOUR_FEATURES)
ck("2.12 outside reserved tooling band", (2, 12) not in GV.RESERVED_TOOLING_REVISIONS)
print("GATE v32 LADDER tests: PASS %d/%d" % (ok, ok))
