#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Офлайн-тест починки формы силами кода (v1.7): что можно чинить без модели и где нельзя."""
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
# 1. JSON с текстом вокруг — чинится
t = 'Конечно! Вот данные:\n[{"id":"A1","qty":5},{"id":"A2","qty":7}]\nГотово.'
r = gf.fix_json_text(a, t)
ck("json: текст вокруг вырезан", r and r.startswith('[{"id"') and '"A2"' in r)

# 2. JSON с хвостовыми запятыми и python-константами — чинится
t = '[{"id":"A1","qty":5,},{"id":"A2","qty":7}]'
r = gf.fix_json_text(a, t)
ck("json: хвостовая запятая", r and '"A2"' in r and json.loads(r)[1]["qty"] == 7)
t = '[{"id":"A1","qty":5,"ok":True},{"id":"A2","qty":7,"ok":False}]'
r = gf.fix_json_text(a, t)
ck("json: True/False", r and "true" in r and "false" in r)

# 3. Ключи без кавычек
t = "[{id: \"A1\", qty: 5}, {id: \"A2\", qty: 7}]"
r = gf.fix_json_text(a, t)
ck("json: ключи без кавычек", r and '"qty"' in r)

# 4. Данных нет вообще — не выдумываем
r = gf.fix_json_text(a, "Я не могу ответить")
ck("json: нет данных -> отказ", r is None)

# 5. Обрезанный JSON — не дописываем
r = gf.fix_json_text(a, '[{"id":"A1","qty":5},{"id":"A2","qty"')
ck("json: обрезанный массив -> отказ", r is None)

# 6. Поля: пояснения вокруг, ключи на месте
t = ("Ниже результат.\nAMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no\n"
     "Обратите внимание на сроки.")
r = gf.fix_fields_text(a, t, ["AMOUNT", "PAYMENT_DAYS", "DELIVERY_DAYS", "EXCLUDES_TAXES"])
ck("fields: мусор убран, порядок ключей задан",
   r == "AMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no")

# 7. Поля: ключа нет — не додумываем
r = gf.fix_fields_text(a, "AMOUNT: 5120\nPAYMENT_DAYS: 45", ["AMOUNT", "PAYMENT_DAYS", "DELIVERY_DAYS"])
ck("fields: нет ключа -> отказ", r is None)

# 8. Поля: markdown-маркеры и точка в конце
t = "- **AMOUNT:** 5 120 руб.\n- PAYMENT_DAYS: 45.\n"
r = gf.fix_fields_text(a, t, ["AMOUNT", "PAYMENT_DAYS"])
# значение очищается от висячей пунктуации на конце строки ("45." -> "45", "руб." -> "руб"):
# это оформление, а не данные, и проверка задач такие хвосты всё равно не требует
ck("fields: маркеры и висячая точка съедены",
   r and r.splitlines() == ["AMOUNT: 5 120 руб", "PAYMENT_DAYS: 45"])

# 9. CSV: текст вокруг таблицы
t = "Вот CSV:\nid,qty\nA1,5\nA2,7\nСпасибо!"
r = gf.fix_csv_text(a, t, ["id", "qty"], 2)
ck("csv: текст вокруг убран", r == "id,qty\nA1,5\nA2,7")

# 10. CSV: разное число полей -> отказ (значит строки битые, чинить данными нельзя)
r = gf.fix_csv_text(a, "id,qty\nA1,5\nA2", ["id", "qty"], 2)
ck("csv: битые строки -> отказ", r is None)

# 11. CSV: не то число строк -> отказ (не додумываем строки)
r = gf.fix_csv_text(a, "id,qty\nA1,5\nA2,7\nA3,9", ["id", "qty"], 2)
ck("csv: лишняя строка -> отказ", r is None)

ok = sum(1 for _, v in CASES if v)
for name, v in CASES:
    print("%s %s" % ("OK  " if v else "МИМО", name))
print("\nИТОГ: %d/%d" % (ok, len(CASES)))
