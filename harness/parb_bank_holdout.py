#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Held-out task bank generator.

The dev bank (seed 20261031) was used throughout contour development.
This holdout is generated AFTER contour v1.9 was frozen:

  * identical category/level structure as the dev bank, but every task
    instance comes from a different seed (20261101) — unseen instances of
    the same families;
  * plus hand-written NEW instances in existing task conventions with
    content never present in the dev bank;
  * ids remapped with an "x" level-marker so they are disjoint from dev ids
    (scripts/sanity_data.py asserts disjointness in CI).

Generalization reading: a contour gain that survives on holdout instances
is a real harness property; a gain that only exists on dev instances was
partly task-tuning. This bank was NOT used during v1.0–v1.9 development
(chronology in history/timeline.md).

Usage: python3 harness/parb_bank_holdout.py
Output: benchmarks/holdout/bank-holdout.json
"""
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from parb_bank import build  # deterministic generators, same as dev bank

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "benchmarks", "holdout", "bank-holdout.json")
HOLDOUT_SEED = 20261101


def dev_counts():
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dev = json.load(open(os.path.join(repo, "benchmarks", "text-gates", "bank.json"),
                         encoding="utf-8"))
    counts = {}
    for t in dev:
        cat, level = t["cat"], t["level"]
        i = int(t["id"].split("-")[2])
        counts.setdefault(cat, {}).setdefault(level, 0)
        counts[cat][level] = max(counts[cat][level], i + 1)
    return counts, dev


def extra_tasks():
    """new hand-written instances, existing conventions (units/ref compatible
    with the frozen v1.9 scorer), content absent from the dev bank."""
    t = []
    # A-style depreciation (new scenario, same numeric-ref convention as invoices)
    t.append({"id": "A-xd-00-0", "cat": "A", "level": "holdout", "kind": "total",
              "units": "depreciation", "seed": 91011,
              "prompt": "Оборудование стоит 240000. Линейная амортизация 5 лет, "
                        "годовая ставка равномерная. Посчитай годовую амортизацию "
                        "и остаточную стоимость через 2 года. Ответ числами.",
              "ref": {"annual": "48000.00", "residual_after_2y": "144000.00"}})
    # A-style cross-currency (new)
    t.append({"id": "A-xc-00-0", "cat": "A", "level": "holdout", "kind": "total",
              "units": "currency", "seed": 91012,
              "prompt": "Курс A/B = 1.5, B/C = 2.0. Переведи 100 единиц A в C, "
                        "затем прибавь 30 единиц C. Итог одним числом.",
              "ref": {"result": "330.00"}})
    # J-style CSV join with duplicate key (new tables)
    csv1 = "id;qty\n10;3\n11;5\n10;2\n12;7"
    csv2 = "id;price\n10;100\n11;50\n12;20"
    t.append({"id": "J-x1-00-0", "cat": "J", "level": "holdout", "kind": "csv",
              "units": "csv_join", "seed": 91013,
              "prompt": "Таблицы:\n%s\n---\n%s\nПосчитай суммарную стоимость по id "
                        "(строки-дубликаты id=10 складываются по qty). Ответ: id=сумма, "
                        "в одну строку." % (csv1, csv2),
              "ref": {"10": "500", "11": "250", "12": "140"}})
    # C-style explicit conflict flag (new)
    t.append({"id": "C-xf-00-0", "cat": "C", "level": "holdout", "kind": "rules",
              "units": "conflict", "seed": 91014,
              "prompt": "Правило 1: все счета свыше 100000 отправляются на проверку. "
                        "Правило 2: счета на проверку не архивируются. "
                        "Правило 3: счет 120000 заархивирован. "
                        "Есть ли противоречие? Ответ: CONFLICT или NO_CONFLICT и одно число — "
                        "сумму всех упомянутых счетов.",
              "ref": {"flag": "CONFLICT", "sum": "120000"}})
    # D-style agent plan with two forbidden tools (new scenario)
    t.append({"id": "D-xp-00-0", "cat": "D", "level": "holdout", "kind": "agent_plan",
              "units": "agent_plan", "seed": 91015,
              "prompt": "Ты агент Hermes с инструментами: READ_FILE, WRITE_FILE, SEARCH, "
                        "EXECUTE_COMMAND, SEND_EMAIL, CREATE_DOCUMENT.\nЗадача: сверить "
                        "акт invoices.pdf с реестром registry.xlsx и подготовить исправление. "
                        "Писать письма и выполнять shell-команды запрещено. "
                        "Перечисли инструменты по одному в строке в правильном порядке.",
              "ref": {"must": ["READ_FILE", "SEARCH", "WRITE_FILE"],
                      "must_not_plan": ["SEND_EMAIL", "EXECUTE_COMMAND"],
                      "order": ["READ_FILE", "SEARCH", "WRITE_FILE"],
                      "mode": "plan"}})
    # B-style extraction (new text)
    t.append({"id": "B-xx-00-0", "cat": "B", "level": "holdout", "kind": "extract",
              "units": "fields", "seed": 91016,
              "prompt": "Извлеки из текста поля: номер договора, дату, сумму.\n"
                        "«Договор № Д-2026/417 от 12.09.2026, сумма 1 890 500 руб.»",
              "ref": {"contract": "Д-2026/417", "date": "12.09.2026", "amount": "1890500"}})
    for x in t:
        x["stage"] = "4"
    return t


def main():
    counts, dev = dev_counts()
    tasks = build(HOLDOUT_SEED, counts)
    # remap ids: level code ea/ha/sa/va -> xe/xh/xs/xv (disjoint from dev bank)
    for t in tasks:
        p = t["id"].split("-")
        p[1] = "x" + p[1][0]
        t["id"] = "-".join(p)
    tasks += extra_tasks()
    dev_ids = {t["id"] for t in dev}
    hold_ids = {t["id"] for t in tasks}
    assert not (dev_ids & hold_ids), "holdout ids overlap dev bank"
    assert len(hold_ids) == len(tasks), "duplicate holdout ids"
    h = hashlib.sha256(json.dumps([t["id"] for t in tasks]).encode()).hexdigest()[:16]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(tasks, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("holdout tasks=%d hash16=%s -> %s" % (len(tasks), h, OUT))


if __name__ == "__main__":
    main()
