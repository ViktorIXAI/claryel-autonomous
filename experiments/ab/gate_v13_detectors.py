#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Офлайн-проверка детекторов контура v1.3 на реальных задачах банка (ноль токенов модели)."""
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("gr", os.path.join(HERE, "gate_run.py"))
gr = importlib.util.module_from_spec(spec)
sys.modules["gr"] = gr
os.environ.setdefault("PARB_KEY_FILE", "/nonexistent")
spec.loader.exec_module(gr)

tasks = json.load(open(next(p for p in (os.path.expanduser("~/.hermes/bench/parb/bank.json"), os.path.join(HERE, "bank.json")) if os.path.exists(p)), encoding="utf-8"))
if isinstance(tasks, dict):
    tasks = tasks.get("tasks") or list(tasks.values())

print("всего задач в банке:", len(tasks))
by = {}
for t in tasks:
    cat = (t.get("id") or "?")[0]
    by.setdefault(cat, []).append(t)

for cat in ("K", "J", "B", "I", "H"):
    ts = by.get(cat, [])
    if not ts:
        continue
    dist = {}
    fields = {}
    for t in ts:
        f = gr.want_format(t["prompt"])
        dist[f] = dist.get(f, 0) + 1
        fields[t["id"]] = gr.want_fields(t["prompt"])
    print("\nкатегория %s (n=%d): форматы %s" % (cat, len(ts), dist))
    lens = sorted(len(v) for v in fields.values())
    print("   полей на задачу: мин %s, медиана %s, макс %s" %
          (lens[0], lens[len(lens) // 2], lens[-1]))
    for t in ts[:2]:
        print("   %s -> fmt=%s keys=%s" % (t["id"], gr.want_format(t["prompt"]),
                                           gr.want_fields(t["prompt"])[:8]))

# synthetic unit cases
CASES = [
    ("ВЫВЕДИ CSV с заголовком id,name и разделителем запятая", "csv"),
    ("Ответь строго JSON-массивом", "json"),
    ("Формат: JSON. Выведи строки AMOUNT: x. Данные в CSV не нужны", "ambiguous"),
    ("ВЫВЕДИ СТРОГО:\nAMOUNT: <число>\nPAYMENT_DAYS: <число>\nБЕЗ пояснений", "fields"),
    ("Просто ответ текстом", "text"),
]
bad = 0
print("\nсинтетические случаи:")
for pr, want in CASES:
    got = gr.want_format(pr)
    ok = got == want
    bad += 0 if ok else 1
    print("   %s want=%-9s got=%s" % ("OK " if ok else "МИМО", want, got))

# fields_gate-логика полноты: проверка на тексте ответа (без модели)
need = ["AMOUNT", "PAYMENT_DAYS", "DELIVERY_DAYS", "EXCLUDES_TAXES"]
ANS = [("AMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no", 0),
       ("AMOUNT: 5120\nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 10", 1),
       ("AMOUNT: \nPAYMENT_DAYS: 45\nDELIVERY_DAYS: 7\nEXCLUDES_TAXES: no\nAMOUNT: 1", 1)]
print("\nполнота полей (пробелы/пропуски/дубли):")
for text, want in ANS:
    got = {}
    for ln in text.splitlines():
        m = re.match(r"^\s*([A-Z][A-Z0-9_]{2,})\s*:\s*(.*)$", ln)
        if m:
            got.setdefault(m.group(1), []).append(m.group(2).strip())
    prob = []
    for k in need:
        if k not in got:
            prob.append("нет %s" % k)
        elif not got[k][0]:
            prob.append("%s пусто" % k)
        elif len(got[k]) > 1:
            prob.append("%s дубль" % k)
    ok = len(prob) == want
    bad += 0 if ok else 1
    print("   %s нашли %d (надо %d): %s" % ("OK " if ok else "МИМО", len(prob), want, "; ".join(prob)))

print("\nИТОГ офлайн-проверки:", "зелёная" if bad == 0 else "ЕСЬ ПРОБЛЕМ: %d" % bad)
