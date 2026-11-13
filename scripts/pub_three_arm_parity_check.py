#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0 gate: every in-force public set must carry the three-arm standard in `PUB-DIGEST.md`.

Why this gate exists (2026-11-13, tick 126). The owner rule in force since 2026-11-12 is
"the cross-arm standard is THREE arms: bare local / contour <frozen stamp> in matched request
shape / ChatGPT codex", and the line's own P0 rule says a contour-parity row is admissible only
when the contour leg's REQUEST SHAPE equals the bare leg's. Since 2026-11-12 that census has been
re-derived BY HAND on every tick, and the hand version has already failed three measured times
with the same shape: a bench-name **substring** filter on the digest table silently drops rows --
tick 119 (first instance), tick 124 (`'bench |' not in line` also fires inside `livecodebench |`,
so all seven LiveCodeBench rows vanished and the census printed 42 rows instead of 49), and the
census helper written on tick 126 lost the whole series to `files = [..] and files` and printed
`files=0 GO=0` while 69 readings existed. A rule re-derived by hand every hour, in a form that has
already mis-counted three times, is a gate. This script registers no contour feature, launches no
arm, scores no byte and moves no published number.

Rules pinned here (all of them are properties of the table as published):

  1. vocabulary: an in-force set is a `MANIFEST.json` bench with `tasks > 0`. A bench with
     `tasks == 0` (SimpleBench, closed as unpinnable) may have NO percent row: a percent over an
     unpinned task file is a finding. A bench name in the table that MANIFEST does not know fails
     CLOSED (exit 2), because the table cannot be older or newer than the pin file;
  2. three arms per in-force set: a `bare` row (model == the local brain id exactly), a contour row
     in MATCHED request shape (model suffix `+contour-<stamp>` and the call cell names the matched
     shape), and a codex row (model == `gpt-6.1-sol`). A missing role is a finding;
  3. parity shape: a set whose only contour row is an ESCALATION-shape row (call cell names more
     than one ladder rung, or `enable_thinking off`) is a finding -- the escalation rows stay
     published as history and are superseded as parity rows, never edited;
  4. frozen line: every contour row must carry the frozen stamp. A contour row on another stamp is
     a finding, because the hard-bank contour line is frozen by owner decision 2026-11-08;
  5. Grok is NOT an arm and is NOT required: the line is cancelled by owner decision 2026-11-12, so
     a Grok cell may never satisfy rule 2 and its absence may never be reported as a missing arm.
     The cancel sentence is read out of `GROK-RESUME-PIN.json` at run time so this script cannot
     quote a stale status. A Grok percent row whose cell carries no superseded/cancelled label is
     handed to `pub_grok_cell_check.py`, not re-litigated here;
  6. sidecar rows (`+pub-repair-*` keep-best arms) are counted separately and never satisfy rule 2;
  7. self-census: every parsed row is attributed to exactly one bench and one role, and the sum of
     the per-bench census must equal the parsed row count -- the mechanical form of "no row was
     dropped by a name-substring filter".

Denominators are reported, not compared: rule 4 of the line (the local brain runs the full pinned
set, the cloud cross-arm slice is the first 300 ids) means bare/codex legitimately differ in task
count on gsm8k / arc-easy / arc-challenge / bfcl, so a common denominator is printed as a
`matched-cell` fact when it exists and as a stated skew when it does not.

Exit: 0 clean, 3 findings, 2 fail closed (missing artifact, malformed table, unknown bench).
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "benchmarks", "public")
DIGEST = os.path.join(PUB, "PUB-DIGEST.md")
MANIFEST = os.path.join(PUB, "MANIFEST.json")
GROK_PIN = os.path.join(PUB, "GROK-RESUME-PIN.json")

# The local brain id as it appears in the digest model column, and the cloud arm id.
BARE_MODEL = "qwen3.8-flash-next-iq3_s-basalt"
CODEX_MODEL = "gpt-6.1-sol"

# The frozen contour stamp of this line (tag stable-hard-0.0.2.56, owner decision 2026-11-08).
# A new frozen line means a NEW dated constant in a new commit, never an in-place edit of a
# published row: the numbers under the old stamp stay quotable.
FROZEN_CONTOUR_STAMP = "0.0.2.56"

GROK_MARK = "grok"


def parse_table(path: str) -> tuple[list[str], list[list[str]]]:
    """Read the digest table by COLUMNS. Never a substring filter on the bench cell."""
    with open(path, encoding="utf-8") as fh:
        lines = [ln for ln in fh if ln.startswith("|")]
    hdr: list[str] = []
    rows: list[list[str]] = []
    for ln in lines:
        cells = [c.strip() for c in ln.strip().strip("|").split("|")]
        if not hdr:
            if cells and cells[0] == "bench":
                hdr = cells
            continue
        if set(cells[0]) <= set("-: "):
            continue
        if len(cells) != len(hdr):
            raise SystemExit(
                f"FAIL CLOSED: digest row has {len(cells)} cells, header has {len(hdr)}: {ln[:120]}")
        rows.append(cells)
    if not hdr:
        raise SystemExit("FAIL CLOSED: no `| bench |` header row in the digest table")
    return hdr, rows


def role_of(model: str, call: str) -> str:
    m = model.lower()
    if GROK_MARK in m:
        return "grok(cancelled)"
    if model == CODEX_MODEL:
        return "codex"
    if model == BARE_MODEL:
        return "bare"
    if "+contour-" in m:
        low = call.lower()
        stamp = m.split("+contour-", 1)[1].strip()
        rungs = ""
        if "ladder rungs" in low:
            rungs = low.split("ladder rungs", 1)[1].split(";")[0].split(",first")[0]
        many = len([r for r in rungs.split(",") if r.strip().isdigit()]) > 1
        think_off = "enable_thinking off" in low
        matched = ("bare-matched" in low) or ("matched shape" in low)
        if matched and not many:
            return f"contour-matched[{stamp}]"
        if many or think_off:
            return f"contour-escalation[{stamp}]"
        return f"contour-shape-unknown[{stamp}]"
    if "pub-repair" in m:
        return "repair-sidecar"
    return "unknown-role"


def main(argv: list[str]) -> int:
    digest, manifest, pin = DIGEST, MANIFEST, GROK_PIN
    args = list(argv[1:])
    i = 0
    while i < len(args):
        if args[i] in ("--digest", "--manifest", "--pin"):
            if i + 1 >= len(args):
                print(f"FAIL CLOSED: {args[i]} needs a path")
                return 2
            if args[i] == "--digest":
                digest = args[i + 1]
            elif args[i] == "--manifest":
                manifest = args[i + 1]
            else:
                pin = args[i + 1]
            i += 2
        else:
            print(f"FAIL CLOSED: unknown argument {args[i]!r}")
            return 2
    for p in (digest, manifest):
        if not os.path.isfile(p):
            print(f"FAIL CLOSED: missing artifact {p}")
            return 2
    try:
        benches = json.load(open(manifest, encoding="utf-8"))["benches"]
    except Exception as exc:  # a pin file that cannot be parsed is never a pass
        print(f"FAIL CLOSED: {manifest} unreadable ({exc})")
        return 2

    try:
        hdr, rows = parse_table(digest)
    except SystemExit as exc:
        print(str(exc))
        return 2

    pinned = {b: int(v.get("tasks", 0)) for b, v in benches.items()}
    in_force = sorted(b for b, n in pinned.items() if n > 0)
    closed = sorted(b for b, n in pinned.items() if n == 0)

    findings: list[str] = []
    per_bench: dict[str, dict[str, int]] = {}
    total_roles = 0
    for r in rows:
        bench, model, tasks, _sha, call = r[0], r[1], r[2], r[3], r[4]
        role = role_of(model, call)
        total_roles += 1
        if bench not in pinned:
            print(f"FAIL CLOSED: digest bench {bench!r} is not in {os.path.basename(manifest)} "
                  f"-- the table and the task-file pins disagree")
            return 2
        if pinned[bench] == 0:
            findings.append(f"{bench}: a percent row exists for a set pinned at 0 tasks "
                            f"(closed as unpinnable) -- {model} {tasks}")
            continue
        d = per_bench.setdefault(bench, {})
        d[role] = d.get(role, 0) + 1

    # rule 7: the census cannot silently drop a row
    census_sum = sum(sum(d.values()) for d in per_bench.values())
    if census_sum != total_roles:
        findings.append(f"census self-check: {census_sum} attributed rows != {total_roles} parsed rows")

    # rules 2-4, per in-force set
    matched_cells: list[str] = []
    for bench in in_force:
        d = per_bench.get(bench, {})
        if not d:
            findings.append(f"{bench}: no digest row at all for an in-force set")
            continue
        contour = {k: v for k, v in d.items() if k.startswith("contour-")}
        matched_n = sum(v for k, v in contour.items() if k.startswith("contour-matched"))
        esc_n = sum(v for k, v in contour.items() if k.startswith("contour-escalation"))
        unknown_n = sum(v for k, v in contour.items() if k.startswith("contour-shape-unknown"))
        stamps = {k.split("[", 1)[1].rstrip("]") for k in contour}
        bad = sorted(s for s in stamps if s != FROZEN_CONTOUR_STAMP)
        if bad:
            findings.append(f"{bench}: contour row(s) on stamp(s) {bad}, the line is frozen at "
                            f"{FROZEN_CONTOUR_STAMP}")
        if unknown_n:
            findings.append(f"{bench}: {unknown_n} contour row(s) whose call cell names neither the "
                            f"matched shape nor an escalation -- parity cannot be certified")
        if matched_n == 0:
            findings.append(
                f"{bench}: no MATCHED-shape contour row (escalation rows: {esc_n}). The parity rule "
                f"refuses an escalation-shape row as the contour arm.")
        for role in ("bare", "codex"):
            if d.get(role, 0) == 0:
                findings.append(f"{bench}: missing {role} arm row")
        # matched-cell reporting (facts, not findings)
        bare_tasks, codex_tasks, contour_tasks = set(), set(), set()
        for r in rows:
            if r[0] != bench:
                continue
            role = role_of(r[1], r[4])
            try:
                n = int(r[2])
            except ValueError:
                continue
            if role == "bare":
                bare_tasks.add(n)
            elif role == "codex":
                codex_tasks.add(n)
            elif role.startswith("contour-matched"):
                contour_tasks.add(n)
        common = bare_tasks & codex_tasks & contour_tasks
        if common:
            matched_cells.append(f"{bench}: three arms share tasks={sorted(common)}")
        else:
            matched_cells.append(f"{bench}: skew bare{sorted(bare_tasks)} vs contour{sorted(contour_tasks)} "
                                 f"vs codex{sorted(codex_tasks)} (full set vs cross-arm slice)")

    # rule 5: Grok census, sentence read from the pin so it cannot go stale
    grok_status = "(no pin file, Grok status not quoted)"
    if os.path.isfile(pin):
        try:
            pj = json.load(open(pin, encoding="utf-8"))
            win = pj.get("owner_window") or {}
            phrase = win.get("cell_phrase")
            if isinstance(phrase, str) and phrase.strip():
                grok_status = phrase.strip()
            if win.get("cancelled_on"):
                grok_status += f" | cancelled_on={win['cancelled_on']}"
            else:
                grok_status += " | cancelled_on=null (re-armed: this census must be re-read)"
        except Exception as exc:
            print(f"note: Grok pin unreadable ({exc}); the cancel sentence is not quoted")
    grok_rows = sum(sum(v for k, v in d.items() if k.startswith("grok")) for d in per_bench.values())
    grok_benches = sorted(b for b, d in per_bench.items() if any(k.startswith("grok") for k in d))
    no_grok = [b for b in in_force if b not in grok_benches]

    print(f"three-arm parity gate: {len(rows)} digest rows, "
          f"{len(in_force)} in-force set(s), {len(closed)} closed ({', '.join(closed) or '-'})")
    for bench in in_force:
        d = per_bench.get(bench, {})
        print(f"  {bench:14s} " + " ".join(f"{k}={v}" for k, v in sorted(d.items())))
    print("Grok cells: %d row(s) over %s -- %s" % (grok_rows, grok_benches or "none", grok_status))
    print("Grok percent absent (never a missing arm): %s" % (no_grok or "none"))
    for line in matched_cells:
        print("  " + line)
    if findings:
        print(f"THREE-ARM PARITY: {len(rows)} rows, {len(findings)} FINDING(S)")
        for f in findings:
            print("  - " + f)
        return 3
    print(f"THREE-ARM PARITY: {len(rows)} rows / {len(in_force)} sets, 0 findings "
          f"(contour stamp {FROZEN_CONTOUR_STAMP}, Grok not an arm)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
