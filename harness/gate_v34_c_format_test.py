#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for contour 2.13: C format normalization + C best-of-2.
Normalization must keep the scorer's got-set identical and only restore
format; gate must be off at 0.0.2.12 and on at 0.0.2.13 (subprocess,
since features are fixed at import)."""
import json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ok = 0
def ck(name, cond):
    global ok
    print("ok " + name if cond else "FAIL " + name)
    assert cond
    ok += 1

SNIP = """
import gate_run as GR, parb_check as CK, json, sys
t = {"cat": "C", "n_cand": 12, "ref": {"letters": ["A", "C", "F"]}}
messy = "A=ПОДХОД B=НЕ ПОДХОД C=ПОДХОД D=НЕ ПОДХОД E=НЕ ПОДХОД F=ПОДХОД\\nФИНАЛ: A, C, F"
c0, f0, n0 = CK.check_C(t, messy)
norm = GR.c_format_normalize(t, messy)
c1, f1, n1 = CK.check_C(t, norm)
print(json.dumps({"c0": c0, "f0": f0, "c1": c1, "f1": f1, "norm": norm,
                  "noop": GR.c_format_normalize(t, "нет букв вообще")}))
"""
out = subprocess.run([sys.executable, "-c", SNIP], cwd=HERE, capture_output=True, text=True)
assert out.returncode == 0, out.stderr
d = json.loads(out.stdout)
ck("messy answer loses format at check", d["f0"] == 0)
ck("normalize keeps content identical", d["c1"] == d["c0"] == 1.0)
ck("normalize restores format", d["f1"] == 1)
ck("normalized is canonical letters", d["norm"] == "A,C,F")
ck("no letters -> no rewrite", d["noop"] == "нет букв вообще")

def feats(stamp):
    env = dict(os.environ, PARB_GATE_VERSION=stamp)
    o = subprocess.run([sys.executable, "-c",
        "import gate_run as GR; print(bool(GR.C_FORMAT_NORM), bool(GR.C_BEST2))"],
        cwd=HERE, env=env, capture_output=True, text=True)
    return o.stdout.strip()

ck("feature gate off at 0.0.2.12", feats("0.0.2.12") == "False False")
ck("feature gate on at 0.0.2.13", feats("0.0.2.13") == "True True")

import gate_versioning as GV
ck("2.13 registered as contour feature", (2, 13) in GV.CONTOUR_FEATURES)
ck("2.13 outside reserved tooling band", (2, 13) not in GV.RESERVED_TOOLING_REVISIONS)
print("GATE v34 C-FORMAT tests: PASS %d/%d" % (ok, ok))
