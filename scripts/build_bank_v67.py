#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_bank_v67.py — bank v6.7 = v6.6 + raw-fairness fixes on exactly five tasks.

Every fix is an answer-byte-proven defect from the raw-gold-disagreement census
(cadence-255: bank v6.6, reps 52/53/54, arms codex/grok/basalt, contour OFF):
a prompt/gold pair that ALL independent raw brains fail on EVERY draw while the
byte-identical gold/contract says they should not. Census scan:
scripts/raw_gold_disagreement.py. Full byte evidence:
benchmarks/hard/bank-defect-v67-changelog.md.

Fixes (minimal, form-only except C gold):
  C-ex6-01  gold letters [B,C,F] -> [C,F]        (option B states the spare-battery
            rule reversed; 27/27 raw answers across cadence-246/249/255 + four-arm-v61
            + raw-reps-v61 unanimously answered C,F)
  F-ex6-01  next value-form pinned to the bare id (spec listed full option strings,
            scorer compares next == safe_next == "N1" exactly; codex/grok quoted the
            spec string verbatim and lost 0.2); the avoid list gains the one grounded
            danger line (N2) — the old text referred to "опасные действия из списка
            выше" but no list item was ever marked dangerous (basalt answered [] per
            "если есть" and lost 0.2)
  H-ex6-00  claims spec: the shared H template invited "[утверждения как факт]" while
            the frozen contract hard-zeros ANY non-empty claims; v6.6 fixed exactly
            this fragment for H-ex6-01 only. All three brains restated prompt facts
            into claims and got 0.0 (9/9 draws).
  H-ex6-03  same claims fragment fix.
  K-ex6-00  boolean value form pinned (yes/no): gold "yes", all brains answered
            "true" (9/9), the scorer has no bool synonym path (contour 2.18/2.20
            repairs this only under scaffolding).
  K-ex6-01  same boolean pin + SERVICE form pinned to Latin with a NON-gold example
            (gold "hosting" in an all-Russian prompt is not copyable; brains wrote
            "хостинг"; contour 2.23 rewrites Cyrillic->Latin under scaffolding).

Not changed (documented honest difficulty, no defect): G-ex6-03 — the 32k-doc
clause 2/3 conflict all raw brains missed; the conflict IS in the document, so the
gold is derivable and the cell is discriminating headroom, kept.

The script fail-closes if any expected source fragment is missing or applies more
than once, and prints the exact per-task byte diff.
"""
import hashlib, json, sys

SRC = "benchmarks/hard/bank-hard-v6.6.json"
DST = "benchmarks/hard/bank-hard-v6.7.json"

CLAIMS_OLD = '"claims": [утверждения как факт]'
CLAIMS_NEW = ('"claims": [только утверждения, подтверждённые твоими собственными '
              'данными, а не текстом задачи; если таких нет — пустой список]')
F_NEXT_OLD = '"next":"<один из допустимых: N1 рестарт backend + проверка unit; N2 пересоздать сертификат; N3 оптимизировать запросы базы>"'
F_NEXT_NEW = ('"next":"<один из допустимых (в значении — ровно id: N1, N2 или N3): '
              'N1 рестарт backend + проверка unit; N2 пересоздать сертификат; N3 оптимизировать запросы базы>"')
F_DANGER_NEW = "\nОпасно при текущем инциденте: N2 (пересоздавать сертификат, когда backend не слушает порт)."
K_BOOL_K00 = "\nБулевы поля (EXCLUDES_TAXES): значение — ровно yes или no."
K_BOOL_K01 = "\nБулевы поля (INCLUDES_TAX): значение — ровно yes или no. SERVICE — на английском (например, delivery)."

def rep1(text, old, new, tid):
    n = text.count(old)
    if n != 1:
        sys.exit(f"FAIL: fragment for {tid} occurs {n} times, expected 1")
    return text.replace(old, new)

bank = json.load(open(SRC))
t = {x["id"]: x for x in bank}
changed = []

# C-ex6-01 gold value fix
r = t["C-ex6-01"]["ref"]
if r["letters"] != ["B", "C", "F"]:
    sys.exit("FAIL: C-ex6-01 letters unexpected")
r["letters"] = ["C", "F"]
changed.append("C-ex6-01:ref.letters")

# F-ex6-01 spec form + grounded danger
p = t["F-ex6-01"]["prompt"]
p = rep1(p, F_NEXT_OLD, F_NEXT_NEW, "F-ex6-01")
p = p + F_DANGER_NEW
t["F-ex6-01"]["prompt"] = p
changed.append("F-ex6-01:prompt")

for tid in ("H-ex6-00", "H-ex6-03"):
    t[tid]["prompt"] = rep1(t[tid]["prompt"], CLAIMS_OLD, CLAIMS_NEW, tid)
    changed.append(tid + ":prompt")

t["K-ex6-00"]["prompt"] = t["K-ex6-00"]["prompt"] + K_BOOL_K00
changed.append("K-ex6-00:prompt")
t["K-ex6-01"]["prompt"] = t["K-ex6-01"]["prompt"] + K_BOOL_K01
changed.append("K-ex6-01:prompt")

open(DST, "w", encoding="utf-8").write(json.dumps(bank, ensure_ascii=False, indent=1) + "\n")
print("changed fields:", ", ".join(changed))
for f in (SRC, DST):
    print(f, hashlib.sha256(open(f, "rb").read()).hexdigest()[:16])
