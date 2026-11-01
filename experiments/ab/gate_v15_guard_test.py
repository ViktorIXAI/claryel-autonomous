#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline check of the cheap-repair guard (v1.5): format repair must not lose data."""
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
os.environ["PARB_GATE_VERSION"] = "v1.5"
os.environ.setdefault("PARB_KEY_FILE", "/nonexistent")
spec = importlib.util.spec_from_file_location("gr5", os.path.join(HERE, "gate_run.py"))
gr = importlib.util.module_from_spec(spec)
sys.modules["gr5"] = gr
spec.loader.exec_module(gr)

good = '[{"id":"A1","qty":5},{"id":"A2","qty":7},{"id":"A3","qty":9}]'
bad = '[{"id":"A1","qty":5}]'
fl = "AMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no"
fl2 = "AMOUNT: 5120\nPAYMENT_DAYS: 45"
csv_good = "id,qty\nA1,5\nA2,7\nA3,9"
csv_bad = "id\nA1\nA2"

CASES = [
    ("same structure", gr.struct_sig(good), gr.struct_sig(good), False),
    ("repair ate JSON rows", gr.struct_sig(bad), gr.struct_sig(good), True),
    ("repair ate fields", gr.struct_sig(fl2), gr.struct_sig(fl), True),
    ("repair added rows", gr.struct_sig(good), gr.struct_sig(bad), False),
# csv_bad also has fewer data rows (2 instead of 3): the row-count guard must fire.
# Guard limitation: it counts CSV rows, not columns.
    ("CSV: fewer rows", gr.struct_sig(csv_bad), gr.struct_sig(csv_good), True),
    ("empty answer after repair", gr.struct_sig(""), gr.struct_sig(fl), True),
]
bad_n = 0
for name, a, b, want in CASES:
    got = gr.worse_than_before(a, b)
    ok = got == want
    bad_n += 0 if ok else 1
    print("%-28s worse=%-5s expected=%-5s %s" % (name, got, want, "OK" if ok else "MISS"))

print("\nJSON-array signature:", gr.struct_sig(good))
print("fields signature:", gr.struct_sig(fl))
print("CSV signature:", gr.struct_sig(csv_good))
print("\nmodes:", "CHEAP_REPAIR =", gr.CHEAP_REPAIR, "| MAX_FMT_FIXES =", gr.MAX_FMT_FIXES)
print("RESULT:", "green" if bad_n == 0 else "PROBLEMS: %d" % bad_n)
