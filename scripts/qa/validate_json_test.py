#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the JSONL line-splitting rule in scripts/qa/validate_json.py.

Pinned bug (measured 08.11, red devsecops): GPQA-Diamond's upstream text carries a literal
U+2028 LINE SEPARATOR inside a prompt string. Python's str.splitlines() breaks the record
there, so the validator reported two phantom syntax errors on a file whose every real line
parses. The fix is to split JSONL on "\n" only.

The test is non-vacuous: it asserts a genuinely broken line is still reported.
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate_json import jsonl_failures  # noqa: E402

fails = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        fails.append("%s %s" % (name, detail))
        print("FAIL", name, detail)
    else:
        print("ok  ", name)


with tempfile.TemporaryDirectory() as td:
    p = Path(td) / "u2028.jsonl"
    # one real record whose text contains U+2028, U+2029, U+0085 and vertical tab
    rec = {"id": "x-1", "prompt": "line sep \u2028 para sep \u2029 nel \x85 vtab \x0b done",
           "gold": "A"}
    p.write_text(json.dumps(rec, ensure_ascii=False) + "\n", encoding="utf-8")
    got = jsonl_failures(p)
    check("separators inside a string are one record", got == [], repr(got)[:120])

    # the same file must still be readable as one JSON object per "\n"-split line
    lines = [l for l in p.read_text(encoding="utf-8").split("\n") if l.strip()]
    check("one line, one record", len(lines) == 1 and json.loads(lines[0])["id"] == "x-1")

    bad = Path(td) / "bad.jsonl"
    bad.write_text('{"id": "ok"}\nnot json at all\n{"id": "also ok"}\n', encoding="utf-8")
    got = jsonl_failures(bad)
    check("a broken line is still reported", len(got) == 1 and "line 2" in got[0], repr(got)[:160])

    empty = Path(td) / "blank.jsonl"
    empty.write_text("\n\n", encoding="utf-8")
    check("blank lines are not findings", jsonl_failures(empty) == [])

    junk = Path(td) / "junk.jsonl"
    junk.write_text("404: Not Found\n", encoding="utf-8")
    check("a fetched error page IS a finding", len(jsonl_failures(junk)) == 1)

print("\n%d checks, %d failures" % (5, len(fails)))
sys.exit(1 if fails else 0)
