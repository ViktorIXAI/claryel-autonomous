#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_derived_percent_check.py` (added 2026-11-10).

The digest table is machine-checked against shipped bytes; this pins the SECOND
class of quotable percents — slices, category/difficulty breakdowns, truncation
censuses and paired-join rates that no digest row carries.

What it pins:

  1. the tracked tree passes: every registry entry recomputes from the shipped
     artifacts and every percent quoted in a result document is covered by a
     digest row, a registry entry, or an exclusion that states a reason;
  2. the rule is not vacuous — seven tamper controls each redden it:
       a. a declared count moved by one cell,
       b. the quoted fraction deleted from its document,
       c. a registry entry deleted, leaving its citation uncovered,
       d. one shipped verdict row flipped in a sidecar,
       e. a brand-new unexplained percent inserted into a document,
       f. a registry artifact deleted (structural fail-closed, exit 2),
       g. one REDRAW-CONTROL verdict flipped inside the first-arm failure universe,
          which moves only the `directional_sign` counts (the repair-family split);
  3. every derivation kind the checker implements is exercised by at least one
     entry, so a kind cannot rot into dead code;
  4. every exclusion record carries a reason, and the excluded class is exactly
     the stochastic `pub-ifeval` scorer class (documented +-1 checker-noise band),
     so an exclusion cannot become a dumping ground.

Run: python3 harness/pub_derived_percent_test.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PUB = os.path.join(ROOT, "benchmarks", "public")
CHECKER = os.path.join(ROOT, "scripts", "pub_derived_percent_check.py")
FAILS = []
CHECKS = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILS.append("%s %s" % (name, detail))
        print("FAIL %s %s" % (name, detail))
    else:
        print("ok   %s" % name)


def run(pub_dir):
    env = dict(os.environ, SAH_PUB_DIR=pub_dir)
    r = subprocess.run([sys.executable, CHECKER], capture_output=True, text=True, env=env)
    return r.returncode, r.stdout + r.stderr


def mirror_pub(dst: str, rel: str = "", depth: int = 2) -> None:
    """Symlink the public tree file by file (two levels deep) so a tamper control
    can replace a SINGLE file without copying 50 MB of pinned artifacts."""
    src_dir = os.path.join(PUB, rel)
    tgt_dir = os.path.join(dst, rel) if rel else dst
    if rel:
        os.makedirs(tgt_dir, exist_ok=True)
    for name in sorted(os.listdir(src_dir)):
        src = os.path.join(src_dir, name)
        dstp = os.path.join(tgt_dir, name)
        if os.path.isdir(src) and depth > 0:
            mirror_pub(dst, os.path.join(rel, name) if rel else name, depth - 1)
        else:
            os.symlink(src, dstp)


def replace_file(dst: str, name: str, text: str) -> None:
    """Swap one symlinked file for a real edited copy inside the mirror."""
    p = os.path.join(dst, name)
    if os.path.islink(p):
        os.unlink(p)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(text)


def main() -> int:
    if not os.path.exists(CHECKER):
        print("FAIL checker missing: %s" % CHECKER)
        return 1

    # 1. tracked tree must be clean
    rc, out = run(PUB)
    check("tracked tree passes", rc == 0 and "0 findings" in out, "rc=%d" % rc)
    check("recompute count reported", "DERIVED PERCENTS:" in out)

    reg = json.load(open(os.path.join(PUB, "DERIVED-PERCENTS.json"), encoding="utf-8"))
    entries = reg["entries"]

    # 3. every implemented kind is exercised
    kinds = {e["kind"] for e in entries}
    for k in ("subset", "category", "field_count", "join"):
        check("kind %s exercised by an entry" % k, k in kinds)
    join_modes = {e.get("mode") for e in entries if e["kind"] == "join"}
    for m in ("symmetric_flip", "flip_gain", "keep_best_union", "directional_sign"):
        check("join mode %s exercised" % m, m in join_modes)

    # 4. exclusions carry reasons and stay inside the stochastic-scorer class
    for a in reg["not_recomputable_in_ci"]:
        check("exclusion %s has a reason" % a["fraction"], len(a.get("reason", "")) > 20)
        check("exclusion %s names its bench" % a["fraction"], a.get("bench") == "ifeval")

    # 2a-f. tamper controls
    cases = []

    # a. one cell off in a declared count
    r1 = json.loads(json.dumps(reg))
    for e in r1["entries"]:
        if e["id"] == "gsm8k-bare-slice300":
            e["expect"] = "294/300 = 98.0 %"
    cases.append(("declared count moved by one cell", r1, None, "COUNT MISMATCH"))

    # b. quoted fraction deleted from its document
    cases.append(("quote deleted from the document", reg,
                  ("GSM8K-RESULT.md", "295/300"), "QUOTE GONE"))

    # c. registry entry deleted -> its citation is uncovered
    r2 = json.loads(json.dumps(reg))
    r2["entries"] = [e for e in r2["entries"] if e["id"] != "bfcl-cat-irrelevance"]
    cases.append(("registry entry deleted, citation uncovered", r2, None, "uncovered"))

    # e. a brand-new unexplained percent in a document
    cases.append(("new unexplained percent inserted", reg,
                  ("GSM8K-RESULT.md", None,
                   "\n| fabricated arm | 1201/1319 = 91.1 % |\n"), "is quoted but neither"))

    for name, payload, doc_edit, marker in cases:
        with tempfile.TemporaryDirectory() as td:
            mirror_pub(td)
            if payload is not reg:
                replace_file(td, "DERIVED-PERCENTS.json", json.dumps(payload, indent=2))
            if doc_edit and doc_edit[1]:
                src = open(os.path.join(PUB, doc_edit[0]), encoding="utf-8").read()
                replace_file(td, doc_edit[0], src.replace(doc_edit[1], "296/301"))
            elif doc_edit:
                src = open(os.path.join(PUB, doc_edit[0]), encoding="utf-8").read()
                replace_file(td, doc_edit[0], src + doc_edit[2])
            rc, out = run(td)
            check("tamper reddens it: %s" % name, rc != 0 and marker in out, "rc=%d" % rc)

    # d. one shipped verdict flipped
    with tempfile.TemporaryDirectory() as td:
        mirror_pub(td)
        src_p = os.path.join(PUB, "arms", "bfcl-basalt-verdicts.jsonl")
        p = os.path.join(td, "arms", "bfcl-basalt-verdicts.jsonl")
        os.unlink(p)  # drop the symlink, write an edited real copy in its place
        rows = [json.loads(l) for l in open(src_p, encoding="utf-8") if l.strip()]
        flipped = 0
        for r in rows:
            if r["ok"] and flipped < 1:
                r["ok"] = False
                flipped += 1
        if flipped != 1:
            FAILS.append("tamper (d) flipped nothing - the sidecar shape changed")
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        rc, out = run(td)
        check("tamper reddens it: shipped verdict row flipped", rc != 0 and "COUNT MISMATCH" in out,
              "rc=%d" % rc)

    # g. one redraw-control verdict flipped inside the first-arm failure universe:
    #    only the `directional_sign` counts can move, so this is the non-vacuity
    #    proof for the mode the repair-family census is built from.
    with tempfile.TemporaryDirectory() as td:
        mirror_pub(td)
        base_p = os.path.join(PUB, "arms", "bfcl-basalt-verdicts.jsonl")
        fails = {json.loads(l)["id"] for l in open(base_p, encoding="utf-8") if l.strip()
                 if not json.loads(l)["ok"]}
        src_p = os.path.join(PUB, "arms", "bfcl-contour-matched-verdicts.jsonl")
        p = os.path.join(td, "arms", "bfcl-contour-matched-verdicts.jsonl")
        os.unlink(p)
        rows = [json.loads(l) for l in open(src_p, encoding="utf-8") if l.strip()]
        flipped = 0
        for r in rows:
            if r["ok"] and r["id"] in fails and flipped < 1:
                r["ok"] = False
                flipped += 1
        if flipped != 1:
            FAILS.append("tamper (g) flipped nothing - the redraw-control sidecar shape changed")
        with open(p, "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
        rc, out = run(td)
        check("tamper reddens it: redraw-control verdict flipped (directional_sign)",
              rc != 0 and "COUNT MISMATCH" in out
              and "redraw-only" in out, "rc=%d" % rc)

    # f. registry artifact deleted -> structural fail-closed
    with tempfile.TemporaryDirectory() as td:
        mirror_pub(td)
        os.unlink(os.path.join(td, "arms", "bfcl-basalt-verdicts.jsonl"))
        rc, out = run(td)
        check("missing artifact fails closed (exit 2)", rc == 2 and "STRUCTURAL" in out, "rc=%d" % rc)

    print("\nCHECKS %d, FAILED %d" % (CHECKS, len(FAILS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    raise SystemExit(main())
