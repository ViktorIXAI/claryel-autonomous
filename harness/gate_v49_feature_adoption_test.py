#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.32 contract: a stamp inherits only ADOPTED behaviour.

0.0.2.30 (artifact-shape guarantee) and 0.0.2.31 (plurality vote) were measured negative and published as
negative. `contour_at_least` would carry them into every future stamp, which is how a lost experiment
becomes a permanent regression. So both are frozen to the exact revision where they were measured, and the
adopted line (0.0.2.29 behaviour) is what later stamps build on.

Checks:
1. flags at each revision: shape guarantee only at 2.30, self-consistency only at 2.31, J re-rank from 2.32
2. at 2.32 the J re-rank is real: a shuffled order from a bank prompt is repaired, a refused rule is not
3. the J grammar never confidently mis-sorts a bank task (coverage stated, mis-sort count must be 0)
4. the loop-D J path is untouched by the re-rank (it answers a different contract)
"""
import importlib
import importlib.util
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp.

    `gate_versioning` puts an older workspace (`~/parb`) on sys.path, which silently shadows the repo copy
    and would make the contract test measure a stale contour. The path is forced and the resolved file is
    asserted, so a shadowed import fails the gate instead of quietly passing on old code.
    """
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning", "gate_j_rerank"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
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


g229 = load("0.0.2.29")
ck(not g229.CONTRACT_GUARANTEE and not g229.SELFCONSIST and not g229.J_RERANK,
   "2.29 has none of the three experimental features")
g230 = load("0.0.2.30")
ck(g230.CONTRACT_GUARANTEE and not g230.SELFCONSIST and not g230.J_RERANK,
   "2.30 keeps ONLY its own shape guarantee")
g231 = load("0.0.2.31")
ck(not g231.CONTRACT_GUARANTEE and g231.SELFCONSIST and not g231.J_RERANK,
   "2.31 does not inherit the rejected 2.30 feature")
g232 = load("0.0.2.32")
ck(not g232.CONTRACT_GUARANTEE and not g232.SELFCONSIST and g232.J_RERANK and not g232.A_TABLE_ARITH,
   "2.32 builds on adopted behaviour plus the J re-rank only")
g233 = load("0.0.2.33")
ck(not g233.CONTRACT_GUARANTEE and not g233.SELFCONSIST and not g233.J_RERANK and g233.A_TABLE_ARITH
   and not g233.B_FIELD_COMPLETE,
   "2.33 does NOT inherit the unadopted 2.32 re-rank and adds only the threshold-table arithmetic")
g234 = load("0.0.2.34")
ck(not g234.CONTRACT_GUARANTEE and not g234.SELFCONSIST and not g234.J_RERANK and not g234.A_TABLE_ARITH
   and g234.B_FIELD_COMPLETE and not g234.B_TABLE_AGGREGATE,
   "2.34 inherits adopted behaviour plus B field completeness only; the unadopted 2.32/2.33 stay frozen")
g235 = load("0.0.2.35")
ck(not g235.CONTRACT_GUARANTEE and not g235.SELFCONSIST and not g235.J_RERANK and not g235.A_TABLE_ARITH
   and not g235.B_FIELD_COMPLETE and g235.B_TABLE_AGGREGATE,
   "2.35 inherits adopted behaviour plus the B table aggregation only: the measured -1.0/zero-fire "
   "2.34 grammar is frozen to its own stamp and must not ride into 2.35")
g236 = load("0.0.2.36")
ck(not g236.CONTRACT_GUARANTEE and not g236.SELFCONSIST and not g236.J_RERANK and not g236.A_TABLE_ARITH
   and not g236.B_FIELD_COMPLETE and not g236.B_TABLE_AGGREGATE and g236.G4_LOTTERY,
   "2.36 does NOT inherit the pair-235-unadopted 2.35 table repair and adds only the group-4 "
   "lottery selection: confirmed-on-target but arm-unresolved stays frozen to its own stamp")
g237 = load("0.0.2.37")
ck(not g237.CONTRACT_GUARANTEE and not g237.SELFCONSIST and not g237.J_RERANK and not g237.A_TABLE_ARITH
   and not g237.B_FIELD_COMPLETE and not g237.G4_LOTTERY and g237.B_TABLE_AGGREGATE,
   "2.37 inherits adopted behaviour plus the RE-LANDED B table repair only: the pair-236-measured-negative "
   "group-4 lottery is frozen to exactly 2.36 and must not ride into 2.37 or any later stamp")
g236b = load("0.0.2.36")
ck(not g236b.B_TABLE_AGGREGATE and g236b.G4_LOTTERY,
   "the 2.37 re-adoption must not rewrite history: 2.36 still runs the lottery and NOT the table repair")
g238 = load("0.0.2.38")
ck(not g238.CONTRACT_GUARANTEE and not g238.SELFCONSIST and not g238.J_RERANK and g238.A_TABLE_ARITH
   and not g238.B_FIELD_COMPLETE and not g238.G4_LOTTERY and g238.B_TABLE_AGGREGATE,
   "2.38 inherits the ADOPTED line (2.29 behaviour + the pair-237-adopted B table repair) plus the "
   "re-landed A threshold arithmetic only: the measured-negative 2.30/2.31/2.36 and the unresolved "
   "2.32/2.34 grammars stay frozen to their own stamps")
g237b = load("0.0.2.37")
ck(not g237b.A_TABLE_ARITH and g237b.B_TABLE_AGGREGATE,
   "the 2.38 re-adoption must not rewrite history: the 2.37 arms still ran WITHOUT the A arithmetic")
ck(not g238.J_RERANK_V2, "2.38 does not inherit the 2.39 grammar v2 re-land")
g239 = load("0.0.2.39")
ck(not g239.CONTRACT_GUARANTEE and not g239.SELFCONSIST and not g239.J_RERANK and g239.J_RERANK_V2
   and not g239.A_TABLE_ARITH and g239.B_TABLE_AGGREGATE and not g239.B_FIELD_COMPLETE and not g239.G4_LOTTERY,
   "2.39 inherits the ADOPTED line (2.29 + B table) plus the J re-rank grammar v2 ONLY: the A arithmetic "
   "was UNMEASURED at pair-238 and stays pinned to exactly (2,33)/(2,38) — it must NOT ride into 2.39 "
   "via a contour_at_least floor; the v1 J flag stays frozen to 2.32 and 2.30/2.31/2.34/2.36 stay frozen")
ck(g238.A_TABLE_ARITH and not g239.A_TABLE_ARITH,
   "pin matrix: 2.38 still runs the A arithmetic (its own measured stamp), 2.39 does not")
g240 = load("0.0.2.40")
ck(not g240.CONTRACT_GUARANTEE and not g240.SELFCONSIST and not g240.J_RERANK and g240.J_RERANK_V2
   and g240.J_MEMBERSHIP_V3 and not g240.A_TABLE_ARITH and g240.B_TABLE_AGGREGATE
   and not g240.B_FIELD_COMPLETE and not g240.G4_LOTTERY,
   "2.40 inherits the ADOPTED line (2.29 + B table + the pair-239-adopted J grammar v2) plus the J "
   "membership re-derivation ONLY: 2.30/2.31/2.34/2.36 frozen, 2.32 v1 frozen, A arithmetic still "
   "pinned to exactly (2,33)/(2,38)")
g239b = load("0.0.2.39")
ck(not g239b.J_MEMBERSHIP_V3 and g239b.J_RERANK_V2,
   "history pin: the 2.39 arms ran the re-rank WITHOUT membership adoption; the 2.40 change must not "
   "rewrite what pair-239 measured")
g241 = load("0.0.2.41")
ck(not g241.CONTRACT_GUARANTEE and not g241.SELFCONSIST and not g241.J_RERANK and g241.J_RERANK_V2
   and g241.J_MEMBERSHIP_V3 and g241.C_RULE_GROUND and not g241.A_TABLE_ARITH and g241.B_TABLE_AGGREGATE
   and not g241.B_FIELD_COMPLETE and not g241.G4_LOTTERY,
   "2.41 inherits the ADOPTED line (2.29 + B table + J grammar v2 + J membership) plus the C "
   "rule-grounded membership ONLY: 2.30/2.31/2.34/2.36 frozen, 2.32 v1 frozen, A arithmetic still "
   "pinned to exactly (2,33)/(2,38)")
g240b = load("0.0.2.40")
ck(not g240b.C_RULE_GROUND and g240b.J_MEMBERSHIP_V3,
   "history pin: the 2.40 arms ran WITHOUT C rule-grounding; pair-240's numbers must not move")
ck(g232.J_RERANK and not g232.J_RERANK_V2,
   "history pin: the 2.32 arms ran grammar v1 only; the 2.39 re-land must not rewrite 2.32")
g238b = load("0.0.2.38")
ck(not g238b.J_RERANK and not g238b.J_RERANK_V2,
   "history pin: the 2.38 arms ran NO J re-rank at all")

bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))
import gate_j_rerank as JR

cov = dict(JR.rule_coverage(bank))
ck(not [t for t, s in cov.items() if s.startswith("MIS")], "J grammar must not mis-sort: %s" % cov)
covered = [t for t, s in cov.items() if s == "reproduces"]
ck(len(covered) >= 2, "J grammar must cover at least two bank tasks: %s" % cov)

# behaviour through the contour itself, not just through the helper
t = next(x for x in bank if x["id"] == covered[0])
shuffled = list(t["ref"])
shuffled.reverse()
out, ev = g232.post_normalize_answer("J", {"prompt": t["prompt"]}, json.dumps(shuffled, ensure_ascii=False))
ck(json.loads(out) == list(t["ref"]), "2.32 repairs a reversed J order: %s vs %s" % (out, t["ref"]))
ck(any("v232_j_rerank" in e for e in (ev or [])), "the repair is evented: %s" % ev)

# a task the grammar refuses stays byte-identical
refused = [x for x in bank if cov.get(x["id"]) == "refuses"]
for bad in refused:
    out, ev = g232.post_normalize_answer("J", {"prompt": bad["prompt"]}, json.dumps(list(bad["ref"]), ensure_ascii=False))
    ck(json.loads(out) == list(bad["ref"]), "%s refused rule leaves the order alone" % bad["id"])

# loop J is a different contract: not touched
loop = dict(t, mode="loop")
out, ev = g232.post_normalize_answer("J", loop, "1. v5 2. v3")
ck(out == "1. v5 2. v3" and not any("v232" in e for e in (ev or [])), "loop-D J answers are not re-ranked")

# 2.39 call-site wiring: J-ex6-02 is OUTSIDE the v1 grammar (product primary key + tie chain), so the
# same bytes prove the v2 path fires at 2.39 with its own event and stays untouched at 2.38.
tj = next(x for x in bank if x["id"] == "J-ex6-02")
sh2 = list(tj["ref"])
sh2.reverse()
inp = json.dumps(sh2, ensure_ascii=False)
out9, ev9 = g239.post_normalize_answer("J", {"prompt": tj["prompt"]}, inp)
ck(json.loads(out9) == list(tj["ref"]), "2.39 repairs the J-ex6-02 product+chain order: %s vs %s" % (out9, tj["ref"]))
ck(any("v239_j_rerank" in e for e in (ev9 or [])), "the 2.39 repair is evented: %s" % ev9)
out8, ev8 = g238b.post_normalize_answer("J", {"prompt": tj["prompt"]}, inp)
ck(out8 == inp and not any("j_rerank" in str(e) for e in (ev8 or [])),
   "at 2.38 the same bytes stay untouched: %s / %s" % (out8, ev8))

# The smoke-caught composition bug: a model answer that decorates each id in a dict hit the
# decorated-ids early return and the re-rank never saw it. From 2.39 the two compose; at 2.32 the
# early return stays byte-identical.
dicts = [{"id": i} for i in reversed(list(tj["ref"]))]
outd9, evd9 = g239.post_normalize_answer("J", {"prompt": tj["prompt"]}, json.dumps(dicts, ensure_ascii=False))
ck(json.loads(outd9) == list(tj["ref"]) and any("j_id_norm" in e for e in evd9)
   and any("v239_j_rerank" in e for e in evd9),
   "2.39 composes decorated-ids repair with the re-rank: %s %s" % (outd9, evd9))
outd2, evd2 = g232.post_normalize_answer("J", {"prompt": tj["prompt"]}, json.dumps(dicts, ensure_ascii=False))
ck(json.loads(outd2) == list(reversed(list(tj["ref"]))) and evd2 == ["j_id_norm"],
   "2.32 keeps the early-return composition: re-rank never sees a decorated answer")

# pair-242 froze C_RULE_GROUND: the pair was UNMEASURED (the adopted line passed C-ex6-03 strict in
# all three control seeds, zero live on-target cell), so the flag must stay pinned to exactly 2.41
# and can never inherit into a future contour. The 2.41 firing itself is pinned by gate_v55 and the
# published pair ledger (v241_c_rule_ground_matched x6); this check pins the freeze boundary.
g240c = load("0.0.2.40")
g241c = load("0.0.2.41")
ck(not g240c.C_RULE_GROUND, "C_RULE_GROUND is OFF at 0.0.2.40 (the adopted line never ran it)")
ck(g241c.C_RULE_GROUND, "C_RULE_GROUND is ON only at its own stamp 0.0.2.41")

# 2.42 (D-loop policy re-ground): a NEW candidate, so it must be off on every earlier stamp and
# on exactly itself until pair-243 measures it; the frozen 2.41 must NOT inherit into it and the
# adopted line must not disappear from it. Full wiring is pinned by gate_v56.
g242f = load("0.0.2.42")
ck(not g240c.LOOP_POLICY_REGROUND and not g241c.LOOP_POLICY_REGROUND,
   "LOOP_POLICY_REGROUND is OFF at 0.0.2.40/0.0.2.41 (older arms byte-identical)")
ck(g242f.LOOP_POLICY_REGROUND, "LOOP_POLICY_REGROUND is ON at its own stamp 0.0.2.42")
ck(not g242f.C_RULE_GROUND, "the frozen 2.41 C grounding stays off at 0.0.2.42")
ck(g242f.J_RERANK_V2 and g242f.J_MEMBERSHIP_V3,
   "0.0.2.42 builds on the adopted line (J re-rank v2 + J membership inherited)")

# pair-243 froze LOOP_POLICY_REGROUND to exactly (2,42): the prevention nudge was MEASURED NEGATIVE
# (net-zero loop pool, +9.5% energy) and contour_at_least would otherwise inherit it into every
# later stamp as a permanent regression. pair-244's candidate 2.43 (loop best-of-2 on the
# banned_attempted family) must therefore run WITHOUT the policy tail, while keeping the adopted
# 2.11 selection and the 2.39/2.40 J line. Full wiring: gate_v57.
g243 = load("0.0.2.43")
ck(not g240c.D_BEST2_BANNED and not g241c.D_BEST2_BANNED and not g242f.D_BEST2_BANNED,
   "D_BEST2_BANNED is OFF at 0.0.2.40/41/42 (published arms byte-identical)")
ck(g243.D_BEST2_BANNED, "D_BEST2_BANNED is ON at its own stamp 0.0.2.43")
ck(g243.LOOP_POLICY_REGROUND is False,
   "the frozen 2.42 policy re-ground stays off at 2.43 — rejected behaviour never inherits")
ck(g243.D_BEST2 and g243.J_RERANK_V2 and g243.J_MEMBERSHIP_V3,
   "0.0.2.43 keeps the adopted line: 2.11 loop selection + 2.39 re-rank + 2.40 membership")
ck(not g243.CONTRACT_GUARANTEE and not g243.SELFCONSIST and not g243.C_RULE_GROUND,
   "every frozen band (2.30/2.31/2.41) stays off at 2.43")

# pair-244 ADOPTED D_BEST2_BANNED (line moves to 0.0.2.43); pair-245's candidate 2.44 (loop
# best-of-2 on the false_completion_claim family) INHERITED the 2.43 trigger as line behavior.
# pair-245 verdict (pre-registered): UNMEASURED — zero control loop rows drew the claim note —
# so 2.44 is NOT adopted and its flag is frozen to exactly (2,44): it must be ON only at its own
# stamp and the 2.43 line stays unchanged. The 2.42 policy tail and every frozen band stay off.
# Full wiring: gate_v58; the freeze mirror: gate_v58's per-stamp matrix.
g244 = load("0.0.2.44")
ck(not g240c.D_BEST2_CLAIM and not g241c.D_BEST2_CLAIM and not g242f.D_BEST2_CLAIM
   and not g243.D_BEST2_CLAIM,
   "D_BEST2_CLAIM is OFF at 0.0.2.40/41/42/43 (published arms byte-identical)")
ck(g244.D_BEST2_CLAIM, "D_BEST2_CLAIM is ON at its own stamp 0.0.2.44")
ck(g244.D_BEST2_BANNED and g244.D_BEST2,
   "the ADOPTED 2.43 banned trigger + 2.11 selection are inherited line behavior at 2.44")
ck(g244.LOOP_POLICY_REGROUND is False and not g244.C_RULE_GROUND
   and not g244.CONTRACT_GUARANTEE and not g244.SELFCONSIST,
   "the frozen bands (2.30/2.31/2.41/2.42) stay off at 2.44 — rejected behaviour never inherits")
ck(g244.J_RERANK_V2 and g244.J_MEMBERSHIP_V3,
   "0.0.2.44 builds on the adopted line (J re-rank v2 + J membership inherited)")

# 0.0.2.45 is the first MEASUREMENT-ONLY release since the reserved band: the scorer
# gained a version identity (contract v6.2, `gate_scorer_contract.py`) and every row /
# run record now names its stack, but NO contour tuple was registered. Two things must
# hold. (1) The adopted flag matrix at 2.45 is IDENTICAL to 2.43 — an identity release
# may not move a single contour flag. (2) The reporting axis still says behavior 2.44
# (the newest REGISTERED stamp), while the 2.44 flag itself is frozen off at 2.45 —
# exactly the stamp-vs-behavior trap the skill names, so it is pinned here instead of
# being discovered in a scoreboard later.
g245 = load("0.0.2.45")
import importlib.util as _ilu  # noqa: E402
_GV_SPEC = _ilu.spec_from_file_location("gate_versioning_v49", str(HERE / "gate_versioning.py"))
assert _GV_SPEC and _GV_SPEC.loader, "cannot load gate_versioning for the 2.45 matrix check"
GV = _ilu.module_from_spec(_GV_SPEC)
_GV_SPEC.loader.exec_module(GV)
_FLAGS = ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "J_RERANK_V2", "A_TABLE_ARITH",
          "B_FIELD_COMPLETE", "B_TABLE_AGGREGATE", "G4_LOTTERY", "J_MEMBERSHIP_V3",
          "C_RULE_GROUND", "LOOP_POLICY_REGROUND", "D_BEST2_BANNED", "D_BEST2_CLAIM",
          "D_BEST2", "H_BEST2", "C_BEST2", "E_MULTIERR", "CODE_FIX", "FORMAT_REPAIR",
          "C_BEST2_SET", "K_FIELDS_ENUM", "B_ECHO_RESTORE", "A_PCT_CHAIN", "C_PY_GROUND",
          "H_UNKNOWN_PROMPT")
_missing = [f for f in _FLAGS if not hasattr(g245, f) or not hasattr(g243, f)]
ck(not _missing, "every flag name in the matrix exists at 2.43 and 2.45 (%s)" % _missing)
_moved = [f for f in _FLAGS if getattr(g245, f) != getattr(g243, f)]
ck(not _moved, "2.45 moves ZERO contour flags vs the adopted 2.43 line (%s)" % _moved)
ck(g245.D_BEST2_CLAIM is False,
   "the frozen 2.44 claim trigger does NOT ride into the measurement release 2.45")
ck(g245.D_BEST2_BANNED and g245.D_BEST2 and g245.J_MEMBERSHIP_V3 and g245.J_RERANK_V2,
   "2.45 runs the adopted line unchanged (2.11 + 2.39/2.40 + 2.43)")
ck((2, 45) not in GV.CONTOUR_FEATURES,
   "2.45 registers no contour feature — a tooling release must not fake a contour change")
ck(GV.behavior_tuple("0.0.2.45") == (2, 44) and GV.CURRENT_REVISION >= (2, 45),
   "reporting axis: stamp 2.45, behavior 2.44 (newest registered) while the 2.44 flag is "
   "frozen off — name BOTH axes in every table")
ck(GV.summary("0.0.2.45")["contour_changed_at_this_release"] is False,
   "the run record says this release did not change the contour")
ck(g245.SCORER_CONTRACT_ID == "v6.2" and len(g245.SCORER_ID["contract_sha16"]) == 16,
   "the runner carries a scorer contract identity on every row")

# pair-246 (2026-11-07): 0.0.2.47 is a CONTOUR CANDIDATE stamp. The matrix discipline: 2.46 (the
# pair control) must still equal the adopted 2.43 matrix exactly, and 2.47 must equal 2.46 plus
# EXACTLY the C_BEST2_SET trigger — a candidate may not smuggle any other flag forward, and the
# pair control may not accidentally carry the candidate's mechanism.
g246 = load("0.0.2.46")
g247 = load("0.0.2.47")
_m246 = [f for f in _FLAGS if getattr(g246, f) != getattr(g243, f)]
ck(not _m246, "2.46 moves ZERO contour flags vs the adopted 2.43 line (%s)" % _m246)
ck(getattr(g246, "C_BEST2_SET") is False, "the pair-246 candidate trigger is OFF on the 2.46 control")
ck(getattr(g247, "C_BEST2_SET") is True, "the candidate trigger is ON at 2.47")
_m247 = [f for f in _FLAGS if getattr(g247, f) != getattr(g246, f) and f != "C_BEST2_SET"]
ck(not _m247, "2.47 = the 2.46 matrix + exactly C_BEST2_SET (%s)" % _m247)
ck((2, 47) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.47") == (2, 47),
   "the candidate registers a real contour change (stamp 2.47 = behavior 2.47)")

# pair-247 (2026-11-07): 0.0.2.48 is the CONTOUR CANDIDATE stamp (K fields-gate key enumeration).
# Matrix discipline again: the pair control 2.47 (the adopted line after pair-246) must move ZERO
# flags vs 2.46+C_BEST2_SET, and 2.48 must equal 2.47 plus EXACTLY K_FIELDS_ENUM.
g248 = load("0.0.2.48")
ck(getattr(g247, "K_FIELDS_ENUM") is False, "the pair-247 candidate trigger is OFF on the 2.47 control")
ck(getattr(g248, "K_FIELDS_ENUM") is True, "the candidate trigger is ON at 2.48")
_m248 = [f for f in _FLAGS if getattr(g248, f) != getattr(g247, f) and f != "K_FIELDS_ENUM"]
ck(not _m248, "2.48 = the 2.47 matrix + exactly K_FIELDS_ENUM (%s)" % _m248)
ck((2, 48) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.48") == (2, 48)
   and GV.behavior_tuple("0.0.2.47") == (2, 47),
   "the candidate registers a real contour change; the control keeps behavior 2.47")
ck(g248.C_BEST2_SET is True and g248.D_BEST2_CLAIM is False,
   "2.48 inherits the adopted pair-246 trigger and still refuses the frozen 2.44 one")

# pair-248 (2026-11-07): 0.0.2.51 is the CONTOUR CANDIDATE stamp (B echo restore re-armed).
# Matrix discipline holds: the tooling release 2.50 moves ZERO flags vs the adopted 2.48 line,
# and 2.51 = the 2.50 matrix + exactly B_ECHO_RESTORE. The 2.34 config grammar stays frozen:
# 2.34 keeps B_FIELD_COMPLETE without the new flag, and 2.51 runs the echo WITHOUT 2.34's flag.
g250 = load("0.0.2.50")
ck(getattr(g250, "B_ECHO_RESTORE") is False, "the re-arm does NOT ride backwards into the 2.50 tooling release")
_m250 = [f for f in _FLAGS if getattr(g250, f) != getattr(g248, f)]
ck(not _m250, "2.50 moves ZERO contour flags vs the adopted 2.48 line (%s)" % _m250)
g251 = load("0.0.2.51")
ck(getattr(g251, "B_ECHO_RESTORE") is True, "the candidate flag is ON at 2.51")
_m251 = [f for f in _FLAGS if getattr(g251, f) != getattr(g250, f) and f != "B_ECHO_RESTORE"]
ck(not _m251, "2.51 = the 2.50 matrix + exactly B_ECHO_RESTORE (%s)" % _m251)
ck(g251.B_FIELD_COMPLETE is False and g234.B_FIELD_COMPLETE is True,
   "the config-fields grammar stays pinned to exactly (2,34) in both directions")
ck((2, 51) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.51") == (2, 51)
   and GV.behavior_tuple("0.0.2.50") == (2, 48),
   "the candidate registers a real contour change; the 2.50 tooling release keeps behavior 2.48")

# pair-249 (2026-11-07): 0.0.2.52 is the CONTOUR CANDIDATE stamp (A percent-chain arithmetic,
# the fifth 2.27-family branch). Matrix discipline: 2.52 = the adopted 2.51 matrix + exactly
# A_PCT_CHAIN; the pair control 2.51 must not carry the candidate's trigger.
g252 = load("0.0.2.52")
ck(getattr(g251, "A_PCT_CHAIN") is False, "the pair-249 candidate trigger is OFF on the 2.51 control")
ck(getattr(g252, "A_PCT_CHAIN") is True, "the candidate trigger is ON at 2.52")
_m252 = [f for f in _FLAGS if getattr(g252, f) != getattr(g251, f) and f != "A_PCT_CHAIN"]
ck(not _m252, "2.52 = the 2.51 matrix + exactly A_PCT_CHAIN (%s)" % _m252)
ck((2, 52) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.52") == (2, 52)
   and GV.behavior_tuple("0.0.2.51") == (2, 51),
   "the candidate registers a real contour change; the control keeps behavior 2.51")

# pair-250 (2026-11-07): 0.0.2.53 is the CONTOUR CANDIDATE stamp (C python-literal options
# grounding, gate_c_ground shape C). Matrix discipline: 2.53 = the adopted 2.52 matrix + exactly
# C_PY_GROUND; the frozen 2.41 C_RULE_GROUND must be False at BOTH stamps (shape C fires only
# under its own flag and its own v53 event names - the pair-248 re-arm meta-rule).
g253 = load("0.0.2.53")
ck(getattr(g252, "C_PY_GROUND") is False, "the pair-250 candidate trigger is OFF on the 2.52 control")
ck(getattr(g253, "C_PY_GROUND") is True, "the candidate trigger is ON at 2.53")
_m253 = [f for f in _FLAGS if getattr(g253, f) != getattr(g252, f) and f != "C_PY_GROUND"]
ck(not _m253, "2.53 = the 2.52 matrix + exactly C_PY_GROUND (%s)" % _m253)
ck(getattr(g253, "C_RULE_GROUND") is False and getattr(g252, "C_RULE_GROUND") is False,
   "the frozen 2.41 C_RULE_GROUND stays silent at 2.52 and 2.53 (separate function/flag/events)")
ck((2, 53) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.53") == (2, 53)
   and GV.behavior_tuple("0.0.2.52") == (2, 52),
   "the candidate registers a real contour change; the control keeps behavior 2.52")

# pair-251 (2026-11-07): 0.0.2.54 is the CONTOUR CANDIDATE stamp (H unknown slot grounded from
# the prompt's own denial sentence - a re-arm of the ADOPTED 2.28 grammar's own documented gap).
# Matrix discipline: 2.54 = the adopted 2.53 matrix + exactly H_UNKNOWN_PROMPT; the pair control
# 2.53 must not carry the candidate's flag; the 2.28 H_REQUIRES_PROMPT stays ON at both stamps
# (its bytes never move) and the frozen 2.41 C_RULE_GROUND stays silent.
g254 = load("0.0.2.54")
ck(getattr(g253, "H_UNKNOWN_PROMPT") is False, "the pair-251 candidate trigger is OFF on the 2.53 control")
ck(getattr(g254, "H_UNKNOWN_PROMPT") is True, "the candidate trigger is ON at 2.54")
_m254 = [f for f in _FLAGS if getattr(g254, f) != getattr(g253, f) and f != "H_UNKNOWN_PROMPT"]
ck(not _m254, "2.54 = the 2.53 matrix + exactly H_UNKNOWN_PROMPT (%s)" % _m254)
ck(getattr(g253, "H_REQUIRES_PROMPT") is True and getattr(g254, "H_REQUIRES_PROMPT") is True,
   "the adopted 2.28 grammar stays ON at 2.53 and 2.54 (the re-arm is a separate function/flag/events)")
ck((2, 54) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.54") == (2, 54)
   and GV.behavior_tuple("0.0.2.53") == (2, 53),
   "the candidate registers a real contour change; the control keeps behavior 2.53")
ck(GV.CURRENT_REVISION >= (2, 54) and GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION,
   "CURRENT follows the newest registered stamp without pinning an exact tuple")

print("gate_v49 PASS: %d checks | features frozen per stamp; J re-rank v1 ONLY at 2.32 (not adopted), "
      "grammar v2 from 2.39 only; covers %d/%d J tasks under v1"
      % (CHECKS, len(covered), len([x for x in bank if x["cat"] == "J"])))
