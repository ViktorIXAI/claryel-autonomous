#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Publish one public-line arm into benchmarks/public/arms/ with the privacy scrub applied.

Why a script: the PUB digest rows are only auditable if the bytes behind them ship. The ledger
carries the gate/ladder/token columns and the results rows carry `gen.request_shape` (the parity
rule's evidence), so both go out together with the converted answers the public checker scored.

Scrub (AGENTS.md safety rules): hostnames -> <HOST>, LAN addresses -> <LAN_IP>, absolute local
paths -> <LOCAL_PATH>, key/endpoint material -> [REDACTED]. Answer text is never edited; only
infrastructure fields are masked, and the script prints what it masked.

Usage: publish_pub_arms.py <ws-dir> <arm-label> [--bench <bench>]
"""
import hashlib
import json
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO, "benchmarks", "public", "arms")

HOST = re.compile(r'"hostname"\s*:\s*"[^"]*"')
LAN = re.compile(r'\b(?:10(?:\.[0-9]{1,3}){3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|'
                 r'172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b')
PATH = re.compile(r'(?:/home|/Users|/mnt|/srv|/opt)/[^\s",]*')


def scrub(line):
    hits = []
    if HOST.search(line):
        hits.append("hostname")
        line = HOST.sub('"hostname": "<HOST>"', line)
    if LAN.search(line):
        hits.append("lan_ip")
        line = LAN.sub("<LAN_IP>", line)
    if PATH.search(line):
        hits.append("local_path")
        line = PATH.sub("<LOCAL_PATH>", line)
    line = re.sub(r'("api_key"\s*:\s*)"[^"]*"', r'\1"[REDACTED]"', line)
    return line, hits


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    ws, label = sys.argv[1], sys.argv[2]
    bench = ""
    if "--bench" in sys.argv:
        bench = sys.argv[sys.argv.index("--bench") + 1]
    # `matched` = the matched-shape parity legs; `frozen` = the original escalation-shape legs
    # (published unchanged so a superseded row stays re-scorable too).
    srcset = "matched"
    if "--srcset" in sys.argv:
        srcset = sys.argv[sys.argv.index("--srcset") + 1]
    ws = os.path.expanduser(ws)
    os.makedirs(OUT_DIR, exist_ok=True)
    rec_glob = ("run-record-pub-%s-contour-matched.json" % (bench or "*") if srcset == "matched"
                else "run-record-pub-%s-contour.json" % (bench or "*"))
    wanted = [("results-%s.jsonl" % ("matched" if srcset == "matched" else "main"), "results.jsonl"),
              ("gate-ledger-%s.jsonl" % ("matched" if srcset == "matched" else "main"),
               "ledger.jsonl"),
              ("answers-contour%s.jsonl" % ("-matched" if srcset == "matched" else ""),
               "answers.jsonl"),
              ("stats-contour%s.json" % ("-matched" if srcset == "matched" else ""), "stats.json"),
              (rec_glob, "run-record.json"),
              ("plan.json", "plan.json"),
              ("bank-version.json", "bank-version.json"),
              ("WS-IDENTITY.json", "ws-identity.json")]
    masked = {}
    shipped = []
    for src, dst in wanted:
        paths = []
        if "*" in src:
            base = src.split("*")[0]
            tail = src.split("*")[1]
            paths = [os.path.join(ws, f) for f in sorted(os.listdir(ws))
                     if f.startswith(base) and f.endswith(tail)]
        else:
            p = os.path.join(ws, src)
            if os.path.exists(p):
                paths = [p]
        if not paths:
            print("  skip (absent): %s" % src)
            continue
        out = os.path.join(OUT_DIR, "%s-%s" % (label, dst))
        n = 0
        with open(out, "w", encoding="utf-8") as fh:
            for p in paths:
                for line in open(p, encoding="utf-8"):
                    s, hits = scrub(line.rstrip("\n"))
                    for h in hits:
                        masked[h] = masked.get(h, 0) + 1
                    fh.write(s + "\n")
                    n += 1
        shipped.append((os.path.relpath(out, REPO), n,
                        hashlib.sha256(open(out, "rb").read()).hexdigest()[:16]))
    print("masked fields:", json.dumps(masked))
    for rel, n, sha in shipped:
        print("  %-56s lines=%-5d sha16=%s" % (rel, n, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
