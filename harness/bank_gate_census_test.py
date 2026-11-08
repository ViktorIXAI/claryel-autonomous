#!/usr/bin/env python3
"""Contract test for the bank gate census (scripts/bank_gate_census_v6.py).

Pins STRUCTURAL invariants only - which bank version is `working` is never pinned to a
name (the gate_v63 lesson: exact enumerations go stale the day the chain grows):
  * registry file set == published bank files on disk;
  * every bank file byte-matches its registry published_sha16 (immutable published banks);
  * exactly one entry is `working`, statuses stay in the allowed set;
  * the working bank passes gold self-test and leakage scan at current bytes;
  * the committed BANK-GATE-CENSUS.md table and scanner stamp match a fresh recompute
    (--check semantics: a retyped scoreboard row or an edited scanner goes red).
"""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

spec = importlib.util.spec_from_file_location(
    "bank_gate_census_v6", os.path.join(ROOT, "scripts", "bank_gate_census_v6.py"))
cen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cen)

fails = []


def check(cond, msg):
    if not cond:
        fails.append(msg)


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

print("BANK GATE CENSUS TEST: %d banks, statuses=%s, working gold=%s E=%s leak=%s"
      % (len(rows), sorted({r["status"] for r in rows}),
         working[0]["gold"] if working else "-",
         working[0]["gold_e"] if working else "-", working[0]["leak"] if working else "-"))
if fails:
    for f in fails:
        print("FAIL:", f)
    sys.exit(1)
print("BANK GATE CENSUS TEST: PASS")
