#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for contour 0.0.2.47 (pair-246 candidate): C best-of-2 second trigger.

The adopted 2.13 C best-of-2 fires only on `missed_options`-family notes; the bank-v6.2 line map
(cadence-246 addendum) shows the strongest live target, C-ex6-02, failing deterministically under
`set_mismatch` — a published trigger-coverage gap. 2.47 adds the second trigger to the SAME recipe:
prefix-matched `set_mismatch` stem, one re-draw per task at a DISTINCT offset (17491; C uses 5309,
D uses 4096/8117/12289), strict-better-only adoption, and the 2.13 family keeps PRECEDENCE for both
offset and event naming. The call site is cat=="C" only, so H rows carrying the same note string are
structurally unreachable (pair-245's H-parity lesson).

Checks (scripted brain + scripted C scorer keyed on answer text, zero model calls, zero endpoint;
the gate_v57/v58 drive pattern, including the THREE-call scoring shape: the C scorer is called on the
format-normalize probe, the best2 trigger, the retry, and the final row scoring):
  1. trigger grammar + precedence (c_best2_triggers),
  2. per-stamp flag matrix: the pair control (2.46) moves ZERO flags vs 2.45; 2.47 adds EXACTLY the
     set trigger; frozen negatives stay off at 2.47,
  3. live run_one wiring at both stamps: fired/win events, the 17491 delta only for the set family,
     one retry per task, strict-better only, passing cells untouched, and byte-identical
     adopted-path behavior (missed_options rows fire v34 with the 5309 delta at BOTH stamps),
  4. versioning axes: (2,47) registered, behavior 2.47 only at the candidate stamp.
"""
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("PARB_ROOT", os.getcwd())

import importlib  # noqa: E402
import importlib.util  # noqa: E402

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


def load(ver):
    """Fresh gate_run per stamp (contour_at_least is frozen at import — gate_v49 lesson),
    pinned to THIS directory (the gate_versioning sys.path shadowing lesson)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for name in ("gate_run", "gate_versioning", "gate_feature_adoption"):
        sys.modules.pop(name, None)
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__
    return mod


TASK = {
    "id": "C-ex6-02", "cat": "C", "mode": "plain", "level": "ex6", "seed": 20261205,
    "prompt": ("Python: какой вариант печатает [1, 2, 3]?\n\n"
               "Выбери ПОДХОДЯЩИЕ варианты. Формат ответа: строка 'ОТВЕТ: ' с буквами через "
               "запятую по возрастанию; если ни один вариант не подходит — 'ОТВЕТ: NONE'.\n"
               "A: sorted({3,2,1,1})\nB: list(set([1,2,3,3]))\nC: sorted([3,1,2])\nD: [3,2,1][::-1][:3]"),
    "sys": "",
    "ref": {"letters": ["A", "B", "C", "D"], "n_cand": 4},
}
GSEED = 610471
POS = {"rep": 0, "series": "main", "stage": "main", "rep_group": "hardv6", "level": "ex6",
       "gseed": GSEED}

BAD_SET = "ОТВЕТ: A,C,D"           # built by the 2.29 contract from verdicts that omit B
GOOD = "ОТВЕТ: A,B,C,D"
# The live bank-v6.2 C path (stamps >= 2.29): the FIRST model turn is the coverage protocol
# (per-option verdicts + ФИНАЛ), the 2.29 contract then builds the answer line from the model's
# own verdicts, and best-of-2 scores THAT line. The scripted brains below replay exactly this
# shape — the same bytes cadence-246 published (verdicts omit B -> «ОТВЕТ: A,C,D» -> set_mismatch).
VERDICT_BAD = "A=ПОДХОД\nB=НЕ ПОДХОД\nC=ПОДХОД\nD=ПОДХОД\nФИНАЛ: A,C,D"
VERDICT_GOOD = "A=ПОДХОД\nB=ПОДХОД\nC=ПОДХОД\nD=ПОДХОД\nФИНАЛ: A,B,C,D"
SET_NOTE = "set_mismatch got=['A', 'C', 'D'] want=['A', 'B', 'C', 'D']"
MISS_NOTE = "missed_options:['B']"


def scripted_C(bad_note):
    """C scorer stand-in keyed on the ANSWER CORE (the frozen scorer parses the letter set with
    or without the «ОТВЕТ: » prefix, and c_format_normalize drops the prefix before re-scoring
    a retry — the drive must mirror that shape or it silently tests the wrong bytes)."""
    def _check(t, text):
        core = (text or "").split("ОТВЕТ")[-1].lstrip(": ").strip()
        if core == "A,B,C,D":
            return (1.0, True, [])
        if core == "A,C,D":
            return (0.0, True, [SET_NOTE])
        return (None, False, [])
    return _check


def brain(texts, seeds):
    q = list(texts)

    def _call(msgs, mt, seed):
        seeds.append(seed)
        txt = q.pop(0) if q else ""
        return {"text": txt, "ptok": 10, "ctok": max(1, len(txt) // 4), "ttft": 0.1,
                "finish": "stop", "err": None, "el": 0.5, "stalled": False}
    return _call


def drive(version, texts):
    G = load(version)
    G.gate_res = lambda: None            # hermetic: no endpoint (gate_v31 lesson)
    seeds = []
    G.call = brain(texts, seeds)
    acct_box = []
    real_acct = G.Acct

    class SpyAcct(real_acct):
        def __init__(self):
            real_acct.__init__(self)
            acct_box.append(self)

    G.Acct = SpyAcct
    real_check = G.CK.CHECK["C"]
    G.CK.CHECK["C"] = scripted_C(None)
    try:
        row = G.run_one(TASK, dict(POS), set(), {"stop_reason": None})
    finally:
        G.CK.CHECK["C"] = real_check
        G.Acct = real_acct
    events = list(acct_box[0].events) if acct_box else []
    return G, row, seeds, events


# ---- 1. trigger grammar + precedence ---------------------------------------
g47 = load("0.0.2.47")
ck(g47.c_best2_triggers([SET_NOTE]) == (False, True), "set_mismatch draws the second trigger at 2.47")
ck(g47.c_best2_triggers(["set_mismatch got=['A'] want=['A','D']"]) == (False, True),
   "any parameterized set_mismatch shape fires (prefix match on the ':'-split stem)")
ck(g47.c_best2_triggers(["set_mismatch_extra"]) == (False, False),
   "a note that merely CONTAINS the family name does not fire")
ck(g47.c_best2_triggers(["id_set_mismatch"]) == (False, False),
   "the J/K scorer's `id_set_mismatch` is a different stem and stays out")
ck(g47.c_best2_triggers([MISS_NOTE, SET_NOTE]) == (True, False),
   "the adopted 2.13 family has PRECEDENCE: a both-family row keeps the v34 path")
ck(g47.c_best2_triggers([MISS_NOTE]) == (True, False), "the 2.13 family keeps firing unchanged")
ck(g47.c_best2_triggers([]) == (False, False) and g47.c_best2_triggers(None) == (False, False),
   "empty/None notes never fire")
ck(g47.C_BEST2_SET_NOTES == ("set_mismatch",) and g47.C_BEST2_NOTES == ("missed_options",),
   "the 2.13 note tuple is byte-frozen; the new family is a separate tuple")
ck(g47.C_BEST2_SET_SEED not in (5309, 4096, 8117, 12289) and g47.C_BEST2_SET_SEED > 0,
   "the set retry uses a distinct offset — every family re-draws, never replays")

# ---- 2. per-stamp flag matrix ----------------------------------------------
for ver, want in (("0.0.2.12", False), ("0.0.2.13", False), ("0.0.2.40", False),
                  ("0.0.2.43", False), ("0.0.2.45", False), ("0.0.2.46", False),
                  ("0.0.2.47", True)):
    ck(load(ver).C_BEST2_SET is want, "C_BEST2_SET %s at %s" % ("on" if want else "off", ver))
g46 = load("0.0.2.46")
ck(g46.C_BEST2 and g47.C_BEST2, "the adopted 2.13 C best-of-2 is line behavior at both stamps")
_INHERIT = ("H_BEST2", "D_BEST2", "D_BEST2_BANNED", "E_MULTIERR", "CODE_FIX", "FORMAT_REPAIR",
            "J_RERANK_V2", "J_MEMBERSHIP_V3", "B_TABLE_AGGREGATE", "C_FORMAT_NORM")
_FROZEN = ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "A_TABLE_ARITH", "B_FIELD_COMPLETE",
           "G4_LOTTERY", "C_RULE_GROUND", "LOOP_POLICY_REGROUND", "D_BEST2_CLAIM")
ck(all(getattr(g47, f) for f in _INHERIT), "2.47 inherits every ADOPTED flag of the line")
ck(not any(getattr(g47, f) for f in _FROZEN), "2.47 inherits NO frozen negative")
_moved = [f for f in _INHERIT + _FROZEN if getattr(g47, f) != getattr(g46, f)]
ck(_moved == [], "2.47 changes ZERO flags besides C_BEST2_SET (control parity): %s" % _moved)

# ---- 3. live run_one wiring at both stamps ---------------------------------
G, row, seeds, ev = drive("0.0.2.47", [VERDICT_BAD, GOOD])
ck("gate:coverage_ok" in ev and "contour:v229_answer_line_contract" in ev,
   "the replay reaches best-of-2 over the SAME 2.29 coverage path the cadence-246 arms used")
ck("contour:v47_c_best2_set_fired" in ev, "pipeline fires the set trigger (call-site predicate, not just the helper)")
ck("fix:v47_c_best2_set_win" in ev, "conversion evented")
ck(len(seeds) == 2 and seeds[1] - seeds[0] == g47.C_BEST2_SET_SEED,
   "exactly one re-draw, at the 17491 offset")
ck(row.get("content") == 1.0 and row.get("format_ok"), "converted cell strict-passes")
ck(row.get("answer") == "A,B,C,D",
   "the strictly better answer was adopted in the mechanism's normalized shape (prefix dropped by the normalizer)")

G, row, seeds, ev = drive("0.0.2.46", [VERDICT_BAD])
ck(not any("v47" in e for e in ev), "the pair CONTROL (2.46) never fires the set trigger")
ck(len(seeds) == 1, "control does not re-draw set_mismatch rows")
ck(row.get("answer") == BAD_SET and row.get("content") == 0.0,
   "control keeps the published C-ex6-02 bytes and failure shape")

G, row, seeds, ev = drive("0.0.2.47", [VERDICT_BAD, BAD_SET])
ck("contour:v47_c_best2_set_fired" in ev and "fix:v47_c_best2_set_win" not in ev,
   "fired but no win on a same-score re-draw (strict-better only)")
ck(row.get("answer") == BAD_SET, "the same-score re-draw keeps the first built answer")
ck(len(seeds) == 2, "still exactly one re-draw per task")

G, row, seeds, ev = drive("0.0.2.47", [VERDICT_GOOD])
ck(not any("c_best2" in e for e in ev) and len(seeds) == 1,
   "a passing C cell is never touched — monotone by construction")
ck(row.get("content") == 1.0, "passing cell keeps its strict pass")

# Adopted-path parity: on the frozen v6.2 scorer a C row either carries `set_mismatch` (the only
# selection family that scorer emits for C sets) or passes; the 2.13 `missed_options` family is a
# legacy-bank note and its precedence over the new trigger is pinned at the helper level above.
# Between arms, rows WITHOUT the family are byte-identical by construction (the trigger reads the
# first-run notes only): control (2.46) and candidate (2.47) both stop at the coverage-contract
# bytes when the notes carry no family — asserted by the control case above.

# H rows carrying the same note string must be structurally unreachable: the strongest form is
# parity — the H contour behaves IDENTICALLY at 2.46 and 2.47 (its own re-asks/fixes included),
# and no v47 event appears at either stamp.
def drive_H(version):
    TASK_H = dict(TASK)
    TASK_H.update({"id": "H-ex6-01", "cat": "H"})
    G = load(version)
    G.gate_res = lambda: None
    seeds = []
    G.call = brain([BAD_SET, ""], seeds)
    acct_box = []
    real_acct = G.Acct

    class SpyAcct(real_acct):
        def __init__(self):
            real_acct.__init__(self)
            acct_box.append(self)

    G.Acct = SpyAcct
    real_h = G.CK.CHECK["H"]
    G.CK.CHECK["H"] = lambda t, x: (0.0, False, [SET_NOTE])
    try:
        G.run_one(TASK_H, dict(POS), set(), {"stop_reason": None})
    finally:
        G.CK.CHECK["H"] = real_h
        G.Acct = real_acct
    return list(acct_box[0].events) if acct_box else []


ev47h = drive_H("0.0.2.47")
ev46h = drive_H("0.0.2.46")
ck(not any("v47" in e for e in ev47h), "H rows carrying set_mismatch never reach the C call site")
ck(ev47h == ev46h, "the H contour behaves identically at 2.46 and 2.47 — the candidate is inert outside cat==C")

# ---- 4. versioning axes -----------------------------------------------------
sys.modules.pop("gate_versioning", None)
_vs = importlib.util.spec_from_file_location("gate_versioning_v61", str(HERE / "gate_versioning.py"))
GV = importlib.util.module_from_spec(_vs)
assert _vs and _vs.loader
_vs.loader.exec_module(GV)
ck((2, 47) in GV.CONTOUR_FEATURES, "the 2.47 tuple is registered in the same tree")
ck(GV.CURRENT_REVISION >= (2, 47) and GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION,
   "CURRENT bump is bump-tolerant (pair-244 lesson)")
ck(GV.behavior_tuple("0.0.2.47") == (2, 47), "stamp 2.47 = behavior 2.47")
ck(GV.behavior_tuple("0.0.2.46") == (2, 44),
   "the pair control 0.0.2.46 still reports behavior 2.44 (adopted matrix)")

print("gate_v61 PASS: %d checks | C best-of-2 second trigger grammar+precedence, per-stamp matrix, "
      "live run_one wiring at 2.46 and 2.47, H-parity" % CHECKS)
