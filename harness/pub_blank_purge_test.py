#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_cloud_blank_purge.py` (added 2026-11-11).

Hermetic temp fixtures only: it writes synthetic arm files in a temp dir, makes no network
call and reads no real answer file. What it pins:

  1. a clean arm file (every row finish=ok) is reported clean, exit 0, bytes untouched;
  2. parked non-ok rows are REPORTED (exit 3) without --write and the file bytes do not move;
  3. --write moves exactly the parked rows: ok ids and their order survive cell-for-cell, the
     quarantine holds exactly the parked id set, a byte-exact pre-purge copy is kept, the run
     is idempotent (a second pass reports clean), and an ok row that carries an
     `engine_error` string is still never moved;
  4. the tool refuses (exit 3, bytes untouched) on anomalies it must not decide alone: a
     duplicate id among ok rows, an ok row with an empty answer;
  5. input gaps exit 1 and are never a green light: missing file, empty file, unparseable
     line;
  6. an all-blank arm file (an arm with no pinned ok rows) purges to an empty file with exit 0,
     because parked rows carry zero credit — while the same empty file read later is an input
     gap, which is why the launcher guards with `[ -s file ]`.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "pub_cloud_blank_purge.py")

CHECKS = 0
FAILED = []


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def sha16(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def run(path: str, write: bool = False):
    cmd = [sys.executable, SCRIPT, path] + (["--write"] if write else [])
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def arm(tmp: str, name: str, rows) -> str:
    p = os.path.join(tmp, name)
    with open(p, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return p


def R(i, finish="ok", answer="42", extra=None):
    r = {"id": "b-%04d" % i, "bench": "fakebench", "arm": "grok",
         "model": "grok-4.7", "finish": finish, "answer": answer, "seconds": 1.0}
    if finish != "ok":
        r["engine_error"] = "rc1: transport said no"
    if extra:
        r.update(extra)
    return r


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        # 1. clean arm file
        p = arm(tmp, "clean.jsonl", [R(0), R(1), R(2)])
        h = sha16(p)
        rc, out = run(p)
        ck(rc == 0 and "nothing parked" in out, "clean arm file must exit 0: %s" % out[-300:])
        ck(sha16(p) == h, "clean run must not touch the bytes")

        # 2. report mode on parked blanks: exit 3, bytes unchanged
        p = arm(tmp, "blank.jsonl", [R(0), R(1, finish="rc1"), R(2), R(3, finish="error")])
        h = sha16(p)
        rc, out = run(p)
        ck(rc == 3 and "REPORT MODE" in out and "b-0001" in out,
           "report mode must exit 3 and name the parked ids: %s" % out[-300:])
        ck(sha16(p) == h, "report mode must not touch the bytes")

        # 3. --write: exact split, byte-exact copy, idempotent, odd-but-ok row preserved
        p = arm(tmp, "mixed.jsonl", [
            R(0),
            R(1, finish="rc1"),
            R(2, extra={"engine_error": "transient but the answer is real"}),  # ok + error field
            R(3, finish="error"),
            R(4)])
        h = sha16(p)
        rc, out = run(p, write=True)
        ck(rc == 0 and "PURGED" in out, "--write must purge and verify: %s" % out[-400:])
        rows = [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
        ck([r["id"] for r in rows] == ["b-0000", "b-0002", "b-0004"],
           "ok ids and their order must survive cell-for-cell: %s" % [r["id"] for r in rows])
        ck(all(r.get("finish") == "ok" for r in rows), "no non-ok row may stay in the arm file")
        ck(any(r["id"] == "b-0002" and r.get("engine_error") for r in rows),
           "an ok row that carries an engine_error string must NOT be moved")
        bak = [f for f in os.listdir(tmp) if f.startswith("mixed.jsonl.blank-quarantine-")]
        keep = [f for f in os.listdir(tmp) if f.startswith("mixed.jsonl.pre-purge-")]
        ck(len(bak) == 1 and len(keep) == 1, "quarantine and pre-purge copy must both exist")
        if bak:
            moved = [json.loads(l) for l in
                     open(os.path.join(tmp, bak[0]), encoding="utf-8") if l.strip()]
            ck([r["id"] for r in moved] == ["b-0001", "b-0003"],
               "quarantine must hold exactly the parked rows in order: %s"
               % [r["id"] for r in moved])
            ck(all(r.get("finish") != "ok" for r in moved),
               "an ok row must never be moved into the quarantine")
        if keep:
            ck(sha16(os.path.join(tmp, keep[0])) == h,
               "the pre-purge copy must be byte-exact with the original file")
        rc2, out2 = run(p)
        ck(rc2 == 0 and "nothing parked" in out2,
           "the purge must be idempotent: %s" % out2[-300:])

        # 4. anomalies this tool must not decide alone
        p = arm(tmp, "dup.jsonl", [R(0), R(0), R(1, finish="rc1")])
        h = sha16(p)
        rc, out = run(p, write=True)
        ck(rc == 3 and "duplicate ids" in out, "duplicate ok ids must REFUSE: %s" % out[-300:])
        ck(sha16(p) == h, "a refused purge must not touch the bytes")
        p = arm(tmp, "emptyans.jsonl", [R(0, answer="   "), R(1, finish="rc1")])
        h = sha16(p)
        rc, out = run(p, write=True)
        ck(rc == 3 and "EMPTY answer" in out, "an ok row with an empty answer must REFUSE: %s"
           % out[-300:])
        ck(sha16(p) == h, "a refused purge must not touch the bytes (empty answer case)")

        # 5. input gaps exit 1, never a green light
        rc, out = run(os.path.join(tmp, "no-such.jsonl"))
        ck(rc == 1 and "INPUT GAP" in out, "a missing arm file is an input gap: %s" % out[-200:])
        p = arm(tmp, "zero.jsonl", [])
        rc, out = run(p)
        ck(rc == 1 and "INPUT GAP" in out, "an empty arm file is an input gap: %s" % out[-200:])
        p = os.path.join(tmp, "broken.jsonl")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(R(0)) + "\n{not json}\n")
        rc, out = run(p)
        ck(rc == 1 and "UNPARSEABLE" in out, "an unparseable line must be loud: %s" % out[-200:])

        # 6. an all-blank arm file (no pinned ok rows) purges to empty with exit 0
        p = arm(tmp, "allblank.jsonl", [R(0, finish="rc1"), R(1, finish="error")])
        rc, out = run(p, write=True)
        ck(rc == 0 and "PURGED" in out, "an all-blank arm file purges: %s" % out[-300:])
        ck([l for l in open(p, encoding="utf-8") if l.strip()] == [],
           "an all-blank arm file must end with no rows")

    print("pub_cloud_blank_purge contract: %d checks, %d failure(s)" % (CHECKS, len(FAILED)))
    for m in FAILED:
        print("FAIL: %s" % m)
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
