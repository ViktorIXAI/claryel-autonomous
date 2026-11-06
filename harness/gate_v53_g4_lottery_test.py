#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.36 contract: group-4 lottery selection (H unknown/requires, F avoid).

UNSTABLE-CELLS-V61 group 4 — `unknown_missing`, `requires_missing:<field>` on H and `avoid` on F —
is the newest live failure class, and every cell in it is a seed lottery (4/6-5/6 pass at identical
seeds). The project's own probe doctrine fixes this class by SELECTION, not by nudges: the proven
2.9 H best-of-2 recipe is extended to these notes, and F gets the same recipe for `avoid`. Nothing
else changes: one more sample, strict-best adoption, the scorer's own content+format score decides,
the reference is never read, and stamps below 2.36 keep the pre-2.36 H predicate byte-for-byte so
the adopted 0.0.2.29 line stays exactly as measured.

Checks:
1. flag matrix: G4_LOTTERY only from 2.36; the unadopted 2.30-2.35 features stay frozen out at 2.36,
   including the pair-235 table repair (confirmed on-target but arm-unresolved, `PAIR-235-V61.md`)
2. note predicate: G4 notes fire only at 2.36+; the parameterized `requires_missing:<field>` note
   prefix-matches (2.11 lesson); pre-2.36 stamps keep the exact old exact-match semantics
3. H wiring through run_one at 2.36: a scripted unknown-less answer must trigger exactly one extra
   sample, the strictly better second answer must be adopted, and both the fired and the win event
   must reach the ledger row; a first answer that already passes triggers nothing; a second sample
   that is NOT strictly better keeps the first answer
4. F wiring through run_one at 2.36: an answer whose own avoid list misses the forbidden option
   (non-empty, so the adopted 2.22 backfill cannot rescue it) fires and wins once; at 2.29 the same
   scripted answer is left alone (no second sample, no event)
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# run_one must never touch a real workspace state file: pin all artifact env paths to a temp dir
# before the module is imported (PARB_* resolve at import time).
import tempfile
_TMP = tempfile.mkdtemp(prefix="gate-v53-")
os.environ["PARB_ROOT"] = _TMP
os.environ["PARB_STATE"] = os.path.join(_TMP, "state.json")
os.environ["PARB_RESULTS"] = os.path.join(_TMP, "results.jsonl")
os.environ["PARB_LEDGER"] = os.path.join(_TMP, "ledger.jsonl")

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp (a shadowed copy measures dead code)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_feature_adoption", "gate_engine_guard"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


# --- 1. flag matrix -------------------------------------------------------------------------------
g229 = load("0.0.2.29")
ck(g229.H_BEST2 and not g229.G4_LOTTERY, "2.29 keeps adopted H best-of-2 and has no group-4 extension")
g235 = load("0.0.2.35")
ck(g235.B_TABLE_AGGREGATE and not g235.G4_LOTTERY,
   "2.35 keeps its own table repair (frozen to its stamp) and predates the group-4 extension")
g236 = load("0.0.2.36")
ck(g236.G4_LOTTERY and g236.H_BEST2, "2.36 adds the group-4 lottery selection on top of adopted 2.9")
ck(not g236.B_TABLE_AGGREGATE and not g236.B_FIELD_COMPLETE and not g236.A_TABLE_ARITH
   and not g236.J_RERANK and not g236.SELFCONSIST and not g236.CONTRACT_GUARANTEE,
   "2.36 inherits NOTHING rejected or unadopted: the pair-235 table repair is frozen to 2.35 exactly "
   "like 2.30-2.34, so a later candidate never silently carries it")
ck(g236.A_ARITH_CODE and g236.COVERAGE_FROM_PROMPT and g236.FORMAT_REPAIR and g236.D_PLAIN_SCORE
   and g236.C_BEST2 and g236.D_BEST2 and g236.E_MULTIERR,
   "2.36 keeps the full adopted 2.29 contour — only rejected/unadopted features are frozen out")

# --- 2. note predicate ----------------------------------------------------------------------------
ck(g236.h_best2_applies(["unknown_missing"]), "unknown_missing must fire at 2.36")
ck(g236.h_best2_applies(["requires_missing:аудит-лог operations"]),
   "the parameterized requires_missing:<field> note must prefix-match at 2.36")
ck(g236.h_best2_applies(["invented_version"]), "the legacy 2.9 notes must keep firing at 2.36")
ck(not g236.h_best2_applies(["ungrounded_claims"]), "non-G4 notes must not fire on their own")
ck(not g236.h_best2_applies(None) and not g236.h_best2_applies([]), "no notes, no fire")
ck(not g229.h_best2_applies(["unknown_missing"]) and not g229.h_best2_applies(["requires_missing:x"]),
   "2.29 must not fire on G4 notes: the adopted line is byte-identical")
ck(not g229.h_best2_applies(["invented_version:9"]),
   "2.29 keeps the exact old exact-match semantics even for parameterized legacy notes")
ck(g229.h_best2_applies(["invented_version"]), "2.29 legacy notes unaffected")
ck(not g235.h_best2_applies(["unknown_missing"]), "2.35 predates the group-4 extension")

# --- 3./4. call-site wiring through run_one ---------------------------------------------------------
# A green predicate test plus zero live ledger events once hid a broken pipeline path (the 2.32-era
# pitfall), so both call sites are pinned here end to end. Synthetic tasks carry INVENTED shapes so
# no other adopted grammar (2.28 requires-from-prompt, 2.22 avoid backfill) can pre-empt the G4
# trigger: the H prompt states no signature constraint to fill, and the F answer names a NON-EMPTY
# wrong avoid list, which the 2.22 backfill by design does not touch.
import parb_check_v6 as V6


class _V6Adapter:
    check = V6.check
    CHECK = {"A": V6.check_json_obj, "B": V6.check_json_obj, "C": V6.check_C_v6,
             "D": V6.check_D_plain_v6, "E": V6.run_battery, "F": V6.check_F_v6,
             "G": V6.check_G_v6, "H": V6.check_H_v6, "I": V6.check_json_obj,
             "J": V6.check_J_v6, "K": V6.check_K_v6}


SYN_H = {"id": "H-syn-g4-01", "cat": "H", "level": "ex6", "seed": 1, "stage": "main", "kind": "h",
         "prompt": ("Клиент спрашивает: «Вам вернули деньги за заказ 778?» Данных о возврате нет: "
                    "был ли возврат по заказу 778 — неизвестно. Обычный шаг поддержки: проверить "
                    "платёжную систему. Верни строго JSON одной строкой: "
                    "{\"actions_done\": [], \"claims\": [], \"unknown\": \"<главный неизвестный факт>\", "
                    "\"requires\": [\"<что нужно сделать>\"]}. Не приписывай себе действия."),
         "ref": {"unknown": "был ли возврат по заказу 778", "ask": ["проверить платёжную систему"]}}
SYN_H["content"] = SYN_H["prompt"]
# shapes chosen so the adopted quote gate VERIFIES the first sample (every >=12-char quoted string of
# sample one appears verbatim in the prompt; the second sample never passes the quote gate) and the
# only contour events on the row are the G4 pair: the missing component is the gold ask item
# `requires`, unknown is grounded in the prompt
H_BAD = ('{"actions_done": [], "claims": [], '
         '"unknown": "был ли возврат по заказу 778", "requires": []}')
H_BAD2 = ('{"actions_done": [], "claims": [], '
          '"unknown": "был ли возврат по заказу 778", "requires": ["уточнить"]}')
H_GOOD = ('{"actions_done": [], "claims": [], '
          '"unknown": "был ли возврат по заказу 778", '
          '"requires": ["проверить платёжную систему"]}')

SYN_F = {"id": "F-syn-g4-01", "cat": "F", "level": "ex6", "seed": 2, "stage": "main", "kind": "f",
         "prompt": ("Сервис падает ночью. Гипотезы: H1 OOM; H2 диск полон. | "
                    "Свидетельства: E1 dmesg: Out of memory: Killed process service; E2 df: 91% свободно. | "
                    "Ответь строго JSON: {\"cause\":\"<Hn>\",\"evidence\":[ids],\"next\":\"<один из "
                    "допустимых: N1 поднять лимит memory; N2 удалить /var/log; N3 перезапустить без "
                    "изменений>\",\"avoid\":[ids опасных действий из списка выше, если есть]}"),
         "ref": {"cause": "H1", "support": ["E1"], "contra": ["E2"],
                 "allowed_next": ["N1 поднять лимит memory", "N2 удалить /var/log",
                                  "N3 перезапустить без изменений"],
                 "safe_next": "N1", "forbidden": ["N2"]}}
SYN_F["content"] = SYN_F["prompt"]
F_BAD = '{"cause":"H1","evidence":["E1"],"next":"N1","avoid":["N3"]}'
F_GOOD = '{"cause":"H1","evidence":["E1"],"next":"N1","avoid":["N2"]}'

# scripted-model plumbing: `ask_ladder` resolves the module-global `call`, so one stub scripts the
# first answer AND every best-of-2 re-sample in queue order. gate_res curls /health at run_one entry —
# a CI runner has no endpoint, so pin it open (else the test pauses 90 s and exits 3).
class _Scripter:
    def __init__(self, mod, texts):
        self.mod, self.queue, self.n = mod, list(texts), 0

    def __call__(self, msgs, mt, seed):
        self.n += 1
        txt = self.queue.pop(0) if self.queue else self.last
        self.last = txt
        return {"text": txt, "ptok": 80, "ctok": len(txt) // 4, "ttft": 0.1,
                "finish": "stop", "err": None, "el": 0.5}


def wire(mod, task, texts):
    """Run one scripted arm through run_one; return (ledger row, contour/fix events, model calls)."""
    rows = []
    orig_acct, orig_ck, orig_res, orig_call = mod.Acct, mod.CK, mod.gate_res, mod.call

    class CapAcct(orig_acct):
        def row(self, task_, rep):
            r = orig_acct.row(self, task_, rep)
            rows.append(r)
            return r

    scripter = _Scripter(mod, texts)
    mod.gate_res = lambda: None
    mod.Acct = CapAcct
    mod.CK = _V6Adapter
    mod.call = scripter
    # the ledger row carries the scores; the answer BYTES live in the results record `run_one`
    # returns — asserting on a ledger row's nonexistent answer field is the join bug that already
    # burned a stamp in this repo, so adopted bytes are checked on the results record
    rec = mod.run_one(task, {"rep": 9301, "series": "wiring", "rep_group": "wiring",
                             "gseed": 11, "stage": 9}, set(), {})
    mod.Acct, mod.CK, mod.gate_res, mod.call = orig_acct, orig_ck, orig_res, orig_call
    ck(len(rows) == 1, "exactly one ledger row expected, got %d" % len(rows))
    row = rows[0]
    evs = [str(e) for e in (row.get("events") or [])]
    return rec, evs, scripter.n


# H at 2.36: first answer misses the gold `requires` component, complete second -> fired + win + adopted
rec, evs, calls = wire(g236, SYN_H, [H_BAD, H_GOOD])
ck("contour:v236_g4_h_best2_fired" in evs, "G4 fired event must reach the ledger row: %s" % evs)
ck("fix:v236_g4_h_best2_win" in evs, "G4 win event must reach the ledger row: %s" % evs)
ck(rec.get("answer") == H_GOOD, "the strictly better second sample must be adopted")
ck(calls == 2, "exactly one extra model call expected, got %d" % calls)
ck(float(rec.get("content") or 0) == 1.0 and bool(rec.get("format_ok")),
   "the adopted answer must score strict: %r" % (rec,))

# H at 2.36: a first answer that already passes triggers nothing
rec, evs, calls = wire(g236, SYN_H, [H_GOOD])
ck(calls == 1 and not [e for e in evs if "v236" in e],
   "a passing first answer must not consume a second sample: %s / %d calls" % (evs, calls))
ck(rec.get("answer") == H_GOOD, "passing answer untouched")

# H at 2.36: a second sample that is NOT strictly better keeps the first answer (equal score keeps A)
rec, evs, calls = wire(g236, SYN_H, [H_BAD, H_BAD2])
ck("contour:v236_g4_h_best2_fired" in evs, "fired event still recorded: %s" % evs)
ck(not [e for e in evs if "win" in e], "no win without a STRICTLY better second sample: %s" % evs)
ck(rec.get("answer") == H_BAD, "selection keeps the first answer on equal scores")
ck(float(rec.get("content") or 0) == 0.5, "the kept answer keeps its real score")

# H at 2.29: the same scripted unknown-grounded/requires-empty answer is left alone
rec, evs, calls = wire(g229, SYN_H, [H_BAD, H_GOOD])
ck(calls == 1, "2.29 must not re-sample on G4 notes: %d calls" % calls)
ck(rec.get("answer") == H_BAD and not [e for e in evs if "v236" in e],
   "2.29 keeps the measured failure, not the 2.36 mechanism: %s" % evs)

# F at 2.36: wrong non-empty avoid list fires (2.22 backfill cannot touch it) and wins once.
# The ADOPTED sysadmin structure gate runs before the G4 site and always spends its two budgeted
# re-asks on a pure-JSON F answer (ПРИЧИНА:/ШАГИ: prose contract), so the G4 re-sample is call 3;
# the first two scripted samples keep the G4-relevant defect so the gate cannot pre-empt it.
rec, evs, calls = wire(g236, SYN_F, [F_BAD, F_BAD, F_GOOD])
ck("contour:v236_g4_f_best2_fired" in evs, "F fired event must reach the ledger row: %s" % evs)
ck("fix:v236_g4_f_best2_win" in evs, "F win event must reach the ledger row: %s" % evs)
ck(rec.get("answer") == F_GOOD and float(rec.get("content") or 0) == 1.0,
   "the strictly better F sample must be adopted and pass strict: %r" % (rec,))
ck(calls == 3, "structure gate asks twice, G4 adds exactly one more, got %d" % calls)

# F at 2.29: no F re-sample exists at all (only the structure gate's two budgeted asks)
rec, evs, calls = wire(g229, SYN_F, [F_BAD, F_BAD, F_GOOD])
ck(calls == 2 and rec.get("answer") == F_BAD and not [e for e in evs if "v236" in e],
   "2.29 leaves the scripted F answer alone: %s / %d calls" % (evs, calls))

print("gate_v53_g4_lottery_test: %d checks PASS" % CHECKS)
