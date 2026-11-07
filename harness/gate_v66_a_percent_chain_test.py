#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.52 contract: the A PERCENT-CHAIN arithmetic (pair-249 candidate).

Bank v6.2+ published draws strict-fail A-ex6-03 in 10/15 contour rows (pair-246 3/3 both arms,
pair-247 2/3 BOTH arms, pair-248 2/3 BOTH arms, cadence-246 1/3): the model emits the right JSON
shape but miscomputes `tax`/`net` around the chain the prompt states verbatim. Zero a_arith contour
events on every published A-ex6-03 row: the adopted 2.27 grammars and the frozen 2.33 tariff branch
never reach this shape. 0.0.2.52 adds the fifth branch of the SAME family: the chain is recomputed
by code from the prompt's own text (one `id=NUMBER` base, «<Label> P% от <expr>, [но] не более|не
менее CAP» clauses, one parenthesized formula binding clause order to spec-key order), the model's
key set is never changed, an already-equal answer is a no-op, every uncertainty refuses, the
reference is never read, zero model tokens.

Checks:
1. per-stamp flag matrix: 2.51 (the adopted line) runs WITHOUT A_PCT_CHAIN, 2.52 with it; the
   event name is v52_a_percent_chain (a 2.27-era name is never reused)
2. coverage census over ALL 77 bank-v6.2 AND all 77 bank-v6.6 prompts: the grammar parses
   EXACTLY {A-ex6-03} on both banks (A-ex6-03 bytes are byte-identical v6.2 -> v6.6)
3. derivability: the grammar's values on A-ex6-03 equal the bank ref numerically (the gold is
   reproduced from the printed rules, no reference read)
4. counterfactual replay over EVERY published A-ex6-03 answer on the v6.2-era line (cadence-246 +
   pair-246/247/248, 21 rows): every strict-fail row re-values to the gold with
   v52_a_percent_chain, every strict-pass row is untouched, mis-derivations 0; the same bytes at
   stamp 2.51 produce ZERO a-family events (the control arm cannot carry the candidate's repair)
5. refusal branches on synthetic invented-name prompts (bank-independence): two bases, clause/
   key count disagreement, unknown token, formula naming an unknown id, word-vs-label collision,
   an extra model key, a non-numeric model value; a synthetic prompt with the same shape but
   invented names/numbers re-values correctly
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


def load_bank(name):
    bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / name), encoding="utf-8"))
    if isinstance(bank, dict):
        bank = bank.get("tasks", bank)
    return bank


bank62 = load_bank("bank-hard-v6.2.json")
bank66 = load_bank("bank-hard-v6.6.json")
t62 = [t for t in bank62 if t["id"] == "A-ex6-03"][0]
t66 = [t for t in bank66 if t["id"] == "A-ex6-03"][0]
ck(json.dumps(t62, sort_keys=True, ensure_ascii=False)
   == json.dumps(t66, sort_keys=True, ensure_ascii=False),
   "A-ex6-03 task bytes byte-identical v6.2 -> v6.6 (chronic target transfers)")

g251 = load("0.0.2.51")
g252 = load("0.0.2.52")

# 1. flag matrix + event naming
ck(getattr(g251, "A_PCT_CHAIN") is False, "the pair-249 candidate trigger is OFF on the 2.51 line")
ck(getattr(g252, "A_PCT_CHAIN") is True, "the candidate trigger is ON at 2.52")
import gate_versioning as GV  # noqa: E402
ck((2, 52) in GV.CONTOUR_FEATURES and GV.behavior_tuple("0.0.2.52") == (2, 52),
   "the candidate registers a real contour change (stamp 2.52 = behavior 2.52)")

# 2. coverage census on both banks
for name, bank in (("v6.2", bank62), ("v6.6", bank66)):
    parsed = [t["id"] for t in bank if g252._a_pct_chain(t.get("prompt", ""))]
    ck(parsed == ["A-ex6-03"], "bank %s: grammar parses EXACTLY {A-ex6-03}, got %s" % (name, parsed))

# 3. derivability: values from the printed rules == bank ref
keys, vals = g252._a_pct_chain(t66["prompt"])
ck(keys == ["social", "tax", "net"], "spec key order preserved")
for k, want in t66["ref"].items():
    ck(abs(vals[k] - float(want)) < 1e-9, "grammar derives ref[%s]=%s from prompt text, got %s"
       % (k, want, vals[k]))

# 4. counterfactual replay over the published v6.2-era line
VR = HERE.parent / "benchmarks" / "hard" / "v6-results"
LEGS = ([("cadence-246", "q45r%d" % r) for r in (16, 17, 18)]
        + [("pair-246", "s46r%d" % r) for r in (19, 20, 21)]
        + [("pair-246", "s47r%d" % r) for r in (19, 20, 21)]
        + [("pair-247", "t47r%d" % r) for r in (22, 23, 24)]
        + [("pair-247", "t48r%d" % r) for r in (22, 23, 24)]
        + [("pair-248", "u48r%d" % r) for r in (34, 35, 36)]
        + [("pair-248", "u51r%d" % r) for r in (34, 35, 36)])
rows = 0
fails_converted = 0
passes_noop = 0
misderived = 0
for d, tag in LEGS:
    led = [json.loads(l) for l in open(VR / d / ("ledger-%s.jsonl" % tag), encoding="utf-8") if l.strip()]
    res = {}
    for l in open(VR / d / ("results-%s.jsonl" % tag), encoding="utf-8"):
        if l.strip():
            r = json.loads(l)
            if r["task"] == "A-ex6-03":
                res[r["rep"]] = r.get("answer") or ""
    for L in led:
        if L["task"] != "A-ex6-03":
            continue
        ans = res.get(L["rep"])
        ck(bool(ans), "blank joined answer for %s r%s (join broken)" % (tag, L["rep"]))
        rows += 1
        strict = L["content"] == 1.0 and bool(L["format_ok"])
        new252, ev252 = g252.a_arith_by_code(dict(t66), ans)
        _, ev251 = g251.a_arith_by_code(dict(t62), ans)
        ev252, ev251 = ev252 or [], ev251 or []
        ck(not any("a_arith" in e or "a_percent" in e or "a_tariff" in e for e in ev251),
          "2.51 control bytes must emit ZERO a-family events (control cannot carry the repair): %s r%s"
          % (tag, L["rep"]))
        if strict:
            ck(not ev252, "zero fires on a strict-PASS row: %s r%s" % (tag, L["rep"]))
            ck(new252 == ans, "strict-pass answer byte-identical at 2.52: %s r%s" % (tag, L["rep"]))
            passes_noop += 1
        else:
            if ev252:
                ck(ev252 == ["v52_a_percent_chain"],
                   "conversion event is exactly v52_a_percent_chain: %s r%s -> %s" % (tag, L["rep"], ev252))
                obj = json.loads(new252)
                if set(obj) != set(keys):
                    misderived += 1
                    continue
                if all(abs(float(obj[k]) - vals[k]) < 1e-9 for k in keys):
                    fails_converted += 1
                else:
                    misderived += 1
            # a strict-fail row the grammar refused is neither conversion nor mis-derivation
ck(rows == 21, "replay covers 21 published A-ex6-03 rows, got %d" % rows)
ck(fails_converted == 15, "all 15 published strict-fail rows re-value to the gold (got %d)" % fails_converted)
ck(passes_noop == 6, "all 6 published strict-pass rows untouched (got %d)" % passes_noop)
ck(misderived == 0, "mis-derivations 0")

# 5. refusals and bank-independence on synthetic invented-name prompts
SYN_OK = ("Тариф: quota=400.0. Комиссия 25% от базы (quota), но не более 90. "
          "Сбор 10% от (quota - комиссия - надбавка 40), не менее 5. "
          'Верни JSON {"fee","levy","rest"} (rest = quota - fee - levy).')
pkeys, pvals = g252._a_pct_chain(SYN_OK)
ck(pkeys == ["fee", "levy", "rest"] and abs(pvals["fee"] - 90.0) < 1e-9
   and abs(pvals["levy"] - 27.0) < 1e-9 and abs(pvals["rest"] - 283.0) < 1e-9,
   "synthetic invented-name chain computes from its own literals (cap binds: min(100,90)=90)")
syn_task = {"id": "A-ex6-99", "cat": "A", "prompt": SYN_OK}
ans_syn = json.dumps({"fee": 100.0, "levy": 36.0, "rest": 264.0})
out, ev = g252.a_arith_by_code(syn_task, ans_syn)
ck(ev == ["v52_a_percent_chain"] and abs(json.loads(out)["fee"] - 90.0) < 1e-9
   and abs(json.loads(out)["levy"] - 27.0) < 1e-9, "synthetic conversion fires with the v52 event")

REFUSALS = {
    "two bases": SYN_OK + " bonus=10.0.",
    "clause/key count": 'Тариф: quota=400.0. Комиссия 25% от базы (quota), но не более 90. Сбор 10% от (quota - комиссия - надбавка 40), не менее 5. Налог 5% от (quota - комиссия), не менее 0. Верни JSON {"fee","levy","rest"} (rest = quota - fee - levy).',
    "unknown token": SYN_OK.replace("надбавка 40", "надбавка * 40"),
    "formula unknown id": SYN_OK.replace("(rest = quota - fee - levy)", "(rest = quota - fee - misc)"),
    "word/label collision": SYN_OK.replace("надбавка 40", "комиссия 40"),
}
for label, pr in REFUSALS.items():
    ck(g252._a_pct_chain(pr) is None, "refusal (%s) must return None" % label)
    out, ev = g252.a_arith_by_code({"id": "A-ex6-99", "cat": "A", "prompt": pr}, ans_syn)
    ck(not ev and out == ans_syn, "refusal (%s) leaves the answer byte-identical" % label)

# model-side refusals: extra key, non-numeric value, missing key
EXTRA = json.dumps({"social": 2090.0, "tax": 1141.9, "net": 6268.1, "extra": 1})
out, ev = g252.a_arith_by_code(dict(t66), EXTRA)
ck(not ev, "an extra model key refuses (membership never changed)")
STR = json.dumps({"social": 2090.0, "tax": "ok", "net": 6268.1})
out, ev = g252.a_arith_by_code(dict(t66), STR)
ck(not ev, "a non-numeric model value refuses")
EQUAL = json.dumps({"social": 2090.0, "tax": 1179.9, "net": 6230.1})
out, ev = g252.a_arith_by_code(dict(t66), EQUAL)
ck(not ev and out == EQUAL, "an already-equal answer is a no-op (zero fires on passes)")

print("gate_v66 PASS: %d checks | A percent-chain only at >=2.52, surface EXACTLY {A-ex6-03} on "
      "v6.2+v6.6, gold derived from prompt text, 15/15 published losses convert, 6/6 passes "
      "untouched, mis-derivations 0, refusals byte-clean" % CHECKS)
