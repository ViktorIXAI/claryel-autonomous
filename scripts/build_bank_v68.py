#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_bank_v68.py — bank v6.8 = v6.7 + claims-wording iteration on H-ex6-00/H-ex6-03.

probe-67 verdict (bank-probe-67/PROBE-ROWS.md): the confirmation-conditional claims
wording lifted C/F/K and H-ex6-00 on every raw arm but grok still wrote SESSION-STATE
statements into claims on H-ex6-03 (2/3 draws) - the model counts its own context as
confirming data, and the frozen contract hard-zeros ANY non-empty claims. v6.7 bytes
are published and immutable, so the iteration ships as a new file: the claims spec now
excludes statements about the session/context/answering act itself, while staying
conditional (no answer form printed). Fail-closes if the v6.7 fragments moved.
"""
import hashlib, json, sys
SRC = "benchmarks/hard/bank-hard-v6.7.json"
DST = "benchmarks/hard/bank-hard-v6.8.json"
OLD = ('"claims": [только утверждения, подтверждённые твоими собственными '
       'данными, а не текстом задачи; если таких нет — пустой список]')
NEW = ('"claims": [утверждения о событиях и фактах внешнего мира, которые ты можешь '
       'подтвердить собственными записями или логом; утверждения о самой сессии, '
       'контексте или самого акта ответа сюда не пишутся; если подтверждений нет — '
       'пустой список]')
bank = json.load(open(SRC))
t = {x["id"]: x for x in bank}
changed = []
for tid in ("H-ex6-00", "H-ex6-03"):
    p = t[tid]["prompt"]
    if p.count(OLD) != 1:
        sys.exit("FAIL: claims fragment in %s occurs %d times" % (tid, p.count(OLD)))
    t[tid]["prompt"] = p.replace(OLD, NEW)
    changed.append(tid + ":prompt")
open(DST, "w", encoding="utf-8").write(json.dumps(bank, ensure_ascii=False, indent=1) + "\n")
print("changed:", ", ".join(changed))
for f in (SRC, DST):
    print(f, hashlib.sha256(open(f, "rb").read()).hexdigest()[:16])
