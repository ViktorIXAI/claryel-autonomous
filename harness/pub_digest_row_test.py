#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the PUB digest writer (`scripts/pub_bench_score.write_digest`).

Why this exists. The writer rebuilt its table with a substring filter,
`"bench |" not in line`, to skip the header row. That filter also matched any DATA row whose bench
name contains `bench |` — which is every `livecodebench` row — so a second digest write silently
DELETED the LiveCodeBench percent published by the first write. Measured 2026-11-09: the LCB
re-score (a call-label correction, verdicts byte-identical) rewrote PUB-DIGEST.md without the
first LCB row. Nothing was scored differently; a published row was eaten, and the next digest
write would have eaten the LCB contour row the same way.

Pinned here:
  1. a `livecodebench` row survives every later write, whatever the bench name contains;
  2. the header/separator appear exactly once per write;
  3. row count never shrinks across writes (fail closed rather than silently dropping);
  4. control: the old substring filter demonstrably loses the row, so this test is not vacuous.
"""
import importlib.util
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "scripts"))

fails = []
checks = [0]


def chk(cond, name):
    checks[0] += 1
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fails.append(name)


spec = importlib.util.spec_from_file_location(
    "pbs", os.path.join(REPO, "scripts", "pub_bench_score.py"))
pbs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pbs)

with tempfile.TemporaryDirectory() as td:
    dst = os.path.join(td, "D.md")
    r_lcb = pbs.digest_row("livecodebench", "m-local", 112, "a" * 16,
                           "temp 0.7, max_tokens 2400; checker lcb-exec-v1", 60, 112)
    r_bfcl = pbs.digest_row("bfcl", "m-local", 1240, "b" * 16, "checker bfcl-ast-v1", 1116, 1240)
    r_lcb2 = pbs.digest_row("livecodebench", "m-local+contour", 112, "a" * 16,
                            "matched shape, checker lcb-exec-v1", 61, 112)
    pbs.write_digest(r_lcb, dst)
    pbs.write_digest(r_bfcl, dst)
    pbs.write_digest(r_lcb2, dst)
    text = open(dst, encoding="utf-8").read()
    lines = [l for l in text.splitlines() if l.startswith("| ")]
    rows = [l for l in lines if not l.startswith("| bench |")]

    chk(len(rows) == 3, "three_percent_rows_survive_three_writes")
    chk(sum(1 for l in rows if l.startswith("| livecodebench")) == 2,
        "livecodebench_rows_not_eaten")
    chk(sum(1 for l in lines if l.startswith("| bench |")) == 1, "header_written_once")
    chk(sum(1 for l in text.splitlines()
            if l.startswith("|") and set(l) <= set("|- ")) == 1,
        "separator_written_once")   # blank lines are a subset of anything: match shape
    chk(rows[0].startswith("| livecodebench | m-local+contour"), "newest_first")

    # Tamper control: the old filter really does lose the row, so the assertions above are not
    # satisfied by accident.
    old_body = [l for l in lines if l.startswith("| ") and "bench |" not in l
                and not set(l) <= set("|- ")]
    chk(len(old_body) < len(rows), "control_old_substring_filter_loses_rows")

    # Fail-closed guard: if the filter ever drops more than the single header line, the writer
    # stops instead of silently losing a published row. Second header-shaped line = the case the
    # old substring filter created by accident.
    broken = os.path.join(td, "BROKEN.md")
    open(broken, "w", encoding="utf-8").write(
        text + "| bench | model | tasks | tasks sha16 | call | strict |\n")
    rc = 0
    try:
        pbs.write_digest(r_bfcl, broken)
    except SystemExit as e:
        rc = e.code
    chk(rc == 2, "row_count_mismatch_fails_closed")

print("pub digest writer contract: %d checks, %d failures" % (checks[0], len(fails)))
sys.exit(1 if fails else 0)
