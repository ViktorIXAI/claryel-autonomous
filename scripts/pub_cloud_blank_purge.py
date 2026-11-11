#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quarantine parked non-ok rows out of a resumable cloud arm file (added 2026-11-11).

Why this exists. `scripts/pub_bench_cloud.py` appends EVERY attempted row to the arm file,
including the failures (`finish` = `rc1`/`error` plus an `engine_error` string), and it stops
a leg only after THREE consecutive transport failures; otherwise it returns 0 as soon as the
set was walked with at least one ok row. Two consequences for the resumable Grok queue of the
2026-11-12 window, found by reading the shipped runner rather than by waiting for them:

  * a single transport flake parks a blank in the arm file, and the public scorer keeps the
    FIRST row per id, so a parked blank is a loss forever unless it is purged first — the
    rule is published practice (the 2026-11-09 timeout blanks were moved to
    `*.bad-timeout.bak` by hand) but no tool did it mechanically;
  * `scripts/pub_grok_resume_check.py` turns a parked non-ok row into a hard NO-GO (exit 3)
    in BOTH owner-window modes, so an unpurged flake halts the NEXT day's leg of a queue that
    is expected to chain across days.

This tool is that missing step: it moves non-ok rows to a named zero-credit quarantine file
and rewrites the arm file with exactly the ok rows. It never touches an ok row, never edits
answer text, deletes nothing, and keeps a byte-exact copy of the pre-purge file. It makes zero
model and zero network calls.

Exit codes:
  0  report mode: nothing parked (or, with --write, purge completed and verified)
  3  report mode: blanks parked (run with --write); OR an anomaly this tool must not decide
     alone (a duplicate id among ok rows, an ok row with an empty answer, an ok row that
     appears twice with different bytes); OR the post-write verification failed
  1  input gap: the arm file is missing, empty or unparseable — never treated as clean

Contract test: `harness/pub_blank_purge_test.py` (hermetic temp fixtures, no network).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import time

NOT_OK = "non-ok"


def sha16(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def read_rows(path: str):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for ln, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception as exc:                       # noqa: BLE001 - input gap, loudly
                raise SystemExit("UNPARSEABLE line %d in %s: %s" % (ln, path, exc))
    return rows


def classify(rows):
    ok, bad = [], []
    for r in rows:
        (ok if r.get("finish") == "ok" else bad).append(r)
    ids = [r.get("id") for r in ok]
    dup_ok = sorted({i for i in ids if ids.count(i) > 1})
    empty_ok = sorted(str(r.get("id")) for r in ok if not (r.get("answer") or "").strip())
    return ok, bad, dup_ok, empty_ok


def main() -> int:
    ap = argparse.ArgumentParser(prog="pub_cloud_blank_purge.py")
    ap.add_argument("arm_file")
    ap.add_argument("--write", action="store_true",
                    help="actually move the parked rows; without it this is a report")
    a = ap.parse_args()

    path = a.arm_file
    if not os.path.exists(path):
        print("INPUT GAP: arm file %s does not exist" % path)
        return 1
    rows = read_rows(path)
    if not rows:
        print("INPUT GAP: arm file %s holds no rows" % path)
        return 1

    ok, bad, dup_ok, empty_ok = classify(rows)
    print("arm file %s  rows %d  unique-ids %d  ok %d  %s %d  sha256-16 %s"
          % (os.path.basename(path), len(rows), len({r.get("id") for r in rows}), len(ok),
             NOT_OK, len(bad), sha16(path)))
    for r in bad[:20]:
        why = str(r.get("engine_error") or r.get("finish") or "")[:90].replace("\n", " ")
        print("   parked %s  finish=%-6s %s" % (r.get("id"), r.get("finish"), why))
    if len(bad) > 20:
        print("   ... %d more parked rows" % (len(bad) - 20))

    anomalies = []
    if dup_ok:
        anomalies.append("duplicate ids among finish=ok rows (%s) — the scorer keeps the FIRST "
                         "row, so this needs a human decision, not a purge"
                         % ", ".join(str(i) for i in dup_ok[:6]))
    if empty_ok:
        anomalies.append("finish=ok rows with an EMPTY answer (%s) — zero-credit by rule, but "
                         "this tool only moves non-ok rows"
                         % ", ".join(str(i) for i in empty_ok[:6]))
    for m in anomalies:
        print("REFUSE: %s" % m)
    if anomalies:
        return 3

    if not bad:
        print("nothing parked — the arm file is clean for a resume")
        return 0
    if not a.write:
        print("REPORT MODE: %d parked row(s) would be quarantined (run with --write before "
              "pub_grok_resume_check.py, or that gate refuses the resume)" % len(bad))
        return 3

    stamp = time.strftime("%Y%m%d-%H%M%S", time.gmtime())
    bak = "%s.blank-quarantine-%s.bak" % (path, stamp)
    keep = "%s.pre-purge-%s.keep" % (path, stamp)
    with open(bak, "w", encoding="utf-8") as fh:
        for r in bad:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    shutil.copyfile(path, keep)

    tmp = path + ".purging"
    with open(tmp, "w", encoding="utf-8") as fh:
        for r in ok:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    os.replace(tmp, path)

    after = read_rows(path)
    ok_ids_before = [r.get("id") for r in ok]
    ok_ids_after = [r.get("id") for r in after]
    moved = read_rows(bak)
    problems = []
    if ok_ids_after != ok_ids_before:
        problems.append("ok ids changed order/content: %d before, %d after"
                        % (len(ok_ids_before), len(ok_ids_after)))
    if any(r.get("finish") == "ok" for r in moved):
        problems.append("an ok row was moved into the quarantine")
    if {r.get("id") for r in moved} != {r.get("id") for r in bad}:
        problems.append("quarantine id set does not equal the parked id set")
    if len(moved) != len(bad):
        problems.append("quarantine holds %d rows, %d were parked" % (len(moved), len(bad)))
    if problems:
        print("VERIFY FAILED: %s  (quarantine %s kept, byte-exact copy %s kept)"
              % ("; ".join(problems), bak, keep))
        return 3

    print("PURGED: %d parked row(s) -> %s  sha256-16 %s" % (len(bad), bak, sha16(bak)))
    print("        arm file now rows %d  ok %d  sha256-16 %s (was %s)"
          % (len(after), len(ok), sha16(path), sha16(keep)))
    print("        byte-exact pre-purge copy kept at %s (zero credit for the parked rows)"
          % keep)
    return 0


if __name__ == "__main__":
    sys.exit(main())
