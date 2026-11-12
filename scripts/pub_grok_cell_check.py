#!/usr/bin/env python3
"""Checker for the Grok availability wording in the public-line result tables.

Owner rule (decision 2026-11-09, Grok quota suspension): in every table, the Grok cell of an
incomplete set must carry the in-force suspension sentence verbatim — never "transport failure",
never a blank that reads as a zero. Grok rows already published from completed legs stay
published and comparable.

The sentence is NOT hardcoded here: it is read from `owner_window.cell_phrase` in
`benchmarks/public/GROK-RESUME-PIN.json`, the same record `pub_grok_resume_check.py` decides its
window from. One owner decision therefore moves one file, and the checker cannot silently keep an
expired sentence. Superseded sentences are listed in the same record (`superseded_cell_phrases`)
and a percent-less grok row carrying one is a finding.

Why that indirection exists (measured 2026-11-12, tick 73): the owner cancelled Grok at 06:40 CET
on the very day the resume window opened (stop touching Grok, very few limits left, Grok
cancelled). Four table cells — BFCL, IFEval, LiveCodeBench twice — still read "suspended by owner
quota, resumes 2026-11-12", which after that decision is a false availability claim: it promises a
resume that was cancelled the same morning.

What is enforced here, mechanically, over the tracked result documents
(`benchmarks/public/*-RESULT.md` — the scope is documented, the digest table and the audit-frozen
README table are not scanned by this checker):

  every markdown table row whose FIRST cell names grok must
    (a) publish a percent for that arm ("N/M = X.X %"), which means the arm completed, OR
    (b) carry the in-force suspension sentence verbatim,
  and a grok row that carries no percent must not carry a stale availability marker
  ("in flight", "not started", "pending", "queued", "lands", "soon", "serialized") and must not
  carry a superseded window's sentence.

Class this was written for (measured 2026-11-10, tick 11): three result tables — GPQA-Diamond,
HumanEval, MMLU-Pro — still described their grok arm as "in flight (12/198 at publish time)" or
"not started yet" a day after the legs had been stopped by the owner quota window (139/198 and
120/164 stored, both resumable by id). Prose elsewhere in the same documents carried the correct
status, so a reader of the table alone got a stale availability claim. A table cell is the part
people quote, so the rule now has a checker with tamper controls
(`harness/pub_grok_cell_test.py`, CI-enrolled by the `harness/*test.py` glob).

No model call, no arm, no published percent is touched: this is a document-state checker.

Usage:
    python3 scripts/pub_grok_cell_check.py [--check] [--pin PIN] [PATH ...]
exits 0 with no finding, 3 with findings, 2 if a scanned document has no grok row at all in its
arm table (a set silently dropping its fourth arm is the same failure class as a stale cell) or if
the owner-window record names no in-force cell phrase — an input gap is never a green light.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCS = sorted((ROOT / "benchmarks" / "public").glob("*-RESULT.md"))
DEFAULT_PIN = ROOT / "benchmarks" / "public" / "GROK-RESUME-PIN.json"

PERCENT = re.compile(r"\d+\s*/\s*\d+\s*=\s*\*{0,2}\d+(?:\.\d+)?\s*%")
STALE_MARKERS = (
    "in flight", "not started", "pending", "queued", "lands", "soon", "serialized",
)

# The in-force sentence and the superseded ones, refreshed by load_window(). No literal is kept
# here on purpose: a remembered phrase in the checker is exactly the tick-11 failure class.
SUSPENSION = None
SUPERSEDED: tuple = ()


def load_window(pin_path: Path = DEFAULT_PIN):
    """Read the in-force cell sentence and the superseded ones from the owner-window record.

    Returns (in_force, superseded) and raises ValueError on an input gap (no pin, no vocabulary):
    the checker never invents wording.
    """
    global SUSPENSION, SUPERSEDED
    if not pin_path.exists():
        raise ValueError("no owner-window record at %s" % pin_path)
    ow = (json.loads(pin_path.read_text(encoding="utf-8")) or {}).get("owner_window") or {}
    phrase = str(ow.get("cell_phrase") or "").strip()
    if not phrase:
        raise ValueError("owner_window.cell_phrase is empty in %s - the checker would have to "
                         "invent the wording" % pin_path)
    superseded = tuple(str(s or "").strip() for s in (ow.get("superseded_cell_phrases") or [])
                       if str(s or "").strip())
    SUSPENSION, SUPERSEDED = phrase, superseded
    return phrase, superseded


def grok_rows(text: str):
    """Yield (line_no, cells) for markdown table rows whose first cell names grok."""
    for n, line in enumerate(text.splitlines(), 1):
        s = line.strip()
        if not s.startswith("|"):
            continue
        cells = [c.strip() for c in s.strip("|").split("|")]
        if not cells:
            continue
        first = cells[0].strip("*` ").lower()
        if first.startswith("grok"):
            yield n, cells


def check_doc(path: Path, in_force=None, superseded=None):
    """Return a list of 'file:line message' findings for one result document."""
    if in_force is None:
        in_force = SUSPENSION if SUSPENSION is not None else load_window()[0]
    if superseded is None:
        superseded = SUPERSEDED
    findings = []
    text = path.read_text(encoding="utf-8")
    rows = list(grok_rows(text))
    if not rows:
        return ["%s: no grok arm row found in any table" % path.name]
    for n, cells in rows:
        body = " | ".join(cells[1:])
        has_percent = bool(PERCENT.search(body))
        if has_percent:
            continue                      # a completed grok arm: published and comparable
        if in_force not in body:
            findings.append(
                "%s:%d grok arm row with no percent and not the in-force suspension sentence "
                "%r: %s" % (path.name, n, in_force, body[:160]))
        for old in superseded:
            if old and old != in_force and old in body:
                findings.append(
                    "%s:%d grok arm row carries a SUPERSEDED owner-window sentence %r - the "
                    "owner decision moved, the cell did not" % (path.name, n, old))
        for marker in STALE_MARKERS:
            if marker in body.lower():
                findings.append(
                    "%s:%d stale grok availability marker %r in a row that publishes no percent"
                    % (path.name, n, marker))
    return findings


def main(argv):
    args = [a for a in argv[1:] if a != "--check"]
    pin = DEFAULT_PIN
    if "--pin" in args:
        i = args.index("--pin")
        pin = Path(args[i + 1])
        args = args[:i] + args[i + 2:]
    docs = [Path(a) for a in args] or list(DEFAULT_DOCS)
    try:
        in_force, superseded = load_window(pin)
    except ValueError as exc:
        print("INPUT GAP: %s" % exc)
        return 2
    print("grok cell rule: in-force sentence %r | %d superseded sentence(s) rejected"
          % (in_force, len(superseded)))
    findings = []
    for d in docs:
        findings += check_doc(d, in_force, superseded)
    print("grok cell rule: %d document(s) scanned, %d finding(s)" % (len(docs), len(findings)))
    for f in findings:
        print("  FINDING:", f)
    if findings:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
