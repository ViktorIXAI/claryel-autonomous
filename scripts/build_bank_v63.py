#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build bank-hard-v6.3.json from the published v6.2 bytes (3c866ea7daae611c).

Exactly ONE correction, everything else byte-identical:

  B-ex6-04  prompt ONLY: the two dated facts now carry the year the gold
            already used (`подписан 3 марта 2026`, `старт работ 1 апреля 2026`).
            The v6.2 prompt states month and day but NO year anywhere, while
            its gold demands `start_date = 2026-04-01`; the year is therefore
            not contract-derivable and the task is a guess-the-year lottery.
            Published evidence (fifteen rows on the v6.2 line, bank copy
            d1e8d11df5840dcc, contour 2.45-2.48, every one `format_ok=True` and
            `fields_mismatch` on the year alone): 13 rows answered 2024-04-01,
            one 2023-04-01, one 2025-04-01 — zero answered the gold year.
            Gold bytes are NOT touched: the fix makes the prompt state what the
            gold already claimed, it does not move the gold.

The distractor clause (`Мой отпуск 10-20 марта ...`) stays exactly as shipped,
so the task keeps its rejection requirement. The v6.2 file is never modified.

Deterministic: the added year is RE-DERIVED at build time from the shipped
gold (`ref["start_date"][:4]`), never typed as a literal, so a CI re-run of
this script reproduces the exact output bytes and the stated year provably
equals the gold year.
"""
import hashlib
import json
import re
import sys

SRC = "benchmarks/hard/bank-hard-v6.2.json"
DST = "benchmarks/hard/bank-hard-v6.3.json"
SRC_SHA16 = "3c866ea7daae611c"  # published v6.2 identity guard

raw = open(SRC, "rb").read()
if hashlib.sha256(raw).hexdigest()[:16] != SRC_SHA16:
    sys.exit("FATAL: v6.2 source bytes moved (expected sha16 %s)" % SRC_SHA16)
bank = json.loads(raw)
tasks = {t["id"]: t for t in bank}

b = tasks["B-ex6-04"]
prompt = b["prompt"]
gold_start = b["ref"]["start_date"]
m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", gold_start)
if not m:
    sys.exit("FATAL: B-ex6-04 gold start_date is not ISO: %r" % gold_start)
year, gmon, gday = m.groups()
MONTHS = {"01": "января", "02": "февраля", "03": "марта", "04": "апреля",
          "05": "мая", "06": "июня", "07": "июля", "08": "августа",
          "09": "сентября", "10": "октября", "11": "ноября", "12": "декабря"}
if MONTHS[gmon] not in prompt:
    sys.exit("FATAL: B-ex6-04 prompt lost its gold-month phrase")

# The two facts that carry the gold's date components must be undated in v6.2
# (otherwise the correction would change meaning, not add a missing value).
facts = ["подписан 3 марта", "старт работ 1 апреля"]
for f in facts:
    if not re.search(re.escape(f) + r"(?!\s*\d{4})", prompt):
        sys.exit("FATAL: B-ex6-04 fact %r is missing or already dated" % f)
if year in prompt:
    sys.exit("FATAL: B-ex6-04 prompt already states the gold year — defect closed upstream")

new_prompt = prompt
for f in facts:
    new_prompt = new_prompt.replace(f, "%s %s" % (f, year), 1)

# The gold must now be contract-derivable from the shipped prompt alone.
if not re.search(r"1 апреля %s" % year, new_prompt):
    sys.exit("FATAL: derived prompt does not state the gold date")

changed = []
b["prompt"] = new_prompt
changed.append("B-ex6-04.prompt")

out = json.dumps(bank, ensure_ascii=False, indent=1).encode() + b"\n"
if not raw.endswith(b"\n"):
    out = out[:-1]
open(DST, "wb").write(out)

print("changed fields:", ", ".join(changed))
print("B-ex6-04 old prompt:", prompt[:120])
print("B-ex6-04 new prompt:", new_prompt[:130])
print("gold (unchanged):", gold_start, "| stated year derived from gold:", year)
print("wrote %s  sha16=%s  bytes=%d" % (DST, hashlib.sha256(out).hexdigest()[:16], len(out)))
