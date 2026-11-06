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

print("gate_v49 PASS: %d checks | features frozen per stamp; J re-rank ONLY at 2.32 (not adopted), covers %d/%d J tasks"
      % (CHECKS, len(covered), len([x for x in bank if x["cat"] == "J"])))
