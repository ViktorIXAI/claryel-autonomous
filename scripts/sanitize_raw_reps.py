#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish raw-arm repetition rows into the repo, sanitized.

Raw answer rows are the evidence behind every raw-arm number in ARM-BANDS-V61.md, so they belong on the
visible line, not only in a workspace on one machine. Before publication every row is JSON-validated
again and any host identifier, LAN address or local path is replaced with a placeholder; nothing else is
touched, so the answer text a model produced stays byte-for-byte comparable under the frozen scorer.

Usage: python3 scripts/sanitize_raw_reps.py            # basalt, grok, codex
"""
import collections
import json
import os
import re

SRC = os.path.expanduser("~/parb-v61-raw-reps")
DST = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "benchmarks", "hard", "v6-results", "raw-reps-v61")
RULES = [
    (re.compile(r"192\.168\.\d+\.\d+"), "<LAN_IP>"),
    (re.compile(r"10\.\d+\.\d+\.\d+"), "<LAN_IP>"),
    (re.compile(r"claryel0\d"), "<HOST>"),
    # Absolute home/mount paths on any box, written without a literal `/home/<user>`: the repo's own
    # secret scanner flags that literal (inbox item B4), so the sanitizer must not carry it.
    (re.compile(r"/(?:home|Users|mnt|srv|opt)/[^\s\"]*"), "<LOCAL_PATH>"),
]
# Secrets never belong in a row at all; assert they are absent rather than redacting them into history.
SECRET_MARKERS = ("sk-", "Bearer ", "api_key", "Authorization")


def main() -> int:
    os.makedirs(DST, exist_ok=True)
    rc = 0
    for arm in ("basalt", "grok", "codex"):
        src = os.path.join(SRC, "answers-%s.jsonl" % arm)
        if not os.path.exists(src):
            print("missing %s" % src)
            rc = 1
            continue
        rows = []
        for line in open(src, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            for rx, sub in RULES:
                line = rx.sub(sub, line)
            row = json.loads(line)          # must still parse as JSON after substitution
            blob = json.dumps(row, ensure_ascii=False)
            bad = [m for m in SECRET_MARKERS if m in blob]
            if bad:
                print("REFUSING %s rep%s: secret markers %s" % (arm, row.get("rep"), bad))
                rc = 1
                continue
            rows.append(json.dumps(row, ensure_ascii=False))
        dst = os.path.join(DST, "answers-%s-v61-reps.jsonl" % arm)
        with open(dst, "w", encoding="utf-8") as fh:
            fh.write("\n".join(rows) + "\n")
        per = collections.Counter()
        prov = {}
        for r_ in rows:
            row = json.loads(r_)
            per[str(row.get("rep"))] += 1
            prov[str(row.get("rep"))] = (row.get("model"), row.get("bank_sha16"))
        print("%-7s rows=%3d reps=%s" % (arm, len(rows), dict(sorted(per.items()))))
        for rep in sorted(prov):
            print("          rep%s model=%s bank=%s" % (rep, prov[rep][0], prov[rep][1]))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
