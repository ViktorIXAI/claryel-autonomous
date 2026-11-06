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
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts", "security"))
from sanitize_run_record import (  # noqa: E402
    HOST_PLACEHOLDER,
    PATH_PLACEHOLDER,
    PRIVATE_IP,
    HOME_PATH,
    write_run_record,
)

WS = os.path.expanduser("~/parb-v61-contour")
DST = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "pair-230")
RULES = [
    (PRIVATE_IP, HOST_PLACEHOLDER),
    (re.compile(r"claryel0\d"), "<HOST>"),
    (HOME_PATH, PATH_PLACEHOLDER),
]


def sanitize_text(text: str) -> str:
    for rx, sub in RULES:
        text = rx.sub(sub, text)
    return text


def sanitize_copy(src, dst, jsonl=True):
    if not os.path.exists(src):
        return False
    if not jsonl:
        # Plain logs: redact in place, never raw-copy.
        text = open(src, encoding="utf-8", errors="replace").read()
        open(dst, "w", encoding="utf-8").write(sanitize_text(text))
        return True
    out = []
    for line in open(src, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        line = sanitize_text(line)
        json.loads(line)
        out.append(line)
    with open(dst, "w", encoding="utf-8") as fh:
        fh.write('\n'.join(out) + '\n')
    return True


def publish_run_record(src, dst) -> bool:
    if not os.path.exists(src):
        return False
    data = json.load(open(src, encoding="utf-8"))
    write_run_record(dst, data)
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
        for pat, kind in (
            ("results-%s.jsonl", "jsonl"),
            ("ledger-%s.jsonl", "jsonl"),
            ("%s.log", "log"),
            ("run-record-%s.json", "run-record"),
        ):
            src = os.path.join(WS, pat % rid)
            dst = os.path.join(DST, pat % rid)
            if kind == "run-record":
                ok = publish_run_record(src, dst)
            else:
                ok = sanitize_copy(src, dst, jsonl=(kind == "jsonl"))
            if ok:
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
