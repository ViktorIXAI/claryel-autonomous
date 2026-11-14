#!/usr/bin/env python3
"""Contract test for the bank gate census (scripts/bank_gate_census_v6.py).

Pins STRUCTURAL invariants only - which bank version is `working` is never pinned to a
name (the gate_v63 lesson: exact enumerations go stale the day the chain grows):
  * registry file set == published bank files on disk;
  * every bank file byte-matches its registry published_sha16 (immutable published banks);
  * exactly one entry is `working`, statuses stay in the allowed set;
  * the working bank passes gold self-test and leakage scan at current bytes;
  * the committed BANK-GATE-CENSUS.md table and scanner stamp match a fresh recompute
    (--check semantics: a retyped scoreboard row or an edited scanner goes red);
  * the sandbox-skip contract: a run whose sandbox probe failed must not compare the
    E column, must follow its own recorded probe instead of asking the environment
    twice, and must STILL compare it (and go red on drift) when the battery ran.
"""
import contextlib
import copy
import importlib.util
import io
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

spec = importlib.util.spec_from_file_location(
    "bank_gate_census_v6", os.path.join(ROOT, "scripts", "bank_gate_census_v6.py"))
cen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cen)

fails = []
checks_run = 0


def check(cond, msg):
    global checks_run
    checks_run += 1
    if not cond:
        fails.append(msg)


def quiet(fn, *a, **k):
    """Run a census call whose own drift report is EXPECTED (negative controls): the
    test asserts the exit code, the scanner's want/have lines are noise here."""
    with contextlib.redirect_stdout(io.StringIO()):
        return fn(*a, **k)


rows, meta, errors = cen.collect()
check(not errors, "census collect() errors: %s" % errors)
check(len(rows) >= 1, "census produced no rows")

# registry covers exactly the bank files on disk
import glob
disk = {os.path.relpath(p, ROOT).replace(os.sep, "/")
        for p in glob.glob(os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6*.json"))}
check({r["file"] for r in rows} == disk,
      "registry file set != published bank files on disk")

# bytes vs registry (published banks are immutable)
for r in rows:
    check(r["bytes_ok"], "byte drift vs registry for %s" % r["version"])

# exactly one working, allowed statuses
working = [r for r in rows if r["status"] == "working"]
check(len(working) == 1, "exactly one working bank required, found %d" % len(working))
check(all(r["status"] in cen.ALLOWED_STATUS for r in rows), "illegal status present")

# the working bank is gated at current bytes, not asserted in prose
# (E battery columns are sandbox-host-only; gold_ok already folds that in)
for w in working:
    check(w["gold_ok"], "working bank %s gold selftest: %s / E: %s"
          % (w["version"], w["gold"], w["gold_e"]))
    check(w["leak_ok"], "working bank %s leakage scan: %s" % (w["version"], w["leak"]))

# committed md must match a fresh recompute
check(cen.check_md(rows, meta) == 0, "committed BANK-GATE-CENSUS.md does not match recompute")

# ---- the sandbox-skip contract (measured 14.11: a CI job went red on correct bytes) ----
# This host re-executed the E battery, so `rows` carry a measured E verdict and the
# committed table does too. Simulate the CI condition that broke head 8d3426e: the
# recomputing run could NOT run the battery, so its rows carry the sentinel.
rows_nosb = copy.deepcopy(rows)
for r in rows_nosb:
    r["gold_e"] = "NOT RUN (no sandbox)"
meta_nosb = dict(meta, sandbox_ok=False)
check(cen.check_md(rows_nosb, meta_nosb) == 0,
      "a run whose sandbox probe failed must NOT compare the E column against measured bytes")

# the run's recorded probe is the authority: a second, contradicting probe of the
# environment must not re-enable the comparison (that disagreement was the bug)
_probe = getattr(cen.c6, "_docker_available", None)
try:
    cen.c6._docker_available = lambda: True
    check(cen.check_md(rows_nosb, meta_nosb) == 0,
          "check_md must follow the sandbox state recorded by this run, never probe again")
finally:
    cen.c6._docker_available = _probe

# the skip is scoped to ONE column: a tampered gold cell still goes red while skipped
rows_gold = copy.deepcopy(rows)
for r in rows_gold:
    r["gold"] = "PASS 66/67" if r["gold"].startswith("PASS") else r["gold"]
check(quiet(cen.check_md, rows_gold, meta_nosb) == 1,
      "skipping the E column must not skip the gold self-test column")

# and when the battery DID run, the E column is compared strictly
rows_e = copy.deepcopy(rows)
rows_e[0]["gold_e"] = "PASS 9/10"
check(quiet(cen.check_md, rows_e, dict(meta, sandbox_ok=True)) == 1,
      "a tampered E cell must go red when this run re-executed the battery")

# a committed table whose E column was never measured cannot pass a sandbox-capable
# check, and a stale scanner sha in its stamp goes red either way (tamper controls on
# a scratch copy, so the published md is never touched)
with tempfile.TemporaryDirectory() as td:
    md = os.path.join(td, "BANK-GATE-CENSUS.md")
    real_md = cen.MD_PATH
    cen.MD_PATH = md
    try:
        with open(md, "w", encoding="utf-8") as f:
            f.write(cen.render(rows_nosb, meta_nosb))
        check(quiet(cen.check_md, rows, dict(meta, sandbox_ok=True)) == 1,
              "a committed E column that was never re-executed must not pass a "
              "sandbox-capable check")
        txt = open(md, encoding="utf-8").read().replace(meta["census_sha16"], "0" * 16)
        with open(md, "w", encoding="utf-8") as f:
            f.write(txt)
        check(quiet(cen.check_md, rows, dict(meta, sandbox_ok=True)) == 1,
              "a stale scanner sha16 in the committed stamp must go red")
    finally:
        cen.MD_PATH = real_md

# the stamp now names the sandbox state of the run that wrote the table, so a reader
# can tell a measured E column from a never-re-executed one without running anything
check("sandbox during this run:" in open(cen.MD_PATH, encoding="utf-8").read(),
      "committed census stamp must record this run's sandbox state")

print("BANK GATE CENSUS TEST: %d checks, %d banks, statuses=%s, working gold=%s E=%s leak=%s"
      % (checks_run, len(rows), sorted({r["status"] for r in rows}),
         working[0]["gold"] if working else "-",
         working[0]["gold_e"] if working else "-", working[0]["leak"] if working else "-"))
if fails:
    for f in fails:
        print("FAIL:", f)
    sys.exit(1)
print("BANK GATE CENSUS TEST: PASS")
