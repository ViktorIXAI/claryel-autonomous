#!/usr/bin/env python3
"""Contract test for `scripts/push_ready.sh`, the standing pre-push gate (added 2026-11-16, PUB tick 198).

Why this test exists. Two defects were measured in that one script on 2026-11-16, in the same
"the checker cannot lie about its own run" family this repo keeps hitting:

  1. FAIL-OPEN STATUS. The manifest step was
         python3 scripts/regen_manifest_v6.py >/dev/null 2>&1 \\
           && python3 harness/verify_manifest.py --v6 | tail -1 || { echo "regen/verify failed"; rc=1; }
     The exit status of `cmd | tail -1` is TAIL's, so a `verify_manifest.py --v6` that FAILS on pin
     drift printed its own "VERIFY FAIL" line and the script still ended `gate rc=0`. The links step
     was status-blind too: a failing `check_links.py` only printed a retry hint and never moved rc,
     although CI gates on that same script's exit code. Fixture A below reproduces the old shape and
     asserts it really was fail-open (rc 0), so checks C/E below are demonstrably not vacuous;
     fixture B pins the fixed shape at rc 1. Same class as the PUB tick-173
     `echo "$(basename $f) rc=$?"` trap, one level up: in the gate that decides whether a bad commit
     ever reaches CI.
  2. A FORGOTTEN GATE. The standing script ran FIVE of the six publication gates every PUB tick
     block enumerates: `scripts/pub_three_arm_parity_check.py` — the item-P0 gate whose row
     ("49 rows / 9 sets / 0 findings") is the number the verdict line quotes — was never run by the
     script whose comment says it exists so checks "cannot be forgotten between ticks". The repo's
     own infra secret scanner (`scripts/security/secret_scan.py --strict`, the rule that red the CI
     secret-scan job twice with `absolute_local_path`) was missing from it as well. Measured the same
     morning, a hand-typed gate loop guarded by `if [ -f ... ]` skipped two gates on a typo'd file
     name and printed a green suite with four of six rows, which is why an absent named gate is now a
     MISSING row plus a non-zero rc instead of a skip.

What is pinned structurally (the script is not executed here — its manifest step regenerates a
pin file, and a test must not write tracked bytes), and what is pinned behaviorally (faithful bash
fixtures, including one that MUST fail open so the structural census is provably non-vacuous).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "push_ready.sh")

FAILED: list[str] = []
CHECKS = 0

# The six publication gates a PUB tick block enumerates in every tick, plus the repo infra scanner.
CANON_PUB_GATES = [
    "scripts/pub_arms_index.py",
    "scripts/pub_derived_percent_check.py",
    "scripts/pub_grok_cell_check.py",
    "scripts/pub_superseded_cell_check.py",
    "scripts/pub_digest_row_check.py",
    "scripts/pub_three_arm_parity_check.py",
]
INFRA_SCANNER = "scripts/security/secret_scan.py"


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def parse_gate_block(text: str) -> list[str]:
    """Entries of the PUB_GATES=( ... ) array, quotes stripped, in file order."""
    m = re.search(r"^PUB_GATES=\(\n(.*?)^\)", text, re.S | re.M)
    if not m:
        return []
    return [g.group(1) for g in re.finditer(r'"([^"]+)"', m.group(1))]


def main() -> int:
    ck(os.path.isfile(SCRIPT), "scripts/push_ready.sh must exist")
    if not os.path.isfile(SCRIPT):
        print("pub_push_ready_gates_test: %d checks, %d failed" % (CHECKS, len(FAILED)))
        for m in FAILED:
            print("  FAIL:", m)
        return 1
    text = open(SCRIPT, encoding="utf-8").read()
    lines = text.splitlines()

    # ---- A. coverage: every canonical publication gate is in the standing list -------------
    gates = parse_gate_block(text)
    ck(len(gates) >= 6, "PUB_GATES block parsed %d entries, expected the 6 publication gates" % len(gates))
    paths = [g.split()[0] for g in gates]
    for want in CANON_PUB_GATES:
        ck(want in paths, "the standing push gate does not run %s (a forgotten gate)" % want)
    ck(len(paths) == len(set(paths)), "duplicate gate entries in PUB_GATES: %s" % paths)
    ck(len(paths) == len(CANON_PUB_GATES),
       "PUB_GATES holds %d rows, the canonical publication-gate set is %d" % (len(paths), len(CANON_PUB_GATES)))
    ck(any(p.endswith("pub_arms_index.py") and "--check" in g for p, g in zip(paths, gates)),
       "the arms-index gate must run with --check (a bare run regenerates instead of verifying)")
    ck(INFRA_SCANNER in text, "the repo infra secret scanner (%s --strict) is not in the push gate" % INFRA_SCANNER)
    ck('"total_findings"' in text,
       "the infra-scanner row must read its own total_findings cell, so an unparseable report is an input gap")

    # ---- B. existence: a named gate that does not exist is an input gap, not a green row ---
    for p in paths:
        ck(os.path.isfile(os.path.join(ROOT, p)), "PUB_GATES names a file that does not exist: %s" % p)
    tracked = subprocess.run(["git", "-C", ROOT, "ls-files", "--", *paths], capture_output=True, text=True)
    if tracked.returncode == 0:
        got = set(tracked.stdout.split())
        for p in paths:
            ck(p in got, "PUB_GATES names an UNTRACKED gate: %s" % p)

    # ---- C. status census: no step may have its status consumed by a pipeline --------------
    # (the file's own header comment quotes the OLD fail-open shape to document it, so the census
    #  runs on comment-stripped lines: a documented bug must not redden the census of live code)
    code_lines = [ln for ln in lines if not ln.lstrip().startswith("#")]
    code = "\n".join(code_lines)
    bad = [ln for ln in code_lines if re.search(r"\|\s*tail\s+-1\s*\|\|", ln)]
    ck(bad == [], "status consumed by a `| tail -1 ||` pipeline (fail-open shape): %s" % bad[:2])
    ck(not re.search(r"verify_manifest\.py\s+--v6\s*\|", code),
       "verify_manifest.py --v6 must not be piped: its status would become tail's")
    # every gate/step call is followed within 4 lines by a status capture
    for needle in ("check_links.py", "docs_policy.py --push", "verify_manifest.py --v6",
                   "regen_manifest_v6.py", "secret_scan.py --dir . --strict", "python3 $g"):
        idxs = [i for i, ln in enumerate(code_lines) if needle in ln]
        ck(bool(idxs), "step call not found in the push gate: %s" % needle)
        for i in idxs:
            window = "\n".join(code_lines[i:i + 5])
            ck("$?" in window,
               "step %r at line %d has no $? capture within 4 lines" % (needle, i + 1))
    ck(len(re.findall(r"st=\$\?|secrets_st=\$\?", code)) >= 6,
       "fewer than 6 status captures in the push gate: %d" % len(re.findall(r"st=\$\?|secrets_st=\$\?", code)))
    ck("pub gate rows:" in text, "the push gate must print how many pub-gate rows it ran")
    ck("MISSING (input gap" in text, "an absent named gate must print MISSING and move rc, never skip")

    # ---- D/E. behavioural fixtures: the old shape MUST fail open, the new one must not -----
    import tempfile

    tmp = tempfile.mkdtemp(prefix="pub-push-ready-fixtures-")
    with open(os.path.join(tmp, "gate_ok.sh"), "w") as fh:
        fh.write('#!/usr/bin/env bash\necho "gate: 0 findings"\nexit 0\n')
    with open(os.path.join(tmp, "gate_findings.sh"), "w") as fh:
        fh.write('#!/usr/bin/env bash\necho "gate: 3 findings"\nexit 3\n')

    def fixture(name: str, body: str) -> tuple[int, str]:
        path = os.path.join(tmp, name)
        with open(path, "w") as fh:
            fh.write(body)
        o = subprocess.run(["bash", path], capture_output=True, text=True, cwd=tmp)
        return o.returncode, o.stdout + o.stderr

    rc_old, out_old = fixture(
        "old_shape.sh",
        'rc=0\n'
        'python3 -c "pass" >/dev/null 2>&1 && \\\n'
        '  python3 -c \'import sys;print("VERIFY FAIL: pin drift");sys.exit(1)\' | tail -1 \\\n'
        '  || { echo "regen/verify failed"; rc=1; }\n'
        'echo "gate rc=$rc"\n'
        'exit $rc\n')
    ck("VERIFY FAIL" in out_old, "fixture A did not print the failing verify's own line: %s" % out_old)
    ck(rc_old == 0 and "gate rc=0" in out_old,
       "FIXTURE NON-VACUITY BROKEN: the old `| tail -1 ||` shape was expected to end rc=0 "
       "on a failing verify, got rc=%d / %s" % (rc_old, out_old.strip()))

    rc_new, out_new = fixture(
        "new_shape.sh",
        'rc=0\n'
        'out=$(python3 -c \'import sys;print("VERIFY FAIL: pin drift");sys.exit(1)\' 2>&1); st=$?\n'
        'echo "manifest: $(printf \'%s\' "$out" | tail -1) (status $st)"\n'
        '[ $st -ne 0 ] && rc=1\n'
        'echo "gate rc=$rc"\n'
        'exit $rc\n')
    ck(rc_new == 1 and "(status 1)" in out_new,
       "the fixed capture shape must end rc=1 on the same failure: rc=%d / %s" % (rc_new, out_new.strip()))

    # the loop shape as written in the file: a gate exiting 3 is a finding, a missing gate is an input gap
    rc_loop, out_loop = fixture(
        "loop_shape.sh",
        'rc=0; n=0\n'
        'PUB_GATES=("gate_ok.sh" "gate_findings.sh" "scripts/no_such_gate.py")\n'
        'for g in "${PUB_GATES[@]}"; do\n'
        '  p=${g%% *}; n=$((n+1))\n'
        '  if [ ! -f "$p" ]; then printf \'  %-20s MISSING (input gap, never green)\\n\' "$g"; rc=1; continue; fi\n'
        '  out=$(bash "$p" 2>&1); st=$?\n'
        '  printf \'  %-20s status %d  %s\\n\' "$g" "$st" "$(printf \'%s\' "$out" | tail -1)"\n'
        '  [ $st -ne 0 ] && rc=1\n'
        'done\n'
        'echo "pub gate rows: $n"\n'
        'echo "gate rc=$rc"\n'
        'exit $rc\n')
    ck("status 3" in out_loop, "a gate reporting findings (exit 3) must print its own status: %s" % out_loop)
    ck("MISSING (input gap" in out_loop and rc_loop == 1,
       "an absent named gate must be an input gap and redden rc: rc=%d / %s" % (rc_loop, out_loop))
    ck("pub gate rows: 3" in out_loop, "the row count must include the missing gate, not just the ones that ran")

    rc_green, out_green = fixture("green_shape.sh", 'rc=0\necho "gate rc=$rc"\nexit $rc\n')
    ck(rc_green == 0, "control: an all-green suite must stay rc 0")
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)

    print("pub_push_ready_gates_test: %d checks, %d failed" % (CHECKS, len(FAILED)))
    for m in FAILED:
        print("  FAIL:", m)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
