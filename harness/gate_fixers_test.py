#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Offline test of code-only form repair (v1.7): what can be fixed without the model and what cannot."""
import importlib.util
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gf", os.path.join(HERE, "gate_fixers.py"))
gf = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gf)


class A:
    def __init__(self):
        self.evts = []

    def ev(self, a, b):
        self.evts.append("%s:%s" % (a, b))


CASES = []


def ck(name, cond):
    CASES.append((name, bool(cond)))


a = A()
# 1. JSON wrapped in prose — fixable
t = 'Конечно! Вот данные:\n[{"id":"A1","qty":5},{"id":"A2","qty":7}]\nГотово.'
r = gf.fix_json_text(a, t)
ck("json: prose stripped", r and r.startswith('[{"id"') and '"A2"' in r)

# 2. JSON with trailing commas and python constants — fixable
t = '[{"id":"A1","qty":5,},{"id":"A2","qty":7}]'
r = gf.fix_json_text(a, t)
ck("json: trailing comma", r and '"A2"' in r and json.loads(r)[1]["qty"] == 7)
t = '[{"id":"A1","qty":5,"ok":True},{"id":"A2","qty":7,"ok":False}]'
r = gf.fix_json_text(a, t)
ck("json: True/False", r and "true" in r and "false" in r)

# 3. Unquoted keys
t = "[{id: \"A1\", qty: 5}, {id: \"A2\", qty: 7}]"
r = gf.fix_json_text(a, t)
ck("json: unquoted keys", r and '"qty"' in r)

# 4. No data at all — we do not invent
r = gf.fix_json_text(a, "Я не могу ответить")
ck("json: no data -> refuse", r is None)

# 5. Truncated JSON — we do not complete it
r = gf.fix_json_text(a, '[{"id":"A1","qty":5},{"id":"A2","qty"')
ck("json: truncated array -> refuse", r is None)

# 6. Fields: prose around, keys present
t = ("Ниже результат.\nAMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no\n"
     "Обратите внимание на сроки.")
r = gf.fix_fields_text(a, t, ["AMOUNT", "PAYMENT_DAYS", "DELIVERY_DAYS", "EXCLUDES_TAXES"])
ck("fields: junk removed, key order enforced",
   r == "AMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no")

# 7. Fields: a key is missing — we do not invent it
r = gf.fix_fields_text(a, "AMOUNT: 5120\nPAYMENT_DAYS: 45", ["AMOUNT", "PAYMENT_DAYS", "DELIVERY_DAYS"])
ck("fields: missing key -> refuse", r is None)

# 8. Fields: markdown markers and a trailing period
t = "- **AMOUNT:** 5 120 руб.\n- PAYMENT_DAYS: 45.\n"
r = gf.fix_fields_text(a, t, ["AMOUNT", "PAYMENT_DAYS"])
# the value is stripped of dangling end-of-line punctuation ("45." -> "45", "руб." -> "руб"):
# this is presentation, not data, and the task validator never needs those tails
ck("fields: markers and dangling period removed",
   r and r.splitlines() == ["AMOUNT: 5 120 руб", "PAYMENT_DAYS: 45"])

# 9. CSV: prose around the table
t = "Вот CSV:\nid,qty\nA1,5\nA2,7\nСпасибо!"
r = gf.fix_csv_text(a, t, ["id", "qty"], 2)
ck("csv: prose stripped", r == "id,qty\nA1,5\nA2,7")

# 10. CSV: uneven field counts -> refuse (rows are corrupt; cannot be fixed with data we have)
r = gf.fix_csv_text(a, "id,qty\nA1,5\nA2", ["id", "qty"], 2)
ck("csv: corrupt rows -> refuse", r is None)

# 11. CSV: wrong row count -> refuse (we do not invent rows)
r = gf.fix_csv_text(a, "id,qty\nA1,5\nA2,7\nA3,9", ["id", "qty"], 2)
ck("csv: extra row -> refuse", r is None)

ok = sum(1 for _, v in CASES if v)
for name, v in CASES:
    print("%s %s" % ("OK  " if v else "MISS", name))
print("\nRESULT: %d/%d" % (ok, len(CASES)))
