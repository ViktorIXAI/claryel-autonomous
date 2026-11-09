#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish one BARE public-line arm (local or cloud runner output) into benchmarks/public/arms/.

Why this exists: `publish_pub_arms.py` publishes contour arms (results + ledger + answers + run
record). A bare arm has no ledger, and for IFEval the digest percent cannot be re-checked by an
outsider at all without the stored answer bytes plus the scorer's verdict rows, because the verdict
comes from the vendored upstream checker rather than from a number/letter match. Same privacy
contract as the contour publisher: the SAME scrub function is imported from it (one sanitizer, not
two), answer text is never edited, and the script refuses to publish a partial arm.

Usage: publish_pub_bare_arm.py <answers.jsonl> <arm-label> [--verdicts FILE] [--min-rows N]

It prints the exact index lines for benchmarks/public/arms/README.md; the README is then updated
from that output, never retyped.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_DIR = os.path.join(REPO, "benchmarks", "public", "arms")

_spec = importlib.util.spec_from_file_location("publish_pub_arms",
                                               os.path.join(HERE, "publish_pub_arms.py"))
if _spec is None or _spec.loader is None:
    sys.exit("cannot load the shared sanitizer (scripts/publish_pub_arms.py)")
_ppa = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ppa)
scrub = _ppa.scrub


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def publish(src, dst):
    """Scrub line by line; report what was masked. Refuses a file with blank answer rows."""
    masked, kept, blank = {}, 0, 0
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as out:
        for line in open(src, encoding="utf-8"):
            if not line.strip():
                continue
            clean, hits = scrub(line.rstrip("\n"))
            for h in hits:
                masked[h] = masked.get(h, 0) + 1
            out.write(clean + "\n")
            kept += 1
    return kept, masked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers")
    ap.add_argument("label")
    ap.add_argument("--verdicts")
    ap.add_argument("--min-rows", type=int, default=1)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.answers, encoding="utf-8") if l.strip()]
    ids = [r.get("id") for r in rows]
    if len(rows) < a.min_rows:
        sys.exit("REFUSING: %d rows, expected at least %d (partial arm publishes nothing)"
                 % (len(rows), a.min_rows))
    if len(set(ids)) != len(ids):
        sys.exit("REFUSING: duplicate task ids in the arm file (%d rows, %d ids)"
                 % (len(rows), len(set(ids))))
    blank = sum(1 for r in rows if not (r.get("answer") or "").strip())
    if blank > 0.05 * len(rows):
        sys.exit("REFUSING: %d/%d rows have an empty answer" % (blank, len(rows)))
    bad = sum(1 for r in rows if r.get("finish") not in (None, "ok"))
    if bad > 0.05 * len(rows):
        sys.exit("REFUSING: %d/%d rows did not finish ok" % (bad, len(rows)))

    dst = os.path.join(OUT_DIR, "%s-answers.jsonl" % a.label)
    kept, masked = publish(a.answers, dst)
    print("wrote %s lines=%d sha16=%s masked=%s" % (dst, kept, sha16(dst), masked or "nothing"))
    outs = [(dst, kept)]

    if a.verdicts:
        vdst = os.path.join(OUT_DIR, "%s-verdicts.jsonl" % a.label)
        vkept, vmasked = publish(a.verdicts, vdst)
        same = (open(vdst, "rb").read() == open(a.verdicts, "rb").read())
        print("wrote %s lines=%d sha16=%s masked=%s bytes_identical_to_scorer_output=%s"
              % (vdst, vkept, sha16(vdst), vmasked or "nothing", same))
        outs.append((vdst, vkept))
        sc = a.verdicts.rsplit(".", 1)[0] + ".sha16"
        if os.path.exists(sc):
            print("scorer's own verdict sidecar (sha1/16 over the same bytes): %s"
                  % open(sc).read().strip())

    print("\nREADME index lines (paste verbatim):")
    for p, n in outs:
        print("| %s | %d | `%s` |" % (os.path.basename(p), n, sha16(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
