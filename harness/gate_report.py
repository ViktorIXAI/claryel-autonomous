#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сравнение базовой серии PARB и серии с верификационным контуром.

Базовая: ~/.hermes/bench/parb/results.jsonl (run_tag != 'gate', series main)
Контур:  ~/.hermes/bench/parb/results-gate.jsonl + gate-ledger.jsonl (тянем с B2003)

Отчёт: по категориям — доля полностью принятых ответов до и после контура, и цена
в секундах/токенах/потерянных токенах в секунду. Никаких евро: только время и токены.
"""
import json
import os
import statistics as st
import sys
from collections import defaultdict

ROOT = os.path.expanduser("~/.hermes/bench/parb")
CATNAME = {"A": "финансовые расчёты", "B": "извлечение данных", "C": "логика и ограничения",
           "D": "агентное планирование", "E": "программирование", "F": "системное администрирование",
           "G": "поиск в длинном контексте", "H": "галлюцинации", "I": "защита от инъекций",
           "J": "надёжность формата", "K": "многоязычные задачи"}


def load(path, gate=None):
    out = []
    if not os.path.exists(path):
        return out
    for ln in open(path, encoding="utf-8"):
        try:
            r = json.loads(ln)
        except Exception:
            continue
        if r.get("series") != "main":
            continue
        if gate is True and r.get("run_tag") != "gate":
            continue
        if gate is False and r.get("run_tag") == "gate":
            continue
        out.append(r)
    return out


def acc(rows):
    g = defaultdict(lambda: [0, 0, 0, 0, []])   # принято, всего, формат, обрезано, секунды
    for r in rows:
        c = r["cat"]
        cval = r.get("content")
        full = 1 if (cval is not None and cval >= 0.999) else 0
        g[c][0] += full
        g[c][1] += 1
        g[c][2] += 1 if r.get("format_ok") else 0
        g[c][3] += 1 if r.get("truncated") else 0
        if r.get("total_s"):
            g[c][4].append(r["total_s"])
    return g


def main():
    base = load(os.path.join(ROOT, "results.jsonl"), gate=False)
    gate = load(os.path.join(ROOT, "results-gate.jsonl"), gate=True)
    led = []
    lp = os.path.join(ROOT, "gate-ledger.jsonl")
    if os.path.exists(lp):
        led = [json.loads(l) for l in open(lp, encoding="utf-8")]
    if not gate:
        print("серия с контуром ещё не собрана (results-gate.jsonl отсутствует)")
        return 1
    A, B = acc(gate), acc(base)
    lg = defaultdict(list)
    for r in led:
        lg[r["task"].split("-")[0]].append(r)

    print("%-4s %-30s %10s %10s %8s | %8s %8s %9s %9s" % (
        "кат", "категория", "базовая", "контур", "сдвиг", "сек баз", "сек конт", "ток/с эфф", "потеря %"))
    for c in sorted(set(list(A) + list(B))):
        b = B.get(c, [0, 0, 0, 0, []])
        a = A.get(c, [0, 0, 0, 0, []])
        bs = (b[0] / b[1] * 100) if b[1] else None
        as_ = (a[0] / a[1] * 100) if a[1] else None
        rows = lg.get(c, [])
        raw = [x["decode_tps_raw"] for x in rows if x.get("decode_tps_raw")]
        eff = [x["decode_tps_effective"] for x in rows if x.get("decode_tps_effective")]
        secs = [x["seconds"] for x in rows if x.get("seconds")]
        print("%-4s %-30s %9s %9s %8s | %8s %8s %9s %9s" % (
            c, CATNAME.get(c, c),
            ("%.0f%%" % bs) if bs is not None else "—",
            ("%.0f%%" % as_) if as_ is not None else "—",
            ("%+.0f п.п." % (as_ - bs)) if (bs is not None and as_ is not None) else "—",
            ("%.1f" % st.mean(b[4])) if b[4] else "—",
            ("%.1f" % st.mean(secs)) if secs else ("%.1f" % st.mean(a[4]) if a[4] else "—"),
            ("%.0f" % st.mean(eff)) if eff else "—",
            ("%.0f" % (100 - 100 * st.mean(eff) / st.mean(raw))) if (eff and raw) else "—"))

    print("\nвсего: базовая %d записей, контур %d записей, бухгалтерия %d строк" % (len(B), len(A), len(led)))
    if led:
        calls = sum(x["model_calls"] for x in led)
        fixes = sum(x["gate_fixes"] for x in led)
        blocks = sum(x["gate_blocks"] for x in led)
        lad = sum(x["ladder_steps"] for x in led)
        secs = sum(x["seconds"] for x in led)
        ctok = sum(x["ctok"] for x in led)
        utok = sum(x["useful_tokens"] for x in led)
        print("работа контура: вызовов модели %d (переспросов %d, блокировок шага %d, подъёмов лимита %d)" % (
            calls, fixes, blocks, lad))
        print("время модели %d с, токенов %d, из них принято %d (переработка %d токенов, %d%%)" % (
            secs, ctok, utok, ctok - utok, round(100 * (ctok - utok) / max(ctok, 1))))
        ev = defaultdict(int)
        for x in led:
            for e in x.get("events") or []:
                ev[e.split(":")[0] + "_" + e.split(":")[1].split("_")[0]] += 1
        top = sorted(ev.items(), key=lambda kv: -kv[1])[:12]
        print("частые события контура:", ", ".join("%s×%d" % kv for kv in top))
    return 0


if __name__ == "__main__":
    sys.exit(main())
