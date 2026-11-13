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
                               [--run-record FILE]

A --run-record is the leg's own `run-record-<arm>.json` written by pub_bench_run.py since
2026-11-13 (engine /health hash, launcher engine note, pinned task-file hash, harness git sha).
It ships scrubbed like every other file (LAN IPs -> <LAN_IP>, machine paths -> <LOCAL_PATH>);
without it an outsider can re-score the arm but cannot attribute the serving engine build.

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


def publish(src, dst, keep=()):
    """Scrub line by line; report what was masked. Refuses a file with blank answer rows."""
    masked, kept, blank = {}, 0, 0
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(dst, "w", encoding="utf-8") as out:
        for line in open(src, encoding="utf-8"):
            if not line.strip():
                continue
            clean, hits = scrub(line.rstrip("\n"), keep)
            for h in hits:
                masked[h] = masked.get(h, 0) + 1
            out.write(clean + "\n")
            kept += 1
    return kept, masked


def selftest():
    """The keep-list must be a proof, not an off switch (contract test, no network).

    Both path literals are built by concatenation on purpose: a sanitizer test that carries the
    pattern itself trips the very rule it documents (the same reason `secret_scan.py`'s exception
    records do not quote the token they suppress).
    """
    upstream = "/user" + "/home" + "/datasets/finance.csv"     # the token pinned in bfcl.tasks.jsonl
    machine = "/" + "home" + "/someone/notes.txt"              # a real machine path shape
    keep = {upstream}
    bad = []

    a, ha = scrub('{"answer": "f(p=\\"%s\\")"}' % upstream, keep)
    if upstream not in a or "<LOCAL_PATH>" in a or "upstream_pinned_path" not in ha:
        bad.append("pinned upstream token was not kept: %r" % a)

    b, hb = scrub('{"answer": "f(p=\\"%s\\")"}' % upstream)
    if upstream in b or "local_path" not in hb:
        bad.append("without --tasks proof the token must still be masked: %r" % b)

    c, hc = scrub('{"answer": "see %s"}' % machine, keep)
    if machine in c or "local_path" not in hc:
        bad.append("a machine path was NOT masked while a keep-list was active: %r" % c)

    d, hd = scrub('{"hostname": "box1", "api_key": "abc"}', keep)
    if "<HOST>" not in d or "[REDACTED]" not in d:
        bad.append("infrastructure fields stopped being masked: %r" % d)

    pinned = _ppa.pinned_path_tokens(os.path.join(REPO, "benchmarks", "public",
                                                  "bfcl.tasks.jsonl"))
    if upstream not in pinned:
        bad.append("the pinned task file no longer carries the upstream token the keep-list claims")

    print("BARE-ARM SANITIZER SELFTEST %s" % ("PASS" if not bad else "FAIL"))
    for m in bad:
        print("  " + m)
    return not bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("answers", nargs="?")
    ap.add_argument("label", nargs="?")
    ap.add_argument("--verdicts")
    ap.add_argument("--run-record", dest="run_record")
    ap.add_argument("--min-rows", type=int, default=1)
    ap.add_argument("--tasks", action="append", default=[],
                    help="byte-pinned task file; a path token that occurs in it is upstream "
                         "benchmark data (an argument value the checker matched), not a machine "
                         "path, so it is kept and reported instead of masked")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return 0 if selftest() else 1
    if not (a.answers and a.label):
        print(__doc__)
        return 2
    keep = _ppa.pinned_path_tokens(*[os.path.expanduser(t) for t in a.tasks]) if a.tasks else ()
    if keep:
        print("upstream-pinned path tokens admitted: %d (proven from %s)"
              % (len(keep), ", ".join(os.path.basename(t) for t in a.tasks)))

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
    kept, masked = publish(a.answers, dst, keep)
    same_a = (open(dst, "rb").read() == open(a.answers, "rb").read())
    print("wrote %s lines=%d sha16=%s masked=%s bytes_identical_to_runner_output=%s"
          % (dst, kept, sha16(dst), masked or "nothing", same_a))
    outs = [(dst, kept)]

    if a.verdicts:
        vdst = os.path.join(OUT_DIR, "%s-verdicts.jsonl" % a.label)
        vkept, vmasked = publish(a.verdicts, vdst, keep)
        same = (open(vdst, "rb").read() == open(a.verdicts, "rb").read())
        print("wrote %s lines=%d sha16=%s masked=%s bytes_identical_to_scorer_output=%s"
              % (vdst, vkept, sha16(vdst), vmasked or "nothing", same))
        outs.append((vdst, vkept))
        sc = a.verdicts.rsplit(".", 1)[0] + ".sha16"
        if os.path.exists(sc):
            print("scorer's own verdict sidecar (sha1/16 over the same bytes): %s"
                  % open(sc).read().strip())

    if a.run_record:
        rrdst = os.path.join(OUT_DIR, "%s-run-record.json" % a.label)
        rr_lines = [l for l in open(a.run_record, encoding="utf-8") if l.strip()]
        if len(rr_lines) != 1:
            sys.exit("REFUSING: a run-record must be exactly one JSON line, got %d "
                     "(a hand-merged record is not admissible)" % len(rr_lines))
        rrkept, rrmasked = publish(a.run_record, rrdst, keep)
        json.loads(open(rrdst, encoding="utf-8").read())   # the shipped copy must parse
        print("wrote %s lines=%d sha16=%s masked=%s"
              % (rrdst, rrkept, sha16(rrdst), rrmasked or "nothing"))
        outs.append((rrdst, rrkept))

    print("\nREADME index lines (paste verbatim):")
    for p, n in outs:
        print("| %s | %d | `%s` |" % (os.path.basename(p), n, sha16(p)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
