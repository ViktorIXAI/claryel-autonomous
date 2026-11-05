#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for v2.0 G/H answer post-normalization."""
import json
import os
import sys

os.environ["STRATA_CHECKER_INJECT"] = "1"  # historical behaviour test (OFF by default since 0.0.2.14, issue #15)
os.environ["PARB_GATE_VERSION"] = "v2.0"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gate_run as GR

BANK = os.path.join(HERE, "..", "benchmarks", "text-gates", "bank.json")
bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
passed = failed = 0


def ok(name, cond):
    global passed, failed
    if cond:
        passed += 1
        print("ok", name)
    else:
        failed += 1
        print("FAIL", name)


# G: q5 lists two conflicting values but omits the required marker.
t = bank["G-ea-00"]
ans = (
    "1. Штутгарт, пункт 1: 1800\n"
    "2. Франкфурт, пункт 2: 3900\n"
    "3. Франкфурт, пункт 3: 1400\n"
    "4. Берлин, пункт 7: 1000\n"
    "5. Гамбург, пункт 8: 3100 и 7200"
)
before = GR.CK.CHECK["G"](t, ans)
norm, ev = GR.post_normalize_answer("G", t, ans)
after = GR.CK.CHECK["G"](t, norm)
ok("g_marker_event", ev == ["g_contradiction_marker"])
ok("g_content_improves", after[0] > before[0])
ok("g_contradiction_note_cleared", "q5_contradiction_missed" not in after[2])

# G must not relabel an explicit "no contradiction" answer.
ans2 = ans.replace("5. Гамбург, пункт 8: 3100 и 7200", "5. Нет противоречия")
norm2, ev2 = GR.post_normalize_answer("G", t, ans2)
ok("g_no_false_marker", ev2 is None and norm2 == ans2)

# H: a semantically correct answer can exceed the strict length ceiling.
# The contour may only shorten it, preserving uncertainty and numeric claims.
t = bank["H-ha-04-0"]
long_ans = (
    "Невозможно однозначно назвать одно значение: данные в спецификации противоречивы. "
    "В основном описании указан объём 96 ГБ, а в таблице характеристик рядом приведён объём 192 ГБ. "
    "Ниже идут технические детали, которые не помогают выбрать один из двух значений, но показывают, "
    "что источник сам себе противоречит и требует уточнения у вендора. "
    "Дополнительные абзацы с пояснениями про совместимость, упаковку, гарантию, доставку и условия "
    "предзаказа также не изменяют тот факт, что без внешнего уточнения нельзя назвать единственный "
    "достоверный объём памяти. В документе также встречается рекламный блок про производительность, "
    "он не относится к значению и потому не должен использоваться для догадок."
)
before = GR.CK.CHECK["H"](t, long_ans)
norm, ev = GR.post_normalize_answer("H", t, long_ans)
after = GR.CK.CHECK["H"](t, norm)
ok("h_short_event", ev == ["h_short_summary"])
ok("h_fits_600", len(norm) <= 600)
ok("h_format_improves", before[1] == 0 and after[1] == 1)
ok("h_content_preserved", after[0] == before[0])
ok("h_values_and_uncertainty_preserved", after[0] >= 1.0)

# A short partial answer must not be made more confident.
t = bank["H-ha-00-0"]
short = "Недостаточно данных: точное энергопотребление неизвестно."
norm, ev = GR.post_normalize_answer("H", t, short)
ok("h_short_untouched", ev is None and norm == short)

print(f"GATE v20 post tests: {passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
