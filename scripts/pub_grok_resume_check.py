#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Byte-level resume gate for the four suspended Grok arms (added 2026-11-11).

Why this exists: the owner suspended the Grok legs on 2026-11-09 (quota exhausted on the
owner side) and the resume window opens 2026-11-12. From tick 21 to tick 39 of this line
the identity of the two stored partials (gpqa-diamond 139 rows, humaneval 120 rows) was
re-read by hand every tick and the numbers were retyped into commit messages and
`LEG-INCIDENTS.md` prose. Nineteen hand readings of the same file is a rule, so it is now
a gate. It also makes the one thing that must not drift before 1144 paid calls are spent
mechanical: the resume set, i.e. exactly which ids the resumable runner will still ask.

The tool makes ZERO model/cloud calls. It reads only:

  * the PINNED task files `benchmarks/public/<bench>.tasks.jsonl` (through
    `pub_bench_score.manifest_tasks_cell`, so a task file whose bytes moved fails closed
    and no second hash convention is minted for a pinned file),
  * the local arm answer files under `--ws` (untracked workspace),
  * the pinned identity `benchmarks/public/GROK-RESUME-PIN.json`.

It fails closed (exit 3) on the classes that would silently corrupt a resumed arm:

  * identity drift: rows / unique ids / finish=ok / empty answers / SHA-256-16 of the
    stored answer file do not match the pin;
  * a duplicate id inside the arm file - the public scorer keeps the FIRST row per id, so
    a duplicate parked in front of a real answer is a permanent loss;
  * a non-`ok` row parked in the arm file (the same trap: a quarantined blank scored
    forever);
  * an `ok` row with an empty answer;
  * resume-set drift: the derived remaining count, first or last remaining id differs
    from the pin (the 2026-11-11 05:31 launcher-guard bug wrote 4 rows inside the
    suspension window - that is exactly what this line catches).

Zero-credit quarantine files (`*.bak`) are censused and printed as evidence, never turned
into a finding by themselves: a quarantined id is not permanently excluded (the 2026-11-09
timeout blanks were legitimately re-asked), so the byte-level guarantee that no uncredited
row was merged back is the arm-file SHA-256/16 + resume-set check, which pin the exact rows.

Two modes, decided from `owner_window.suspended_until` and the run date (`--as-of`):

  * window CLOSED (today < suspended_until, i.e. now): the pin is an exact snapshot. Row
    counts, the answer-file hash and the resume set must match byte-for-byte, and ANY
    growth is a finding, because no Grok call is legal inside the window - that is exactly
    the 2026-11-11 05:31 class, where a launcher whose date guard parsed as a redirection
    wrote 4 rows that had to be quarantined with zero credit;
  * window OPEN (the resume day itself and after): the pin is a floor. Every id the pin
    records as stored must still be stored (`pinned_ok_ids` - lost work is a finding), the
    corruption classes above still apply, and growth beyond the pin is reported as
    progress with a live resume set instead of a false alarm, so a healthy resumed queue is
    never halted by a gate that only froze one moment.

A `owner_window.cancelled_on` (ISO date, `suspended_until: null`) makes the window
CANCELLED: from that date on it is CLOSED with no end, so the pinned snapshot never expires
and every further Grok row is a finding. That is the owner decision of 2026-11-12 06:40 CET
(stop touching Grok, very few limits left, Grok cancelled), which superseded the 2026-11-09
"resumes 2026-11-12" window the same day it opened. A run date before the cancellation with
no window end in the pin fails CLOSED rather than reading as a green light.

Exit codes: 0 = RESUME-READY (identity matches the pin, resume set exact), 3 = findings
(do NOT spend quota), 1 = input gap (missing pin, missing bench entry, an expected answer
file absent). An input gap is never a green light.

A third mode (`--write-pin`) regenerates the pin from the stored bytes instead of checking
it, so the "regenerate the pin at window end" instruction is mechanical rather than a
hand-edited JSON over a 500-id list: every field is READ from the pinned task file (through
the same MANIFEST pin guard) and from the arm file, the top-level owner window, queue order,
resume rule and any quarantine evidence are carried over verbatim, and the writer REFUSES
instead of laundering a duplicate id, a parked non-ok row or an empty `ok` answer into the
next window's resume identity. Without `--allow-in-flight` it also refuses while a queued
leg is still growing, because such a pin freezes a moment the runner is about to move.
Contract test: `harness/pub_grok_pin_regen_test.py`.

A set pinned as "never legged" (`answer_file: null`) is not exempt from the byte checks once
its leg has started: the runner's output path is the convention `<ws>/<bench>/pub-grok.jsonl`,
so that path is derived and censused, and its resume set is read live. Without the derivation
the gate reported "stored 0 rows / resume set 500 ids" for the 2026-11-12 mmlu-pro leg while
175 rows were already on disk, i.e. the only sets a day-two resume actually needs the gate for
were the two it could not see.

`PUB_MANIFEST_OVERRIDE` points the MANIFEST pin guard at another `MANIFEST.json`; it
exists only so the contract test in `harness/pub_grok_resume_test.py` can run hermetic
fixtures. The default is the published repo manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import pub_bench_score as pbs  # noqa: E402  (reuse of the published pin guard)

FINDINGS: list[str] = []
GAPS: list[str] = []
PROGRESS: list[str] = []
CHECKS = 0


def sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()[:16]


def read_rows(path: str) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def census(path: str) -> dict:
    rows = read_rows(path)
    ids = [r.get("id") for r in rows]
    ok = [r for r in rows if r.get("finish") == "ok"]
    seen, dup = set(), []
    for i in ids:
        if i in seen:
            dup.append(i)
        seen.add(i)
    return {
        "rows": len(rows),
        "unique": len(set(ids)),
        "ok": len(ok),
        "empty": sum(1 for r in ok if not (r.get("answer") or "").strip()),
        "bad_finish": [r.get("id") for r in rows if r.get("finish") != "ok"],
        "dup": sorted(set(dup)),
        "sha256_16": sha16(path),
    }


def task_ids(tasks_path: str) -> list[str]:
    out = []
    with open(tasks_path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line)["id"])
    return out


def check_arm(name: str, spec: dict, repo: str, ws: str, window_open: bool) -> int:
    """Census one arm against its pin. Returns how many pinned ids are still unasked
    (0 on an early input-gap return, which cannot contribute a resume set)."""
    global CHECKS
    tasks_path = os.path.join(repo, "benchmarks", "public", "%s.tasks.jsonl" % name)
    if not os.path.exists(tasks_path):
        GAPS.append("%s: pinned task file %s is missing" % (name, tasks_path))
        return 0
    cell = pbs.manifest_tasks_cell(name, tasks_path)
    CHECKS += 1
    if cell != spec.get("expected_tasks_cell"):
        FINDINGS.append("%s: tasks cell is %s, pin expects %s"
                        % (name, cell, spec.get("expected_tasks_cell")))

    order = task_ids(tasks_path)
    if len(order) != spec.get("expected_pinned_tasks"):
        FINDINGS.append("%s: pinned task file holds %d ids, pin expects %d"
                        % (name, len(order), spec.get("expected_pinned_tasks")))
    CHECKS += 1

    rel = spec.get("answer_file")
    apath = os.path.join(ws, rel) if rel else None
    if apath is None:
        # A set pinned as "never legged" names no answer file, so without this the gate is
        # BLIND to it the moment its leg starts (measured 2026-11-12 while the mmlu-pro Grok
        # leg was mid-flight: the arm file held 175 rows and the gate still printed
        # "stored 0 rows / resume set 500 ids"). The runner's own output path is the
        # convention `<ws>/<bench>/pub-grok.jsonl`, so derive it and census the real bytes:
        # the corruption classes (duplicate id, parked non-ok row, empty ok answer) and the
        # live resume set then apply to a set the pin predates. Growth over a 0-row pin is
        # legal progress only with the owner window OPEN and an uncredited write (finding)
        # inside the closed window, exactly as for a pinned arm.
        cand = os.path.join(ws, name, "pub-grok.jsonl")
        if os.path.exists(cand):
            apath = cand
            print("   answer file derived by convention (%s/pub-grok.jsonl): the pin names "
                  "no file for this set, so its bytes are censused and its resume set is "
                  "read live" % name)
    if apath is None:
        if int(spec.get("expected_rows", 0)) > 0:
            GAPS.append("%s: pin expects %d stored rows but the pin names no answer file"
                        % (name, int(spec["expected_rows"])))
            return 0
        c = {"rows": 0, "unique": 0, "ok": 0, "empty": 0, "bad_finish": [], "dup": [],
             "sha256_16": "-"}
    elif not os.path.exists(apath):
        if int(spec.get("expected_rows", 0)) > 0:
            GAPS.append("%s: answer file %s is missing while the pin expects %d rows"
                        % (name, apath, int(spec["expected_rows"])))
            return 0
        c = {"rows": 0, "unique": 0, "ok": 0, "empty": 0, "bad_finish": [], "dup": [],
             "sha256_16": "-"}
    else:
        c = census(apath)
    CHECKS += 1

    stored_ok_ids: set = set()
    if apath and os.path.exists(apath):
        stored_ok_ids = {r.get("id") for r in read_rows(apath) if r.get("finish") == "ok"}
    pinned_ok = set(spec.get("pinned_ok_ids") or [])
    lost = sorted(str(i) for i in (pinned_ok - stored_ok_ids))
    if lost:
        FINDINGS.append("%s: %d ids the pin records as stored finish=ok are GONE from the arm "
                        "file: %s - stored work was deleted or rewritten"
                        % (name, len(lost), ", ".join(lost[:8])))
    grew = (c["ok"] > int(spec.get("expected_ok") or 0)
            or c["rows"] > int(spec.get("expected_rows") or 0))
    if grew and not window_open:
        FINDINGS.append("%s: the arm file holds %d rows / %d ok while the pin holds %s / %s "
                        "INSIDE the closed owner window - no Grok call is allowed there, so "
                        "any growth is an uncredited write and must be quarantined with zero "
                        "credit (this is the 2026-11-11 05:31 launcher-guard class)"
                        % (name, c["rows"], c["ok"], spec.get("expected_rows"),
                           spec.get("expected_ok")))
    elif grew:
        PROGRESS.append("%s: %d ok ids stored vs %s pinned - the window is open, growth is "
                        "legal; regenerate the pin at window end"
                        % (name, c["ok"], spec.get("expected_ok")))
    if not grew:
        for key in ("rows", "unique", "ok", "empty"):
            if c[key] != spec.get("expected_" + key):
                FINDINGS.append("%s: stored %s is %s, pin expects %s"
                                % (name, key, c[key], spec.get("expected_" + key)))
        if spec.get("answer_file") and os.path.exists(str(apath)) and c["sha256_16"] != spec.get("answer_file_sha256_16"):
            FINDINGS.append("%s: answer-file SHA-256/16 is %s, pin expects %s - the stored "
                            "bytes moved (an uncredited write, a truncation or an edit)"
                            % (name, c["sha256_16"], spec.get("answer_file_sha256_16")))
    CHECKS += 1

    if c["dup"]:
        FINDINGS.append("%s: duplicate ids inside the arm file %s - the public scorer keeps "
                        "the FIRST row per id, so a duplicate parked in front of a real "
                        "answer is a permanent loss" % (name, ", ".join(c["dup"][:6])))
    if c["bad_finish"]:
        FINDINGS.append("%s: non-ok rows parked in the arm file %s - a parked blank is "
                        "scored as a loss forever; purge before any resume"
                        % (name, ", ".join(str(i) for i in c["bad_finish"][:6])))
    if c["empty"]:
        FINDINGS.append("%s: %d finish=ok rows carry an empty answer" % (name, c["empty"]))

    done = set()
    if apath and os.path.exists(apath):
        done = {r.get("id") for r in read_rows(apath) if r.get("finish") == "ok"}
    remaining = [i for i in order if i not in done]
    if not grew:
        exp_n = spec.get("expected_remaining")
        if len(remaining) != exp_n:
            FINDINGS.append("%s: resume set is %d ids, pin expects %d"
                            % (name, len(remaining), exp_n))
        CHECKS += 1
        if exp_n:
            first, last = remaining[0] if remaining else None, remaining[-1] if remaining else None
            if first != spec.get("expected_first_remaining") or last != spec.get("expected_last_remaining"):
                FINDINGS.append("%s: resume range is %s..%s, pin expects %s..%s"
                                % (name, first, last, spec.get("expected_first_remaining"),
                                   spec.get("expected_last_remaining")))
                CHECKS += 1
    else:
        print("   resume set read live (the pin is behind the stored bytes): %d ids %s..%s"
              % (len(remaining), remaining[0] if remaining else "-",
                 remaining[-1] if remaining else "-"))

    for q in spec.get("quarantine", []):
        qpath = os.path.join(ws, q.get("file", ""))
        if not os.path.exists(qpath):
            print("   note: quarantine file %s not present locally (informational)" % qpath)
            continue
        qc = census(qpath)
        # No finding here on purpose: a quarantine file is evidence of a ZERO-CREDIT write,
        # not a permanent exclusion of those ids - the timeout blanks of 2026-11-09 were
        # legitimately re-asked and are now real rows. The byte-level guarantee that an
        # uncredited row was never merged back is the arm-file SHA-256/16 + resume-set check
        # above, which pins the exact stored rows.
        print("   zero-credit quarantine: %-52s rows %3d ok %3d sha256-16 %s"
              % (q.get("file"), qc["rows"], qc["ok"], qc["sha256_16"]))
        CHECKS += 1

    print("%-13s stored %4d rows / %4d ok / sha256-16 %-16s | resume set %4d ids %s..%s"
          % (name, c["rows"], c["ok"], c["sha256_16"], len(remaining),
             (remaining[0] if remaining else "-"), (remaining[-1] if remaining else "-")))
    return len(remaining)


def derive_arm(name: str, spec: dict, repo: str, ws: str) -> dict:
    """Read the stored bytes of one arm and return the pin record for them.

    Every number is READ, never typed: `expected_tasks_cell` comes from the published
    MANIFEST guard (`pub_bench_score.manifest_tasks_cell`, so a moved task file exits 2)
    and the row/ok/empty/hash fields come from `census()` on the arm file itself. The
    answer path follows the same derivation the gate uses (pin value, else the
    conventional `<ws>/<bench>/pub-grok.jsonl`), so a pin can never be regenerated blind
    to a leg the pin predates — the tick-68 defect class.
    """
    tasks_path = os.path.join(repo, "benchmarks", "public", "%s.tasks.jsonl" % name)
    if not os.path.exists(tasks_path):
        GAPS.append("%s: pinned task file %s is missing" % (name, tasks_path))
        return {}
    cell = pbs.manifest_tasks_cell(name, tasks_path)
    order = task_ids(tasks_path)

    rel = spec.get("answer_file")
    apath = os.path.join(ws, rel) if rel else None
    if apath is None:
        cand = os.path.join(ws, name, "pub-grok.jsonl")
        apath = cand if os.path.exists(cand) else None
        rel = os.path.relpath(cand, ws) if apath else None
    if apath and os.path.exists(apath):
        c = census(apath)
        rows = read_rows(apath)
    else:
        c = {"rows": 0, "unique": 0, "ok": 0, "empty": 0, "bad_finish": [], "dup": [],
             "sha256_16": "-"}
        rows = []

    # A pin is the byte-level floor of the NEXT window, so minting it from corrupt bytes
    # would launder a duplicate id, a parked non-ok row or an empty ok answer into the
    # resume identity. Refuse instead.
    if c["dup"]:
        FINDINGS.append("%s: refusing to mint a pin from bytes with duplicate ids %s"
                        % (name, ", ".join(str(i) for i in c["dup"][:6])))
    if c["bad_finish"]:
        FINDINGS.append("%s: refusing to mint a pin from bytes with non-ok rows parked %s"
                        % (name, ", ".join(str(i) for i in c["bad_finish"][:6])))
    if c["empty"]:
        FINDINGS.append("%s: refusing to mint a pin from bytes with %d empty finish=ok "
                        "answers" % (name, c["empty"]))

    ok_ids = [r.get("id") for r in rows if r.get("finish") == "ok" and r.get("id") is not None]
    if len(ok_ids) != len([r for r in rows if r.get("finish") == "ok"]):
        FINDINGS.append("%s: finish=ok rows without an id are present - a row the resume set "
                        "cannot name is never pinnable" % name)
    ok_set = set(ok_ids)
    pinned_ok = [i for i in order if i in ok_set]          # task-file order, not sorted()
    pinned_ok += sorted(i for i in ok_ids if i not in set(order))
    remaining = [i for i in order if i not in ok_set]
    if not remaining:
        status = ("complete: %d/%d ids stored finish=ok, no resume set left"
                  % (len(ok_ids), len(order)))
    else:
        status = ("partial: %d of %d ids stored finish=ok; resume set %d ids %s..%s"
                  % (len(ok_ids), len(order), len(remaining), remaining[0], remaining[-1]))

    rec = {
        "expected_tasks_cell": cell,
        "expected_pinned_tasks": len(order),
        "answer_file": rel,
        "status": status,
        "expected_rows": c["rows"],
        "expected_unique": c["unique"],
        "expected_ok": c["ok"],
        "expected_empty": c["empty"],
        "answer_file_sha256_16": c["sha256_16"],
        "pinned_ok_ids": pinned_ok,
        "expected_remaining": len(remaining),
        "expected_first_remaining": remaining[0] if remaining else None,
        "expected_last_remaining": remaining[-1] if remaining else None,
    }
    if spec.get("quarantine"):
        # operator-maintained evidence of zero-credit writes: carried over verbatim,
        # never rewritten from bytes (the files themselves are censused by the gate).
        rec["quarantine"] = spec["quarantine"]
    print("pin record %-13s rows %4d ok %4d sha256-16 %-16s resume %4d ids %s..%s"
          % (name, c["rows"], c["ok"], c["sha256_16"], len(remaining),
             remaining[0] if remaining else "-", remaining[-1] if remaining else "-"))
    return rec


def write_pin(args) -> int:
    """Regenerate the resume pin from the stored bytes (zero model/cloud calls).

    Why this exists: the gate itself prints "regenerate the pin at window end" and every
    previous pin was hand-edited. A hand-typed pin over a big `pinned_ok_ids` list is
    exactly how a census goes blind again (tick 68 fixed gate blindness; the 19 hand
    readings of tick 21-39 fixed the reading side). This makes the completion commit
    mechanical and keeps the written numbers identical to the ones the gate prints.
    """
    if not os.path.exists(args.pin):
        sys.stderr.write("INPUT GAP: no resume pin at %s (the writer preserves "
                         "owner_window/queue_order/resume_rule from it)\n" % args.pin)
        return 1
    pin = json.load(open(args.pin, encoding="utf-8"))
    queue = pin.get("queue_order") or []
    arms = pin.get("arms") or {}
    if not queue:
        sys.stderr.write("INPUT GAP: the resume pin names no queue_order\n")
        return 1
    out_arms, in_flight = {}, []
    for name in queue:
        rec = derive_arm(name, arms.get(name) or {}, args.repo, args.ws)
        if not rec:
            continue
        out_arms[name] = rec
        # The hazard this guard exists for is pinning bytes WHILE the runner appends to them:
        # a partially grown leg. A leg that has not started (0 stored, the full resume set
        # left) and a leg that finished (0 remaining) are both stable boundaries and write
        # without the flag - refusing them would block the two pins the queue actually needs.
        if rec["expected_remaining"] and rec["expected_ok"]:
            in_flight.append(name)
    if FINDINGS:
        for f in FINDINGS:
            sys.stderr.write("FINDING: %s\n" % f)
        sys.stderr.write("PIN WRITER: NO-GO - corrupt arm bytes are never pinned, and the "
                         "existing pin file was left byte-identical\n")
        return 3
    if GAPS:
        for g in GAPS:
            sys.stderr.write("INPUT GAP: %s\n" % g)
        return 1
    if in_flight and not args.allow_in_flight:
        sys.stderr.write(
            "PIN WRITER: REFUSED - a leg is still in flight (%s), so the pin would freeze a "
            "moment that the runner is about to move. Pass --allow-in-flight only when the "
            "leg was stopped for a reason and this partial IS the resume identity.\n"
            % ", ".join(in_flight))
        return 3
    new = {
        "schema": pin.get("schema") or "grok-resume-pin-v1",
        "as_of": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M CET"),
        "written_by": "scripts/pub_grok_resume_check.py --write-pin (read from stored bytes)",
        "owner_window": pin.get("owner_window"),
        "queue_order": queue,
        "resume_rule": pin.get("resume_rule"),
        "arms": out_arms,
    }
    text = json.dumps(new, indent=2, ensure_ascii=False) + "\n"
    tmp = args.pin + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, args.pin)
    total = sum(a["expected_remaining"] for a in out_arms.values())
    print("PIN WRITTEN: %s | %d arms | %d ids still unasked | as_of %s"
          % (args.pin, len(out_arms), total, new["as_of"]))
    if in_flight:
        print("note: in-flight sets pinned as a floor (--allow-in-flight): %s"
              % ", ".join(in_flight))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="pub_grok_resume_check.py", add_help=True)
    ap.add_argument("--pin", default=os.path.join(ROOT, "benchmarks", "public", "GROK-RESUME-PIN.json"))
    ap.add_argument("--ws", default=os.path.join(os.path.expanduser("~"), "pub-bench"))
    ap.add_argument("--repo", default=ROOT)
    ap.add_argument("--as-of", default=None,
                    help="YYYY-MM-DD the owner-window decision is taken from (default: today). "
                         "Fixed so the contract test can exercise both window states and a "
                         "later run can be reproduced.")
    ap.add_argument("--write-pin", action="store_true",
                    help="regenerate the pin at --pin from the STORED BYTES instead of checking "
                         "it (zero model/cloud calls). The gate's own 'regenerate the pin at "
                         "window end' instruction, made mechanical: numbers are read, never "
                         "typed. Refuses on corrupt arm bytes and, without --allow-in-flight, "
                         "on a leg that is still running.")
    ap.add_argument("--allow-in-flight", action="store_true",
                    help="with --write-pin: pin a partial leg on purpose (the leg was stopped "
                         "and this partial IS the resume identity).")
    args = ap.parse_args()

    override = os.environ.get("PUB_MANIFEST_OVERRIDE")
    if override:
        pbs.MANIFEST_PATH = override
    if args.write_pin:
        return write_pin(args)
    if not os.path.exists(args.pin):
        sys.stderr.write("INPUT GAP: no resume pin at %s\n" % args.pin)
        return 1
    pin = json.load(open(args.pin, encoding="utf-8"))
    queue = pin.get("queue_order") or []
    arms = pin.get("arms") or {}
    if not queue:
        sys.stderr.write("INPUT GAP: the resume pin names no queue_order\n")
        return 1
    for name in queue:
        if name not in arms:
            GAPS.append("%s: listed in queue_order but the pin has no arm record" % name)

    ow = pin.get("owner_window") or {}
    until = str(ow.get("suspended_until") or "")
    cancelled = str(ow.get("cancelled_on") or "")
    as_of = args.as_of or __import__("datetime").date.today().isoformat()

    # The window mode is a string comparison, so BOTH operands must be the ISO
    # YYYY-MM-DD form. Measured 2026-11-11: a compact `--as-of 20261111` compared
    # byte-wise as "20261111" >= "2026-11-12" == True (digit > hyphen at position 4),
    # so any compact date silently reported the suspension window OPEN and disabled
    # the pinned-snapshot guard that exists to catch launches inside the window.
    # Python >= 3.11 date.fromisoformat also accepts the compact form, so the guard
    # is a strict regex plus a calendar check, not fromisoformat alone.
    def _iso_dashed(s):
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(s)):
            return False
        try:
            __import__("datetime").date.fromisoformat(str(s))
            return True
        except ValueError:
            return False

    if not _iso_dashed(as_of):
        sys.stderr.write(
            "INPUT GAP: --as-of %r is not YYYY-MM-DD. The window mode is a string "
            "compare and a non-ISO value decides it silently wrong (20261111-style "
            "compact dates always read OPEN), so the gate refuses rather than "
            "guessing.\n" % (args.as_of,))
        return 1
    if until and not _iso_dashed(until):
        GAPS.append("owner_window.suspended_until %r is not YYYY-MM-DD - the window "
                    "mode cannot be decided by string compare" % until)
    if cancelled and not _iso_dashed(cancelled):
        GAPS.append("owner_window.cancelled_on %r is not YYYY-MM-DD - the cancellation date "
                    "decides the window mode by string compare, so the gate refuses rather "
                    "than guessing" % cancelled)
    if cancelled and _iso_dashed(cancelled) and as_of >= cancelled:
        # Cancelled window state (owner decision 2026-11-12 06:40 CET, delivered on Telegram:
        # stop touching Grok, very few limits left, Grok cancelled): the window has no end, so
        # the pin is an exact snapshot FOREVER. Any growth past it is a finding, which is the
        # mechanical form of "no Grok arm until the owner re-arms this line".
        window_open = False
        mode_note = ("cancelled by owner decision on %s with no resume date - CLOSED "
                     "indefinitely, no Grok call is legal at all" % cancelled)
    elif not until:
        if cancelled and _iso_dashed(cancelled):
            # The run date precedes the cancellation and the old window end was dropped from
            # the pin: fail closed rather than handing out a green light.
            window_open = False
            mode_note = ("the run date %s precedes the owner cancellation on %s and the pin "
                         "names no window end - fail closed" % (as_of, cancelled))
        else:
            GAPS.append("the pin names no owner_window.suspended_until and no cancelled_on - "
                        "the window cannot be decided")
            window_open = False
            mode_note = "undecided"
    else:
        window_open = as_of >= until
        mode_note = "window closes %s" % until
    print("grok resume gate | pin %s | as of %s | window is %s today (%s) | %s"
          % (os.path.relpath(args.pin, ROOT), pin.get("as_of"),
             "OPEN" if window_open else "CLOSED", as_of, mode_note))
    live_remaining = 0
    for name in queue:
        if name in arms:
            live_remaining += check_arm(name, arms[name], args.repo, args.ws, window_open) or 0

    total = sum(int(arms[n].get("expected_remaining", 0)) for n in queue if n in arms)
    print("pinned resume queue total: %d calls, order %s" % (total, " -> ".join(queue)))
    print("live resume total read from the stored bytes: %d ids still unasked"
          % live_remaining)
    for p in PROGRESS:
        print("progress: %s" % p)
    if GAPS:
        for g in GAPS:
            sys.stderr.write("INPUT GAP: %s\n" % g)
        print("checks: %d | RESUME GATE: INPUT GAP - never a green light" % CHECKS)
        return 1
    if FINDINGS:
        for f in FINDINGS:
            sys.stderr.write("FINDING: %s\n" % f)
        print("checks: %d | RESUME GATE: NO-GO - do not spend quota" % CHECKS)
        return 3
    print("checks: %d | RESUME GATE: READY - every stored partial matches its pinned "
          "identity and its resume set is exact" % CHECKS)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
