#!/usr/bin/env python3
"""Publication-completeness gate for SUPERSEDED percent cells.

Why this exists (2026-11-10 line audit): the digest table and the dated prose
carry the supersession pointers, but the per-arm table at the top of every
`<BENCH>-RESULT.md` is the block people actually quote, and its cells froze at
first publication. Three defect shapes were measured on the tracked bytes:

  * an escalation-shape contour percent printed as the set's only contour cell
    (arc-challenge 283/300, gpqa-diamond 91/198, arc-easy: no contour row at all);
  * a `pytest-v1` / `lcb-exec-v1` percent printed as the current verdict after the
    same stored bytes were re-scored under a corrected contract;
  * the corrected (in-force) fraction never appearing in that table, so a reader
    of the table cannot see what replaced the number they are quoting.

Rule, derived from the digest table itself (no hand-maintained list):

  1. a digest row is SUPERSEDED when its `call` cell carries one of the contract
     or shape tokens the digest header declares superseded (escalation shape,
     `pytest-v1`, `lcb-exec-v1`) AND a sibling row exists for the same
     bench+model under a non-superseded label (that sibling is the
     replacement). Arm identity is bench+model, NOT bench+model+tasks: a
     corrected contract can legitimately change the denominator
     (`lcb-exec-v1` 112 of 175 -> `lcb-exec-v2` 175 of 175), and requiring the
     tasks cell to match would hide exactly the supersession this rule is for;
  2. in the arms table of the matching result document, every row of the same arm
     family carrying a superseded fraction must say "superseded" in the row
     (the row may carry no percent at all and then no marker is needed);
  3. the replacement fraction must appear somewhere in that arms table in a row of
     the same arm family (a row that only mentions the fraction in prose, e.g. a
     Grok stored-row count, does not discharge the requirement).

The checker never edits a byte: it reports findings and exits 3. Superseded rows
keep their published numbers; what must move is the LABEL in the quoted cell.
"""
from __future__ import annotations

import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUB = os.path.join(ROOT, "benchmarks", "public")
DIGEST = os.path.join(PUB, "PUB-DIGEST.md")

# tokens the digest header itself declares superseded (2026-11-08 shape rule,
# 2026-11-09 pytest-v2 and lcb-exec-v2 contract releases)
SUPERSEDED_TOKENS = {
    "request-shape escalation": "ladder rungs 512,1200, enable_thinking off",
    "checker pytest-v1": "checker pytest-v1",
    "checker lcb-exec-v1": "checker lcb-exec-v1",
}

DOC_FOR_BENCH = {
    "gsm8k": "GSM8K-RESULT.md",
    "arc-easy": "ARC-EASY-RESULT.md",
    "arc-challenge": "ARC-CHALLENGE-RESULT.md",
    "gpqa-diamond": "GPQA-RESULT.md",
    "humaneval": "HUMANEVAL-RESULT.md",
    "mmlu-pro": "MMLU-PRO-RESULT.md",
    "ifeval": "IFEVAL-RESULT.md",
    "livecodebench": "LIVECODEBENCH-RESULT.md",
    "bfcl": "BFCL-RESULT.md",
}

FRAC_RE = re.compile(r"(\d+)\s*/\s*(\d+)")


def rows_of(path: str) -> list[list[str]]:
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        out.append(cells)
    return out


def digest_rows(path: str = DIGEST) -> list[dict]:
    rows = []
    for cells in rows_of(path):
        if len(cells) < 6 or cells[0] == "bench":
            continue
        bench, model, tasks, _sha, call, strict = cells[:6]
        m = FRAC_RE.search(strict)
        if not m:
            continue
        tok = next((k for k, v in SUPERSEDED_TOKENS.items() if v in call), None)
        rows.append({
            "bench": bench,
            "model": model,
            "tasks": tasks,
            "call": call,
            "frac": f"{m.group(1)}/{m.group(2)}",
            "superseded": tok,
        })
    return rows


def classify(cell: str) -> str:
    c = cell.lower()
    if "contour" in c:
        return "contour"
    if "grok" in c:
        return "grok"
    if "codex" in c or "gpt-" in c:
        return "codex"
    return "bare"


def arms_table(doc_path: str) -> tuple[list[list[str]], int] | None:
    """First markdown table whose header starts with `arm` and names `strict`."""
    lines = open(doc_path, encoding="utf-8").read().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("|") and re.match(r"^\|\s*arm\s*\|", line, re.I) \
                and "strict" in line.lower():
            table = [line]
            j = i + 1
            while j < len(lines) and lines[j].startswith("|"):
                table.append(lines[j])
                j += 1
            return rows_of_from_lines(table), i + 1
        i += 1
    return None


def rows_of_from_lines(lines: list[str]) -> list[list[str]]:
    out = []
    for line in lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue
        out.append(cells)
    return out


def check(digest_path: str = DIGEST, pub_dir: str = PUB) -> list[str]:
    drows = digest_rows(digest_path)
    findings: list[str] = []

    superseded: dict[str, list[dict]] = {}
    for r in drows:
        if not r["superseded"]:
            continue
        sib = [s for s in drows
               if s["bench"] == r["bench"] and s["model"] == r["model"]
               and not s["superseded"] and s["frac"] != r["frac"]]
        if not sib:
            # no corrected row published for this arm: nothing to point at
            continue
        r2 = dict(r)
        r2["replacement"] = sib[0]["frac"]
        superseded.setdefault(r["bench"], []).append(r2)

    for bench, sups in superseded.items():
        doc = DOC_FOR_BENCH.get(bench)
        if doc is None:
            continue
        path = os.path.join(pub_dir, doc)
        if not os.path.exists(path):
            findings.append(f"{doc}: no result document for in-force bench {bench}")
            continue
        got = arms_table(path)
        if not got:
            findings.append(f"{doc}: no arms table found (cannot audit percent cells)")
            continue
        table, line_no = got
        body = [r for r in table if r and r[0].lower() != "arm"]

        for s in sups:
            fam = classify(s["model"])
            fam_rows = [r for r in body if classify(r[0]) == fam]
            hits = [r for r in fam_rows
                    if any(f"{a}/{b}" == s["frac"] for a, b in FRAC_RE.findall(" ".join(r)))]
            if not fam_rows:
                findings.append(
                    f"{doc}: line ~{line_no}: arms table has no {fam} row at all, so the "
                    f"superseded {s['superseded']} percent {s['frac']} and the in-force "
                    f"{s['replacement']} are both unquotable from it")
                continue
            for r in hits:
                if "superseded" not in " ".join(r).lower():
                    findings.append(
                        f"{doc}: line ~{line_no}: {fam} row {s['frac']} "
                        f"({s['superseded']}) carries no 'superseded' marker")
            if not any(s["replacement"] in " ".join(r) for r in fam_rows):
                findings.append(
                    f"{doc}: arms table never prints the in-force percent "
                    f"{s['replacement']} for the {fam} arm superseded by "
                    f"{s['superseded']}")
    return findings


def main() -> int:
    f = check()
    print(f"superseded-cell rule: {len(DOC_FOR_BENCH)} document(s) scanned, "
          f"{len(f)} finding(s)")
    for x in f:
        print("  FINDING:", x)
    return 3 if f else 0


if __name__ == "__main__":
    sys.exit(main())
