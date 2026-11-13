#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_three_arm_parity_check.py` (added 2026-11-13, tick 126).

The rule under test is the line's P0 standard: every in-force public set carries THREE arms --
bare local brain, contour <frozen stamp> in MATCHED request shape, codex -- and a Grok cell is
never one of them (the line is cancelled by owner decision 2026-11-12). That census has been
re-derived by hand on every tick since 2026-11-12 and has already mis-counted three measured times
through a bench-name SUBSTRING filter (tick 119, tick 124: `'bench |' not in line` also fires
inside `livecodebench |` and deleted seven rows from the count; tick 126: a helper's
`files = [..] and files` emptied the whole series). This test pins the machine version, including
the census self-check that makes a dropped row impossible to hide.

Cases (the digest is copied to a temp file for every tamper; the real MANIFEST and Grok pin stay
in place, so a tamper can never touch a published byte):

  1. the published table passes: exit 0, 49 rows, 9 in-force sets, Grok never an arm;
  2. dropping a codex row, a bare row, or the matched-shape contour row each turns exit 3 and
     names the set and the role;
  3. NON-VACUITY on the parity shape: dropping the ESCALATION contour row (superseded history)
     still passes -- the gate requires a matched row, not every contour row;
  4. NON-VACUITY on sidecars: dropping a `pub-repair` row and a Grok row still passes;
  5. a contour row on a stamp other than the frozen one is exit 3 (the frozen-line rule);
  6. a percent row for a set pinned at 0 tasks (SimpleBench, closed) is exit 3;
  7. a bench the manifest does not know, a missing header row, and a row with the wrong cell count
     all fail CLOSED with exit 2;
  8. the anti-substring control: three extra LiveCodeBench rows must show up as exactly +3 in the
     printed per-set census (a name filter that eats the longest bench name cannot survive it).
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "scripts", "pub_three_arm_parity_check.py")
DIGEST = os.path.join(ROOT, "benchmarks", "public", "PUB-DIGEST.md")

FAILED: list[str] = []
CHECKS = 0


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def run(digest_path: str) -> tuple[int, str]:
    p = subprocess.run([sys.executable, SCRIPT, "--digest", digest_path],
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def table_of(text: str) -> tuple[list[str], list[str]]:
    """Split the digest into (header block lines, data row lines).

    The header block is exactly the `| bench | ... |` line plus its `|---|` delimiter; every
    other `|`-line is a data row. (The first draft of this helper never flipped its `seen`
    flag, so every row landed in the header block and every tamper became a no-op -- an
    untested splitter is a fake tamper.)
    """
    head: list[str] = []
    rows: list[str] = []
    for ln in text.splitlines():
        if not ln.startswith("|"):
            continue
        if len(head) < 2:
            head.append(ln)
        else:
            rows.append(ln)
    if len(head) != 2:
        raise SystemExit(f"digest table has no header block: {head}")
    return head, rows


def write_tmp(text: str) -> str:
    fd, path = tempfile.mkstemp(prefix="pub-digest-tamper-", suffix=".md")
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def main() -> int:
    if not os.path.isfile(SCRIPT):
        print(f"MISSING SCRIPT: {SCRIPT}")
        return 1
    src = open(DIGEST, encoding="utf-8").read()
    head, rows = table_of(src)

    # 1. the published table passes
    rc, out = run(DIGEST)
    ck(rc == 0, f"published digest must pass, got exit {rc}: {out[-400:]}")
    ck("49 digest rows" in out, f"published census must report 49 rows, got: {out[:200]}")
    ck("9 in-force set(s)" in out, "published census must report 9 in-force sets")
    ck("Grok not an arm" in out, "a clean run must state that Grok is not an arm")
    ck("cancelled by owner decision 2026-11-12" in out,
       "the Grok sentence must be read out of the pin, not typed")

    def drop(pred) -> str:
        kept = [r for r in rows if not pred(r)]
        return "\n".join(head + kept) + "\n"

    def replace(old: str, new: str) -> str:
        return src.replace(old, new, 1)

    # 2. one arm missing per case
    rc, out = run(write_tmp(drop(lambda r: r.startswith("| mmlu-pro | gpt-6.1-sol"))))
    ck(rc == 3 and "mmlu-pro: missing codex arm row" in out,
       f"dropping the mmlu-pro codex row must be a finding naming the role, got {rc}: {out[-300:]}")
    rc, out = run(write_tmp(drop(lambda r: r.startswith("| mmlu-pro | qwen3.8-flash-next-iq3_s-basalt "))))
    ck(rc == 3 and "mmlu-pro: missing bare arm row" in out,
       f"dropping the mmlu-pro bare row must be a finding, got {rc}: {out[-300:]}")
    rc, out = run(write_tmp(drop(
        lambda r: r.startswith("| arc-easy | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56")
        and "bare-matched" in r)))
    ck(rc == 3 and "arc-easy: no MATCHED-shape contour row" in out,
       f"removing arc-easy's matched contour row must trip the parity rule, got {rc}: {out[-300:]}")

    # 3. non-vacuity: the escalation row is history, not a requirement
    rc, out = run(write_tmp(drop(
        lambda r: r.startswith("| arc-easy | qwen3.8-flash-next-iq3_s-basalt+contour-0.0.2.56")
        and "ladder rungs 512,1200" in r)))
    ck(rc == 0, f"dropping the superseded escalation contour row must still pass, got {rc}: {out[-300:]}")

    # 4. non-vacuity: sidecars and Grok cells are not arms
    rc, out = run(write_tmp(drop(lambda r: "pub-repair" in r)))
    ck(rc == 0, f"dropping every pub-repair sidecar row must still pass, got {rc}: {out[-300:]}")
    rc, out = run(write_tmp(drop(lambda r: "| grok-4.7 " in r)))
    ck(rc == 0, f"dropping every Grok row must still pass (the line is cancelled), got {rc}: {out[-300:]}")
    rc, out = run(write_tmp(drop(lambda r: "bare-matched" in r)))
    # Data-derived expectation: 8 of the 9 sets carry their ONLY matched-shape contour row with the
    # `bare-matched` marker; LiveCodeBench additionally has a matched row phrased "matched shape",
    # so it is the one set that must survive. Reading this off the table beats assuming a count.
    ck(rc == 3 and out.count("no MATCHED-shape contour row") == 8
       and "livecodebench: no MATCHED-shape contour row" not in out,
       f"removing every bare-matched row must flag exactly the 8 sets that lose their only matched "
       f"row, got exit {rc}: {out[-700:]}")

    # 5. a contour row off the frozen stamp
    rc, out = run(write_tmp(replace("+contour-0.0.2.56", "+contour-0.0.2.57")))
    ck(rc == 3 and "frozen at" in out,
       f"a contour row on 0.0.2.57 must trip the frozen-line rule, got {rc}: {out[-300:]}")

    # 6. a percent over a set pinned at 0 tasks
    fake = ("| simplebench | qwen3.8-flash-next-iq3_s-basalt | 10 | deadbeefdeadbeef | "
            "temp 0.7, max_tokens 1200; checker pub-checkers-v2 | 7/10 = **70.0%** |\n")
    rc, out = run(write_tmp(src + fake))
    ck(rc == 3 and "pinned at 0 tasks" in out,
       f"a SimpleBench percent must be a finding, got {rc}: {out[-300:]}")

    # 7. fail-closed cases
    unknown = ("| terminal-bench | qwen3.8-flash-next-iq3_s-basalt | 10 | deadbeefdeadbeef | "
               "temp 0.7; checker pub-checkers-v2 | 7/10 = **70.0%** |\n")
    rc, out = run(write_tmp(src + unknown))
    ck(rc == 2 and "not in" in out,
       f"an unknown bench row must fail closed with exit 2, got {rc}: {out[-300:]}")
    rc, out = run(write_tmp("\n".join(rows) + "\n"))
    ck(rc == 2 and "no `| bench |` header" in out,
       f"a table with no header must fail closed, got {rc}: {out[-300:]}")
    rc, out = run(write_tmp(src + "| gsm8k | qwen3.8-flash-next-iq3_s-basalt | 300 |\n"))
    ck(rc == 2 and "cells" in out, f"a ragged row must fail closed, got {rc}: {out[-300:]}")

    # 8. anti-substring control: the longest bench name must survive the census
    extra = "".join(
        "| livecodebench | qwen3.8-flash-next-iq3_s-basalt | 175 | 8da729553c7c5710 | "
        "temp 0.7, max_tokens 2400; checker lcb-exec-v2 | 101/175 = **57.7%** |\n" for _ in range(3))
    rc, out = run(write_tmp(src + extra))
    m = re.search(r"^\s+livecodebench\s+(.*)$", out, re.M)
    ck(rc == 0 and m is not None, f"three extra bare rows must keep the table clean, got {rc}")
    if m:
        counted = sum(int(v) for v in re.findall(r"=(\d+)", m.group(1)))
        ck(counted == 10,
           f"anti-substring control: livecodebench census must be 7+3=10 rows, counted {counted} "
           f"(a bench-name substring filter drops the longest bench name -- tick 124)")
    ck("52 digest rows" in out, f"the row count must follow the tamper, got: {out[:160]}")

    if FAILED:
        print(f"THREE-ARM PARITY TEST: {CHECKS - len(FAILED)}/{CHECKS} FAILED:")
        for f in FAILED:
            print("  - " + f)
        return 1
    print(f"THREE-ARM PARITY TEST: {CHECKS}/{CHECKS} checks green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
