#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build bank-hard-v6.4.json from the published v6.3 bytes (73f7a04d57473545).

Exactly ONE correction, everything else byte-identical:

  B-ex6-04  prompt ONLY: the JSON spec now states the VALUE FORM of
            `penalty_per_week` — a string carrying a percent sign, with a
            non-gold example (`5%`). The v6.3 prompt types `start_date`
            (`ГГГГ-ММ-ДД`) and `budget_eur` (`число`) but leaves
            `penalty_per_week` bare, while its gold is the STRING `"2%"`.
            Measured, not guessed: the bank-identity probe of 2026-11-07
            (arms p62r22-24 on v6.2 vs p63r22-24 on v6.3, contour 0.0.2.48,
            identical sp1 seeds 861061/593370/188460) showed the v6.3 year
            correction working exactly as intended — start_date went from
            `2024-04-01` (3/3 wrong year, 0/3 strict) to `2026-04-01` (3/3
            right year) — while all three v6.3 rows then failed on
            `penalty_per_week: 2` (number) vs gold `"2%"` (string). The same
            defect is flagged mechanically by scripts/bank_derivability_audit.py
            as `type_form` on v6.3 and only on this task.

The added hint is DERIVED from the shipped gold's shape (its unit character)
and must NOT contain the gold value itself, so the correction states a form
without leaking the answer. The v6.3 file is never modified.
"""
import hashlib
import json
import re
import sys

SRC = "benchmarks/hard/bank-hard-v6.3.json"
DST = "benchmarks/hard/bank-hard-v6.4.json"
SRC_SHA16 = "73f7a04d57473545"  # published v6.3 identity guard

raw = open(SRC, "rb").read()
if hashlib.sha256(raw).hexdigest()[:16] != SRC_SHA16:
    sys.exit("FATAL: v6.3 source bytes moved (expected sha16 %s)" % SRC_SHA16)
bank = json.loads(raw)
tasks = {t["id"]: t for t in bank}

b = tasks["B-ex6-04"]
prompt = b["prompt"]
gold_pen = b["ref"]["penalty_per_week"]
if not isinstance(gold_pen, str):
    sys.exit("FATAL: B-ex6-04 gold penalty_per_week is not a string: %r" % gold_pen)
mu = re.fullmatch(r"(\d+(?:\.\d+)?)(%)", gold_pen)
if not mu:
    sys.exit("FATAL: gold penalty_per_week is not percent-shaped: %r" % gold_pen)
unit = mu.group(2)

key = '"penalty_per_week"'
if prompt.count(key) != 1:
    sys.exit("FATAL: B-ex6-04 spec key %s found %d times" % (key, prompt.count(key)))
if prompt.count("%") != 1:
    sys.exit("FATAL: the prompt's percent token moved — shipped text changed")

# The hint: same key, now typed, with an example whose VALUE differs from gold.
example = "5" + unit
if example == gold_pen:
    sys.exit("FATAL: the example would leak the gold value")
hint = key + ':"число%s (например %s)"' % (unit, example)
new_prompt = prompt.replace(key, hint, 1)

# The prose fact already states `2%` (that is the fact being extracted); what must
# never happen is the FORM HINT using the gold value as its example.
if gold_pen in hint:
    sys.exit("FATAL: the form hint uses the gold value as its example — answer leakage")
sp_new = re.search(r"JSON.*", new_prompt)
if not sp_new:
    sys.exit("FATAL: no JSON spec line in the corrected prompt")
if not re.search(r'"penalty_per_week":"[^"]*%[^"]*"', new_prompt):
    sys.exit("FATAL: corrected prompt does not type the field with a percent example")
if new_prompt.count("2026") != 2:
    sys.exit("FATAL: v6.3's stated year disappeared")

changed = []
b["prompt"] = new_prompt
changed.append("B-ex6-04.prompt")

out = json.dumps(bank, ensure_ascii=False, indent=1).encode() + b"\n"
if not raw.endswith(b"\n"):
    out = out[:-1]
open(DST, "wb").write(out)

print("changed fields:", ", ".join(changed))
sp_old = re.search(r"JSON.*", prompt)
print("spec before:", sp_old.group(0) if sp_old else "?")
print("spec after :", sp_new.group(0))
print("gold (unchanged):", json.dumps(b["ref"], ensure_ascii=False))
print("wrote %s  sha16=%s  bytes=%d" % (DST, hashlib.sha256(out).hexdigest()[:16], len(out)))
