"""0.0.2.14 contract: checker-keyword injection is OFF by default (issue #15).

Without STRATA_CHECKER_INJECT: POST_NORMALIZE / H_SAFETY / F_GROUND / K_NEGATION
must all be False at the current stamp. With the env flag they re-arm for
historical reproduction only.
"""
import os
import subprocess
import sys

SNIP = (
    "import os, sys; sys.path.insert(0, 'harness'); "
    "import gate_run as GR; "
    "print(int(GR.CHECKER_INJECT), int(GR.POST_NORMALIZE), int(GR.H_SAFETY), "
    "int(GR.F_GROUND), int(GR.K_NEGATION))"
)
outs = []
for env_on in (False, True):
    env = dict(os.environ)
    if env_on:
        env["STRATA_CHECKER_INJECT"] = "1"
    else:
        env.pop("STRATA_CHECKER_INJECT", None)
    r = subprocess.run([sys.executable, "-c", SNIP], capture_output=True, text=True, env=env)
    outs.append(r.stdout.strip().split())

off, on = outs
assert off == ["0", "0", "0", "0", "0"], "2.14 default must be fully injection-off: %s" % off
assert on[0] == "1" and all(v == "1" for v in on[1:]), "opt-in must re-arm: %s" % on
print("GATE v35 injection-off default tests: 2 passed, 0 failed")
