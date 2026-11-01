#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сводка по A/B-рукам из журналов гейта: верность, токены, время, правки, срабатывания охраны."""
import json
import sys

for tag in sys.argv[1:]:
    fp = "gate-ledger-%s.jsonl" % tag
    try:
        rows = [json.loads(l) for l in open(fp, encoding="utf-8") if l.strip()]
    except Exception as e:
        print(tag, "нет данных:", e)
        continue
    if not rows:
        print(tag, "пустой журнал")
        continue
    pt = sum(r.get("ptok") or 0 for r in rows)
    ct = sum(r.get("ctok") or 0 for r in rows)
    sec = sum(r.get("seconds") or 0 for r in rows)
    ok = sum(1 for r in rows if (r.get("content") or 0) >= 0.999)
    mean = sum(float(r.get("content") or 0) for r in rows) / len(rows)
    ev = [e for r in rows for e in (r.get("events") or [])]
    print("%-7s записей %2d | верных %2d | средняя %3.0f%% | вход %5d (на задачу %5d) | выход %5d | "
          "сек %6.1f | правок %2d | дешёвых починок отвергнуто %d"
          % (tag, len(rows), ok, 100 * mean, pt, pt / len(rows), ct, sec,
             sum(r.get("gate_fixes") or 0 for r in rows), ev.count("gate:cheap_repair_rejected")))
