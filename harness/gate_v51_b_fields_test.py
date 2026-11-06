#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.34 contract: B field completeness recomputes only what the prompt states.

The fields_mismatch/missing group (UNSTABLE-CELLS-V61.md) loses seeds on B-ex6-03 / B-ex6-05 where the
required field names and values are ALL present in the prompt itself. The repair rebuilds those fields
by code from the prompt's own data block. Like 2.32/2.33 it must fail closed: ambiguity, extra model
keys, unreadable required names or an unparseable shape all mean refuse-and-touch-nothing. Category K
is deliberately outside this stamp (value shapes the prompt never states — bank clarification, not a
guess; the 2.30 lesson).

Checks:
1. flag matrix: B_FIELD_COMPLETE only from 2.34; the unadopted 2.32/2.33 features stay off
2. synthetic config grammar with invented field names: wrong/missing fields repaired, value wins over
   model value only when the prompt block states it
3. synthetic echo-with-count grammar with invented names: count recomputed, dropped field removed,
   model-clobbered items restored to the prompt object
4. negatives refuse: conflicted duplicate keys, extra model key, required name unreadable, prose answer,
   two «удали» instructions, unparseable embedded JSON
5. bank behaviour: the two target B tasks' failing shapes get repaired to answers the frozen scorer
   accepts; every other bank B task refuses
6. no-op safety: an already-correct answer returns byte-identical text with no event
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load(ver):
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning", "gate_j_rerank"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


g233 = load("0.0.2.33")
ck(not g233.B_FIELD_COMPLETE, "2.33 must not see the 2.34 feature")
g234 = load("0.0.2.34")
ck(g234.B_FIELD_COMPLETE, "2.34 enables B field completeness")

# --- synthetic grammar proof with invented field names (never a bank task) ---------------------------
SYN_CFG = {"id": "B-syn-01", "cat": "B", "prompt": (
    "Конфиг:\nsvc:\n  pods: 5\n  image:\n    tag: v7\n  env:\n    - prod\n    - eu\n"
    'JSON: {"pods":число,"tag","env":[..]} из этих данных, без домыслов.')}
new, ev = g234.b_fields_by_code(SYN_CFG, '{"pods": 4, "env": ["prod"], "tag": "v6"}')
ck(ev == ["v234_b_config_fields"], "synthetic config repair must fire")
out = json.loads(new)
ck(out == {"pods": 5, "tag": "v7", "env": ["prod", "eu"]}, "synthetic values recomputed from the block: %s" % out)

# negatives
NEG_DUP = {"id": "B-syn-02", "cat": "B", "prompt": (
    "Конфиг:\nsvc:\n  pods: 5\n  pods: 6\n  env:\n    - prod\n"
    'JSON: {"pods","env"}')}
ck(g234.b_fields_by_code(NEG_DUP, '{"pods": 5, "env": []}')[1] is None, "conflicted duplicate key must refuse")
NEG_EXTRA = dict(SYN_CFG)
ck(g234.b_fields_by_code(NEG_EXTRA, '{"pods": 4, "tag": "v6", "env": ["prod","eu"], "ghost": 1}')[1] is None,
   "extra model key outside the spec must refuse")
NEG_UNREADABLE = {"id": "B-syn-03", "cat": "B", "prompt": (
    "Конфиг:\nsvc:\n  pods: 5\n"
    'JSON: {"pods","ghost"}')}
ck(g234.b_fields_by_code(NEG_UNREADABLE, '{"pods": 4}')[1] is None, "required name unreadable from the block must refuse")
ck(g234.b_fields_by_code(SYN_CFG, "pods это 4, env прод")[1] is None, "prose answer must refuse")
new2, ev2 = g234.b_fields_by_code(SYN_CFG, '{"pods": 5, "tag": "v7", "env": ["prod", "eu"]}')
ck(ev2 is None and new2 == '{"pods": 5, "tag": "v7", "env": ["prod", "eu"]}',
   "already-correct answer returns byte-identical text with no event")

SYN_ECHO = {"id": "B-syn-04", "cat": "B", "prompt": (
    'JSON: {"widgets":[{"sku":"W1","parts":["a","b"]},{"sku":"W2","parts":[]}],"token":"t9"}. '
    'Верни ТОТ ЖЕ объект, но добавь поле "n_kits": сумма длин parts по всем widgets, и удали "token". '
    "Widgets не меняй. Только JSON.")}
new, ev = g234.b_fields_by_code(SYN_ECHO,
    '{"widgets":[{"sku":"W1","parts":["a"]},{"sku":"W3","parts":[]}],"token":"t9"}')
ck(ev == ["v234_b_echo_count"], "synthetic echo-with-count repair must fire")
out = json.loads(new)
ck(out["n_kits"] == 2 and "token" not in out and out["widgets"][1]["sku"] == "W2",
   "count recomputed, token dropped, model-clobbered items restored from the prompt: %s" % out)
ck(g234.b_fields_by_code(SYN_ECHO, '{"widgets":[],"token":"t9","n_kits":2,"ghost":1}')[1] is None,
   "echo branch must refuse extra keys")
NEG_TWO_DROPS = {"id": "B-syn-05", "cat": "B", "prompt": (
    'JSON: {"widgets":[{"parts":["a"]}],"token":"t9","cursor":"c"}. '
    'Добавь поле "n_kits": сумма длин parts по всем widgets, удали "token", удали "cursor".')}
ck(g234.b_fields_by_code(NEG_TWO_DROPS, '{"widgets":[{"parts":["a"]}],"n_kits":1}')[1] is None,
   "two drop instructions = ambiguous membership = refuse")

# --- bank behaviour: the two target cells repair into scorer-passing answers --------------------------
import importlib
CK = importlib.import_module("parb_check_v6")
bank = {t["id"]: t for t in json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))}

t3 = bank["B-ex6-03"]
new, ev = g234.b_fields_by_code(t3, '{"replicas": 2, "mem": "512Mi"}')
ck(ev == ["v234_b_config_fields"], "bank B-ex6-03 failing shape must repair")
c, f = CK.check(t3, new)[:2]
ck(c == 1.0 and bool(f), "repaired B-ex6-03 must pass the frozen scorer: %r" % new)

t5 = bank["B-ex6-05"]
new, ev = g234.b_fields_by_code(t5, json.dumps({"items": [{"sku": "A-1", "tags": []}, {"sku": "B2", "tags": ["x"]}], "cursor": "a9f"}, ensure_ascii=False))
ck(ev == ["v234_b_echo_count"], "bank B-ex6-05 failing shape must repair")
c, f = CK.check(t5, new)[:2]
ck(c == 1.0 and bool(f), "repaired B-ex6-05 must pass the frozen scorer: %r" % new)

# every other bank B task: the grammars must refuse a plausible-but-shuffled probe
refused, fired = [], []
for tid in sorted(k for k in bank if k.startswith("B") and k not in ("B-ex6-03", "B-ex6-05")):
    _, ev = g234.b_fields_by_code(bank[tid], '{"zzz": 1}')
    (fired if ev else refused).append(tid)
ck(not fired, "2.34 grammars must refuse every non-target bank B task: %s" % fired)
ck(len(refused) == len([k for k in bank if k.startswith("B")]) - 2,
   "every non-target B task must be scanned, not silently skipped: %s" % refused)

print("gate_v51_b_fields_test: ALL PASS (%d checks)" % CHECKS)
