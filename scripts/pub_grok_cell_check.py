#!/usr/bin/env python3
"""Checker for the Grok availability wording in the public-line result tables.

Owner rule (decision 2026-11-09, Grok quota suspension): in every table, the Grok cell of an
incomplete set must read "suspended by owner quota, resumes 2026-11-12" — never "transport
failure", never a blank that reads as a zero. Grok rows already published from completed legs stay
published and comparable.

What is enforced here, mechanically, over the tracked result documents
(`benchmarks/public/*-RESULT.md` — the scope is documented, the digest table and the audit-frozen
README table are not scanned by this checker):

  every markdown table row whose FIRST cell names grok must
    (a) publish a percent for that arm ("N/M = X.X %"), which means the arm completed, OR
    (b) carry the suspension sentence verbatim,
  and a grok row that carries no percent must not carry a stale availability marker
  ("in flight", "not started", "pending", "queued", "lands", "soon", "serialized").

Class this was written for (measured 2026-11-10, tick 11): three result tables — GPQA-Diamond,
HumanEval, MMLU-Pro — still described their grok arm as "in flight (12/198 at publish time)" or
"not started yet" a day after the legs had been stopped by the owner quota window (139/198 and
120/164 stored, both resumable by id). Prose elsewhere in the same documents carried the correct
status, so a reader of the table alone got a stale availability claim. A table cell is the part
people quote, so the rule now has a checker with tamper controls
(`harness/pub_grok_cell_test.py`, CI-enrolled by the `harness/*test.py` glob).

No model call, no arm, no published percent is touched: this is a document-state checker.

Usage:
    python3 scripts/pub_grok_cell_check.py [--check] [PATH ...]
exits 0 with no finding, 3 with findings, 2 if a scanned document has no grok row at all in its
arm table (a set silently dropping its fourth arm is the same failure class as a stale cell).
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCS = sorted((ROOT / "benchmarks" / "public").glob("*-RESULT.md"))

SUSPENSION = "suspended by owner quota, resumes 2026-11-12"
PERCENT = re.compile(r"\d+\s*/\s*\d+\s*=\s*\*{0,2}\d+(?:\.\d+)?\s*%")
STALE_MARKERS = (
    "in flight", "not started", "pending", "queued", "lands", "soon", "serialized",
)


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


def check_doc(path: Path):
    """Return a list of 'file:line message' findings for one result document."""
    findings = []
    text = path.read_text(encoding="utf-8")
    rows = list(grok_rows(text))
    if not rows:
        return ["%s: no grok arm row found in any table" % path.name]
    for n, cells in rows:
        body = " | ".join(cells[1:])
        has_percent = bool(PERCENT.search(body))
        has_suspension = SUSPENSION in body
        if has_percent:
            continue                      # a completed grok arm: published and comparable
        if not has_suspension:
            findings.append(
                "%s:%d grok arm row with no percent and no suspension sentence: %s"
                % (path.name, n, body[:160]))
        for marker in STALE_MARKERS:
            if marker in body.lower():
                findings.append(
                    "%s:%d stale grok availability marker %r in a row that publishes no percent"
                    % (path.name, n, marker))
    return findings


def main(argv):
    args = [a for a in argv[1:] if a != "--check"]
    docs = [Path(a) for a in args] or list(DEFAULT_DOCS)
    findings = []
    for d in docs:
        findings += check_doc(d)
    print("grok cell rule: %d document(s) scanned, %d finding(s)" % (len(docs), len(findings)))
    for f in findings:
        print("  FINDING:", f)
    if findings:
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
