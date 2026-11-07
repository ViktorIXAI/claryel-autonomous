#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.51 contract: the B ECHO grammar re-arms, and ONLY the echo grammar.

Pair-234 froze `B_FIELD_COMPLETE` to exactly (2,34) UNMEASURED: that revision's echo guard refused
any answer adding the declared count key, so all three candidate seeds fired ZERO times — a pair
with no live target. The guard was extended right after (drop-names + count-key tolerance), and on
the ADOPTED line (bank v6.2, behavior 2.48, arms t48r22/23/24) the class is live: B-ex6-05
strict-fails 2/3 seeds, every zero the same single mode — the model copies `items` but injects its
own per-item `n_tags`, violating the prompt's «Items не меняй», scored `fields_mismatch:items`.

0.0.2.51 re-arms ONLY the echo path under a NEW flag `B_ECHO_RESTORE = STAMP_REVISION >= (2, 51)`:
the answer is rebuilt from the prompt's own JSON literal (items verbatim, count recomputed, drop
applied), zero model tokens, the reference is never read, and every uncertain step refuses.
The config-fields grammar stays frozen to exactly (2,34).

Checks:
1. per-stamp flag matrix: 2.50 moves ZERO flags vs the adopted 2.48; 2.51 = the 2.50 matrix +
   exactly B_ECHO_RESTORE; 2.35/2.44/2.50 run NEITHER B grammar; 2.34 keeps its own
   B_FIELD_COMPLETE without the 2.51 flag (history bytes not rewritten)
2. call-site predicate `(B_FIELD_COMPLETE or B_ECHO_RESTORE)` per stamp (the 2.17 unbundling lesson)
3. the repair on real bank-v6.2 B-ex6-05 bytes: the published failure shape (per-item n_tags) is
   restored to the prompt literal; an already-equal answer is NOT rewritten (zero fires on passes)
4. every refusal branch: grammar absent, two drops, unparseable literal, items not a list, an item
   missing the length field, a non-dict answer, an invented top-level key
5. the grammar is not bank-specific: it fires on a synthetic prompt with invented field names and
   restores THAT literal
6. coverage census: over all 77 bank-v6.2 prompts `_B_ECHO_RE` matches EXACTLY {B-ex6-05}
7. event naming history: 2.34 bytes emit v234_b_echo_count, 2.51+ emit v51_b_echo_restore
"""
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp (module path pinned)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_engine_guard"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    ck(mod.__file__.startswith(str(HERE)), "shadowed contour copy: %s" % mod.__file__)
    return mod


bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.2.json"),
                      encoding="utf-8"))
if isinstance(bank, dict):
    bank = bank.get("tasks", bank)
b05 = [t for t in bank if t["id"] == "B-ex6-05"][0]

# The published failure shape (t48r22 / t48r24 mode, redacted from the arm answer rows): the model
# adds its own per-item n_tags while keeping the top-level shape.
BAD_ANSWER = json.dumps({
    "items": [
        {"sku": "A-1", "tags": ["хрупкое"], "n_tags": 1},
        {"sku": "B2", "tags": [], "n_tags": 0},
    ],
    "n_tags": 1,
}, ensure_ascii=False)
GOOD_ANSWER = json.dumps({
    "items": [
        {"sku": "A-1", "tags": ["хрупкое"]},
        {"sku": "B2", "tags": []},
    ],
    "n_tags": 1,
}, ensure_ascii=False)

# ---------------------------------------------------------------- matrix
FLAGS = ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "J_RERANK_V2", "A_TABLE_ARITH",
         "B_FIELD_COMPLETE", "B_TABLE_AGGREGATE", "G4_LOTTERY", "J_MEMBERSHIP_V3",
         "C_RULE_GROUND", "LOOP_POLICY_REGROUND", "D_BEST2_BANNED", "D_BEST2_CLAIM",
         "D_BEST2", "H_BEST2", "C_BEST2", "C_BEST2_SET", "E_MULTIERR", "CODE_FIX",
         "FORMAT_REPAIR", "K_FIELDS_ENUM", "B_ECHO_RESTORE")

g234 = load("0.0.2.34")
g235 = load("0.0.2.35")
g248 = load("0.0.2.48")
g250 = load("0.0.2.50")
g251 = load("0.0.2.51")
for mod, name in ((g234, "2.34"), (g235, "2.35"), (g248, "2.48"), (g250, "2.50"), (g251, "2.51")):
    ck(all(hasattr(mod, f) for f in FLAGS), "every flag exists at %s" % name)
mv = [f for f in FLAGS if getattr(g250, f) != getattr(g248, f)]
ck(not mv, "2.50 (tooling) moves ZERO contour flags vs the adopted 2.48 (%s)" % mv)
ck(not g250.B_ECHO_RESTORE, "the frozen echo grammar is OFF at 2.50")
ck(getattr(g248, "B_ECHO_RESTORE") is False, "the pair control 2.48 runs WITHOUT the 2.51 flag")
ck(getattr(g251, "B_ECHO_RESTORE") is True, "2.51 re-arms the echo grammar")
mv2 = [f for f in FLAGS if getattr(g251, f) != getattr(g250, f) and f != "B_ECHO_RESTORE"]
ck(not mv2, "2.51 = the 2.50 matrix + exactly B_ECHO_RESTORE (%s)" % mv2)
ck(not g251.B_FIELD_COMPLETE and g234.B_FIELD_COMPLETE,
   "the config-fields grammar stays frozen to exactly (2,34)")
ck(not g250.B_FIELD_COMPLETE and not g250.B_ECHO_RESTORE and not g235.B_ECHO_RESTORE,
   "2.35-2.50 run NEITHER B field grammar — the 2.51 re-arm does not rewrite history")

# registration axes
spec = importlib.util.spec_from_file_location("gate_versioning_v65", str(HERE / "gate_versioning.py"))
GV = importlib.util.module_from_spec(spec)
spec.loader.exec_module(GV)
ck((2, 51) in GV.CONTOUR_FEATURES, "(2,51) is registered in CONTOUR_FEATURES")
ck(GV.CURRENT_REVISION >= (2, 51) and GV.CURRENT_STAMP == "0.0.2.51", "CURRENT bumped to 2.51")
ck(GV.behavior_tuple("0.0.2.51") == (2, 51), "stamp 2.51 IS a contour release (behavior 2.51)")
ck(GV.behavior_tuple("0.0.2.50") == (2, 48), "tooling 2.50 still reports behavior 2.48")
ck(GV.summary("0.0.2.51")["contour_changed_at_this_release"] is True,
   "the run record says this release changes the contour")

# ------------------------------------------------------- call-site predicate
for mod, want, name in ((g234, True, "2.34"), (g235, False, "2.35"), (g244 := load("0.0.2.44"),
                         False, "2.44"), (g248, False, "2.48"), (g250, False, "2.50"),
                        (g251, True, "2.51")):
    ck((mod.B_FIELD_COMPLETE or mod.B_ECHO_RESTORE) is want,
       "call-site predicate (B_FIELD_COMPLETE or B_ECHO_RESTORE) is %s at %s" % (want, name))

# ------------------------------------------------------------- transformation
r, ev = g251.b_fields_by_code(b05, BAD_ANSWER)
ck(ev == ["v51_b_echo_restore"], "the 2.51 repair fires with its own event name")
out = json.loads(r)


def balanced_literal(text):
    """Same balanced-brace scan the harness itself uses to pull the prompt's JSON literal."""
    i0 = text.find("{")
    depth = 0
    for i in range(i0, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[i0:i + 1])
    raise AssertionError("no balanced literal")


literal = balanced_literal(b05["prompt"])
ck(out["items"] == literal["items"], "items restored VERBATIM from the prompt's own literal")
ck(out["n_tags"] == sum(len(it["tags"]) for it in literal["items"]),
   "the declared count is recomputed from the literal")
ck("cursor" not in out, "the declared drop is applied")
# scorer identity: what the frozen scorer wants for this task == what the repair produces
sys.modules.pop("parb_check_v6", None)
ck_spec = importlib.util.spec_from_file_location("parb_check_v6", str(HERE / "parb_check_v6.py"))
CK = importlib.util.module_from_spec(ck_spec)
ck_spec.loader.exec_module(CK)
c, f, notes = CK.check_json_obj(b05, r)
ck(c == 1.0 and f, "the repaired bytes strict-pass under the frozen v6 scorer (%s)" % notes)

r2, ev2 = g251.b_fields_by_code(b05, GOOD_ANSWER)
ck(ev2 is None and r2 == GOOD_ANSWER, "an already-equal answer is NOT rewritten (zero fires on passes)")

r3, ev3 = g234.b_fields_by_code(b05, BAD_ANSWER)
ck(ev3 == ["v234_b_echo_count"], "2.34 keeps its own event name — history bytes not rewritten")
ck(json.loads(r3) == out, "2.34 and 2.51 repair to identical bytes (only the event name differs)")

r4, ev4 = g248.b_fields_by_code(b05, BAD_ANSWER)
ck(ev4 is None and r4 == BAD_ANSWER, "the control stamp leaves the published failure untouched")

# ------------------------------------------------------------- refusals
prompt = b05["prompt"]
refusals = [
    ("no grammar at all", {"prompt": "Просто верни JSON.", "ref": {}}, BAD_ANSWER),
    ("two drops", {"prompt": prompt + ' и удали "meta"', "ref": {}}, BAD_ANSWER),
    ("unparseable literal", {"prompt": 'добавь поле "n_tags": сумма длин tags по всем items, '
                                       'и удали "cursor". JSON: {items: [', "ref": {}}, BAD_ANSWER),
    ("items not a list", {"prompt": 'добавь поле "n_tags": сумма длин tags по всем items, '
                                    'и удали "cursor". JSON: {"items": 7}', "ref": {}}, BAD_ANSWER),
    ("item missing the length field",
     {"prompt": 'добавь поле "n_tags": сумма длин tags по всем items, '
                'и удали "cursor". JSON: {"items":[{"sku":"x"}],"cursor":"c"}', "ref": {}},
     BAD_ANSWER),
    ("non-dict answer", {"prompt": prompt, "ref": {}}, "[]"),
    ("invented top-level key", {"prompt": prompt, "ref": {}},
     json.dumps({"items": literal["items"], "n_tags": 1, "extra": 1})),
]
for name, task, ans in refusals:
    rr, ee = g251.b_fields_by_code(task, ans)
    ck(ee is None and rr == ans, "refuses and touches nothing: %s" % name)

# ------------------------------------------------- synthetic invented fields
syn_task = {"prompt": ('Инвентарь ниже. добавь поле "n_flags": сумма длин flags по всем boxes, '
                       'и удали "cursor". Boxes не меняй. Только JSON. '
                       'JSON: {"boxes":[{"sku":"Z1","flags":["a","b"]},{"sku":"Z2","flags":[]}],'
                       '"cursor":"x"}'),
            "ref": {}}
syn_bad = json.dumps({"boxes": [{"sku": "Z1", "flags": ["a", "b"], "n_flags": 2},
                                {"sku": "Z2", "flags": [], "n_flags": 0}], "n_flags": 2})
sr, sev = g251.b_fields_by_code(syn_task, syn_bad)
ck(sev == ["v51_b_echo_restore"], "the grammar is field-name generic: it fires on invented names")
sout = json.loads(sr)
ck(sout["boxes"] == [{"sku": "Z1", "flags": ["a", "b"]}, {"sku": "Z2", "flags": []}],
   "synthetic literal restored verbatim")
ck("cursor" not in sout and sout["n_flags"] == 2, "synthetic drop and recompute")

# --------------------------------------------------------- coverage census
hits = set()
for t in bank:
    if g251._B_ECHO_RE.search(t.get("prompt") or t.get("free_text") or ""):
        hits.add(t["id"])
ck(hits == {"B-ex6-05"}, "echo grammar matches EXACTLY one task over the 77 v6.2 prompts (%s)" % hits)

print("gate_v65_b_echo_restore_test: PASS (%d checks)" % CHECKS)
