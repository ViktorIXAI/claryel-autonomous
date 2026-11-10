#!/usr/bin/env python3
"""Contract test for `scripts/pub_superseded_cell_check.py` (added 2026-11-10).

What it pins:

  1. the tracked tree passes the superseded-cell rule (0 findings);
  2. the rule is not vacuous — four independent tamper controls each redden it:
       a. the word "superseded" stripped from a document's arms table,
       b. an arms-table family row deleted,
       c. the in-force (corrected) percent removed from a marked row,
       d. the arms table header removed so the auditor cannot find the table;
  3. every bench with an in-force digest percent has a result document in the
     checker's scope, so a new public set cannot silently escape the audit;
  4. every supersession token the checker recognises is actually exercised by a
     digest row, so the token list cannot rot into dead code.

The pre-fix census of the tracked bytes (measured before this commit, on the
documents as they stood after 2026-11-09) was 9 findings across 4 documents.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import pub_superseded_cell_check as C  # noqa: E402

FAILED = []
CHECKS = 0


def ck(cond: bool, msg: str) -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(msg)


def tmp_copy() -> str:
    dst = tempfile.mkdtemp(prefix="pubcells-")
    shutil.copytree(os.path.join(ROOT, "benchmarks", "public"),
                    os.path.join(dst, "public"))
    return dst


def sub(base: str, name: str) -> str:
    return os.path.join(base, "public", name)


def rewrite(path: str, old: str, new: str, count: int = 1) -> None:
    text = open(path, encoding="utf-8").read()
    assert old in text, "tamper target missing in %s" % path
    open(path, "w", encoding="utf-8").write(text.replace(old, new, count))


def main() -> int:
    # 1. tracked tree is clean
    findings = C.check()
    ck(findings == [], "tracked tree must pass, got %d finding(s): %s"
       % (len(findings), findings[:4]))

    digest_rows = C.digest_rows()
    benches = {r["bench"] for r in digest_rows if r["bench"] != "simplebench"}

    # 2. every in-force bench is inside the checker's document scope
    for b in sorted(benches):
        ck(b in C.DOC_FOR_BENCH, "bench %s has digest percents but no audited document" % b)
        if b in C.DOC_FOR_BENCH:
            ck(os.path.exists(os.path.join(ROOT, "benchmarks", "public", C.DOC_FOR_BENCH[b])),
               "missing result document for %s" % b)

    # 3. every supersession token is exercised by at least one digest row
    for label, tok in C.SUPERSEDED_TOKENS.items():
        hits = [r for r in digest_rows if tok in r["call"]]
        ck(bool(hits), "supersession token %s (%s) matches no digest row (dead rule)"
           % (label, tok))

    # 4a. strip the marker word from each fixed document: each must go red
    for doc in ("HUMANEVAL-RESULT.md", "GPQA-RESULT.md", "ARC-CHALLENGE-RESULT.md",
                "ARC-EASY-RESULT.md", "LIVECODEBENCH-RESULT.md"):
        base = tmp_copy()
        try:
            p = sub(base, doc)
            text = open(p, encoding="utf-8").read()
            i = text.index("| arm |")
            j = text.index("\n\n", i)
            body = text[i:j].replace("superseded", "as-published")
            open(p, "w", encoding="utf-8").write(text[:i] + body + text[j:])
            f = C.check(os.path.join(base, "public", "PUB-DIGEST.md"),
                        os.path.join(base, "public"))
            ck(any(doc in x for x in f), "tamper (marker stripped) not caught in %s" % doc)
        finally:
            shutil.rmtree(base)

    # 4b. delete a family row: the table loses its only contour row -> finding
    base = tmp_copy()
    try:
        p = sub(base, "ARC-EASY-RESULT.md")
        text = open(p, encoding="utf-8").read()
        line = [l for l in text.splitlines()
                if l.startswith("| contour-0.0.2.56, matched shape")][0]
        rewrite(p, line + "\n", "")
        f = C.check(os.path.join(base, "public", "PUB-DIGEST.md"),
                    os.path.join(base, "public"))
        ck(any("no contour row at all" in x for x in f),
           "tamper (contour row deleted) not caught: %s" % f[:3])
    finally:
        shutil.rmtree(base)

    # 4c. drop the corrected percent from every marked row -> in-force cell missing
    base = tmp_copy()
    try:
        p = sub(base, "GPQA-RESULT.md")
        lines = open(p, encoding="utf-8").read().splitlines(True)
        for i, l in enumerate(lines):
            if l.startswith("| contour-0.0.2.56"):
                lines[i] = l.replace("139/198 = 70.2 %", "the matched-shape arm")
        open(p, "w", encoding="utf-8").write("".join(lines))
        f = C.check(os.path.join(base, "public", "PUB-DIGEST.md"),
                    os.path.join(base, "public"))
        ck(any("never prints the in-force percent 139/198" in x for x in f),
           "tamper (corrected percent removed) not caught: %s" % f[:3])
    finally:
        shutil.rmtree(base)

    # 4d. a document with no auditable arms table is reported, not skipped
    base = tmp_copy()
    try:
        p = sub(base, "LIVECODEBENCH-RESULT.md")
        text = open(p, encoding="utf-8").read()
        rewrite(p, "| arm | tasks scored | tasks sha16 | call | strict |",
                "| bench | tasks scored | tasks sha16 | call | strict |")
        f = C.check(os.path.join(base, "public", "PUB-DIGEST.md"),
                    os.path.join(base, "public"))
        ck(any("no arms table found" in x for x in f),
           "tamper (arms table header renamed) not caught: %s" % f[:3])
    finally:
        shutil.rmtree(base)

    # 5. a completed Grok row and a suspended Grok row both stay legal here: the
    #    superseded rule must not fire on the availability cells
    base = tmp_copy()
    try:
        p = sub(base, "MMLU-PRO-RESULT.md")
        text = open(p, encoding="utf-8").read()
        rewrite(p, "| grok | `grok-4.7`, hermes one-shot, toolsets off | **suspended by owner quota, "
                    "resumes 2026-11-12**", "| grok-4.7 | `grok-4.7` | 500/500 | 470/500 = 94.0 % |")
        f = C.check(os.path.join(base, "public", "PUB-DIGEST.md"),
                    os.path.join(base, "public"))
        ck(f == [], "a completed Grok row must not create a superseded finding: %s" % f[:3])
    finally:
        shutil.rmtree(base)

    print("pub_superseded_cell_test: %d checks, %d failed" % (CHECKS, len(FAILED)))
    for m in FAILED:
        print("  FAIL:", m)
    return 1 if FAILED else 0


if __name__ == "__main__":
    sys.exit(main())
