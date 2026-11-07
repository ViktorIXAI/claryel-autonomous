#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gold-derivability audit for a PARB hard bank: find the B-ex6-04 defect class
automatically instead of discovering it after nine paid arms.

A task is a guessing lottery when its gold contains an atomic value that the
shipped prompt never states and never makes computable. This guard checks the
cheap, mechanical part of that claim for extraction-style categories (A, B, K):

  * every gold number must appear as a digit string in the prompt (the A/C
    families are computable by the prompt's own printed chain, so a missing
    number is only reported when it is not a constant of that chain — the
    audit therefore reports CANDIDATES, ranked, not verdicts);
  * every gold ISO date must appear either in ISO form or as
    "<day> <month-name> <year>" with ALL THREE components in the prompt;
  * every gold string must appear verbatim (case-insensitively, after
     whitespace normalization) in the prompt.

Output: one line per (task, missing atom) plus a per-version summary. Exit 0
always (this is a census, not a gate); use it before spending GPU time on a
task that cannot be passed by an honest reader.
"""
import json
import re
import sys

MONTHS = {"01": "январ", "02": "феврал", "03": "март", "04": "апрел", "05": "ма",
          "06": "июн", "07": "июл", "08": "август", "09": "сентябр", "10": "октябр",
          "11": "ноябр", "12": "декабр"}
import os
CATS = set(os.environ.get("PARB_AUDIT_CATS", "ABK"))


def num_forms(x):
    s = repr(x) if not isinstance(x, str) else x
    out = {s}
    try:
        f = float(x)
        out.add(("%f" % f).rstrip("0").rstrip("."))
        if f == int(f):
            out.add(str(int(f)))
    except Exception:
        pass
    return {t for t in out if t and t not in ("0", "1") or t == "0"}


def scan(bank_path):
    bank = json.load(open(bank_path, encoding="utf-8"))
    hits = []
    for t in bank:
        if t["id"][0] not in CATS:
            continue
        pr = re.sub(r"\s+", " ", t["prompt"].lower())
        ref = t.get("ref")
        stack = [(ref, "")]
        while stack:
            v, path = stack.pop()
            if isinstance(v, dict):
                stack.extend((vv, path + "." + kk) for kk, vv in v.items())
            elif isinstance(v, list):
                stack.extend((vv, path + "[%d]" % i) for i, vv in enumerate(v))
            elif isinstance(v, bool):
                continue
            elif isinstance(v, (int, float)):
                if not any(f in pr for f in num_forms(v)):
                    hits.append((t["id"], path, "number", repr(v)))
            elif isinstance(v, str):
                m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v)
                if m:
                    y, mo, d = m.groups()
                    iso = v in pr
                    trio = (y in pr and str(int(d)) in pr and MONTHS[mo] in pr)
                    if not (iso or trio):
                        hits.append((t["id"], path, "date", v))
                elif re.fullmatch(r"\d+(\.\d+)?%", v):
                    # A percent-shaped gold string is only contract-derivable if the task's
                    # own JSON spec states the VALUE FORM (a quoted example carrying '%');
                    # `"penalty_per_week"` with no hint makes number-vs-string a coin flip.
                    spec = re.search(r"JSON[^\n]*", t["prompt"])
                    txt = spec.group(0) if spec else t["prompt"]
                    if not re.search('"[^"]*%[^"]*"|«[^»]*%[^»]*»', txt):
                        hits.append((t["id"], path, "type_form", v))
                else:
                    s = re.sub(r"[\u00ab\u00bb\"'`\s]+", " ", v).lower().strip()
                    pnorm = re.sub(r"[\u00ab\u00bb\"'`]+", " ", pr)
                    if len(s) >= 2 and s not in pnorm and not any(
                            f in pr for f in num_forms(s)):
                        hits.append((t["id"], path, "string", v[:40]))
    return bank, hits


for path in sys.argv[1:]:
    bank, hits = scan(path)
    print("== %s  tasks=%d  sha-less census over categories %s" % (
        path, len(bank), "".join(sorted(CATS))))
    for h in sorted(hits):
        print("   %-10s %-22s %-7s %s" % h)
    bycat = {}
    for tid, _, kind, _ in hits:
        bycat[tid] = bycat.get(tid, 0) + 1
    print("   summary: %d candidate atoms over %d tasks" % (len(hits), len(bycat)))
    print("   tasks with candidates: %s" % ", ".join("%s(%d)" % kv for kv in sorted(bycat.items())))
