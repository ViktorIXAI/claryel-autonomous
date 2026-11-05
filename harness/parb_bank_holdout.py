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

Version note: v3 (2026-11-05) re-fit the four hand-written extras (A-xc, A-xd,
J-x1, C-xf) to the frozen scorers' ref conventions and added a build-time
scorer guard — the first Basalt holdout run showed them dying with
KeyError('sub'/'n'/'letters'). v2 (2026-11-01) assembles the long G documents
(`assembled_doc`) exactly like the dev-bank prep stage does. The first
published holdout bank (v1) shipped G tasks WITHOUT the document, making
holdout G results invalid — the bug and its discovery are recorded in
history/failures/failures.md; task ids and refs are unchanged between v1/v2.

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
from parb_bank import build, FILLER, CITIES  # deterministic generators, same as dev bank

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
    t.append({"id": "A-xd-00-0", "cat": "A", "level": "holdout", "kind": "find_error",
              "units": "depreciation", "seed": 91011,
              "prompt": "Смета: позиция 1) сервер 120000.00; позиция 2) годовая амортизация 24000.00; "
                        "позиция 3) обслуживание 30000.00; всего 174000.00. Оборудование стоит "
                        "240000.00, линейная амортизация за 5 лет — годовая 48000.00. Укажи номер "
                        "ошибочной позиции, её верное значение и верный итог. Числа двумя знаками.",
              "ref": {"bad_pos": 2, "correct_line": "48000.00", "correct_total": "198000.00"}})
    # A-style cross-currency (new)
    t.append({"id": "A-xc-00-0", "cat": "A", "level": "holdout", "kind": "total",
              "units": "currency", "seed": 91012,
              "prompt": "Товар стоит 200 €. Курс 90.5 ₽/€, счёт без скидки в рублях — 18100.00. "
                        "Дай пять строк: без скидки; скидка 10%; после скидки; НДС 20% от суммы "
                        "после скидки; итог (после скидки с НДС). Все суммы двумя знаками после запятой.",
              "ref": {"sub": "18100.00", "disc": "1810.00", "after": "16290.00",
                      "vat": "3258.00", "total": "19548.00"}})
    # J-style CSV join with duplicate key (new tables)
    csv1 = "id;qty\n10;3\n11;5\n10;2\n12;7"
    csv2 = "id;price\n10;100\n11;50\n12;20"
    t.append({"id": "J-x1-00-0", "cat": "J", "level": "holdout", "kind": "csv",
              "units": "csv_join", "seed": 91013,
              "prompt": "Таблицы:\n%s\n---\n%s\nСведи по id: суммарное qty (дубликаты id=10 складывать) "
                        "и цену. Формат: заголовок id,qty,price и по одной строке на id, без пояснений."
                        % (csv1, csv2),
              "ref": {"style": "csv", "n": 3,
                      "recs": [["10", 5, 100], ["11", 5, 50], ["12", 7, 20]]}})
    # C-style explicit conflict flag (new)
    t.append({"id": "C-xf-00-0", "cat": "C", "level": "holdout", "kind": "rules",
              "units": "conflict", "seed": 91014, "n_cand": 5,
              "prompt": "Правило 1: все счета свыше 100000 отправляются на проверку. "
                        "Правило 2: счета на проверку не архивируются. "
                        "Правило 3: счет 120000 заархивирован. "
                        "Выбери ВСЕ верные утверждения и выведи их буквы одной строкой.\n"
                        "A) правила противоречат друг другу\n"
                        "B) противоречия нет\n"
                        "C) счет 120000 не попадает на проверку\n"
                        "D) архивация не нарушает правило 2\n"
                        "E) правило 1 применяется к счетам свыше 100000",
              "ref": {"letters": ["A", "E"]}})
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


def assemble_G(t):
    """Same assembly as the dev-bank prep stage (parb_prep): fact units at
    head/mid/tail, filler units padded to the token target (~3.5 chars/token
    for Russian, calibrated on the dev bank)."""
    known = "\n".join(t["head_units"] + t["mid_units"] + t["tail_units"] + [t["prompt"]])
    target_chars = int(t["target_tokens"] * 3.5)
    need = max(0, int((target_chars - len(known)) // 150))
    fillers = [FILLER % (CITIES[j % len(CITIES)], 1000 + j, (j % 7) + 1, (j % 11) + 6)
               if "%s" in FILLER else
               FILLER.format(c=CITIES[j % len(CITIES)], n=1000 + j, d=(j % 7) + 1, y=(j % 11) + 6)
               for j in range(need)]
    half = need // 2
    t["assembled_doc"] = "\n".join(t["head_units"] + fillers[:half] + t["mid_units"] +
                                   fillers[half:] + t["tail_units"])
    t["filler_units"] = need
    return t


def main():
    counts, dev = dev_counts()
    tasks = build(HOLDOUT_SEED, counts)
    for t in tasks:
        if t["cat"] == "G":
            assemble_G(t)
    # remap ids: level code ea/ha/sa/va -> xe/xh/xs/xv (disjoint from dev bank)
    for t in tasks:
        p = t["id"].split("-")
        p[1] = "x" + p[1][0]
        t["id"] = "-".join(p)
    tasks += extra_tasks()
    # --- scorer-compatibility guard: never ship a bank the frozen scorer cannot
    # score. v1 shipped G without assembled_doc; v2 shipped 4 hand-written tasks
    # with ad-hoc ref shapes that KeyError'd inside check_A/J/C at scoring time.
    import parb_check as CK
    import parb_loop as LP
    SC = {c: getattr(CK, "check_" + c) for c in "ABCEFGHIJK"}
    bad = []
    for t in tasks:
        try:
            if t["cat"] == "D":
                LP.check_D_loop(t, {"agent_steps": [], "agent_final": ""})
            else:
                SC[t["cat"]](t, "0")
        except KeyError as e:
            bad.append((t["id"], "ref key missing: %s" % e))
    for tid, why in bad:
        print("BANK GUARD FAIL:", tid, why)
    if bad:
        raise SystemExit(1)
    print("bank guard: all %d tasks scorable" % len(tasks))
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
