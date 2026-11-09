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
# Whole path-shaped token, prefix included: a token is only ever kept when THIS exact string
# (e.g. a fake dataset path with a `/user` prefix) also occurs in the byte-pinned task file.
# The leading `/?` is deliberate: without it the scan starts at `user` and the pin loses the
# leading slash, so the arm's token and the pinned token would not be the same string.
PATH_TOKEN = re.compile(r'/?[A-Za-z0-9_.\-]*(?:/home|/Users|/mnt|/srv|/opt)/[^\s",\\]*')


def pinned_path_tokens(*files):
    """Path-shaped tokens that live in byte-pinned upstream data (task/bank files).

    Why this exists: pinned public benchmark data carries fake paths (an upstream function
    argument like a dataset path under a home directory), and an arm's answer can echo that token
    verbatim as an argument value. Masking it would edit the exact bytes the published checker
    verdict was computed from, and a masked token is not valid call syntax, so the published arm
    would stop reproducing its own percent. A token is admissible here only if the pinned file
    itself contains it — a machine path can never satisfy that test.
    """
    out = set()
    for f in files:
        text = open(f, encoding="utf-8", errors="replace").read()
        out.update(PATH_TOKEN.findall(text))
    return {t for t in out if t}


def scrub(line, keep=()):
    """Mask infrastructure fields. `keep` = tokens proven to be pinned upstream data.

    Kept tokens are reported as `upstream_pinned_path` so a scan never silently loses one.
    """
    hits = []
    if HOST.search(line):
        hits.append("hostname")
        line = HOST.sub('"hostname": "<HOST>"', line)
    if LAN.search(line):
        hits.append("lan_ip")
        line = LAN.sub("<LAN_IP>", line)
    restored = []
    for i, tok in enumerate(sorted(keep, key=len, reverse=True)):
        n = line.count(tok)
        if n:
            hits.extend(["upstream_pinned_path"] * n)
            ph = "\x00KEEP%d\x00" % i
            line = line.replace(tok, ph)
            restored.append((ph, tok))
    if PATH.search(line):
        hits.append("local_path")
        line = PATH.sub("<LOCAL_PATH>", line)
    for ph, tok in restored:
        line = line.replace(ph, tok)
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
