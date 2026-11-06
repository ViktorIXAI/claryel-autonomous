#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Copy paired-arm run files into the repo, sanitized, with a provenance summary.

Every published number in this repo has to be checkable by someone who does not have this machine, so the
ledger, the answer rows, the log and the run record go into the visible line together. Placeholders replace
host names, LAN addresses and local paths; the substitution is re-validated as JSON so a row cannot be
silently corrupted on the way out.

Usage: python3 scripts/publish_pair_arms.py c29r0 c29r1 c30r0 ...
"""
import json
import os
import re
import shutil
import sys

WS = os.path.expanduser("~/parb-v61-contour")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DST = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "pair-230")
RULES = [
    (re.compile(r"192\.168\.\d+\.\d+"), "<LAN_IP>"),
    (re.compile(r"10\.\d+\.\d+\.\d+"), "<LAN_IP>"),
    (re.compile(r"claryel0\d"), "<HOST>"),
    (re.compile(r"/home/viktor[^\s\"]*"), "<LOCAL_PATH>"),
]


def sanitize_copy(src, dst, jsonl=True):
    if not os.path.exists(src):
        return False
    if not jsonl:
        shutil.copyfile(src, dst)
        return True
    out = []
    for line in open(src, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        for rx, sub in RULES:
            line = rx.sub(sub, line)
        json.loads(line)
        out.append(line)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    return True


def main() -> int:
    ids = sys.argv[1:]
    if not ids:
        print("usage: publish_pair_arms.py <run id> ...")
        return 1
    if os.environ.get("PAIR_OUT_DIR"):
        globals()["DST"] = os.path.join(ROOT, "benchmarks", "hard", "v6-results",
                                        os.environ["PAIR_OUT_DIR"])
    os.makedirs(DST, exist_ok=True)
    for rid in ids:
        done = []
        for pat, js in (("results-%s.jsonl", True), ("ledger-%s.jsonl", True),
                        ("%s.log", False), ("run-record-%s.json", False)):
            src = os.path.join(WS, pat % rid)
            dst = os.path.join(DST, pat % rid)
            if sanitize_copy(src, dst, js):
                done.append(os.path.basename(dst))
        prov = {}
        lp = os.path.join(DST, "ledger-%s.jsonl" % rid)
        if os.path.exists(lp):
            for line in open(lp, encoding="utf-8"):
                r = json.loads(line)
                prov[(r.get("contour_version"), r.get("box"))] = prov.get(
                    (r.get("contour_version"), r.get("box")), 0) + 1
        v230 = sum(1 for line in open(lp, encoding="utf-8") if "v230" in line) if os.path.exists(lp) else 0
        print("%-7s -> %s | %s | guarantee touched %d rows" % (
            rid, ", ".join(done), "; ".join("contour %s on %s x%d" % (k[0], k[1], n)
                                           for k, n in sorted(prov.items())), v230))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
