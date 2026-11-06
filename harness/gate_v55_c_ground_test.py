#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.41 contract: C membership re-derived from the prompt's own stated rule
(pair-242 candidate).

Target class: group 1 `set_mismatch` (UNSTABLE-CELLS-V61). The only failure of the adopted 2.29+
line in ~40 published C rows is C-ex6-03 (`got=['A'] want=['A','D']`) — an SLA task whose rule
and every option's values are stated IN the prompt. C-ex6-00/01 are judgment tasks (no rule in
the prompt): the grammar must REFUSE them byte-identical, that limit is part of the contract.

Checks:
1. flag matrix: C_RULE_GROUND only from 2.41; the 2.40 arms stay byte-identical (history pin)
2. synthetic tasks with INVENTED field names: over-inclusion fixed, omission added, boundary
   value obeyed (`4 минуты 59 секунд` fails `>=5 минут`); every refusal path (option silent on a
   predicate, double-stated value, hour unit, col-first value order, no «когда», non-satisfying
   question, never-said variable, unknown token in a formula) leaves the answer byte-identical
3. the real bank prompts: coverage states exactly which C prompts parse (threshold + truth
   table), and NO parseable prompt is mis-derived; refused prompts untouched
4. REPLAY OVER THE PUBLISHED bank-v6.1 C rows (pair-231, pair-240, full-229, reps-229,
   four-arm-v61): the three published C-ex6-03 losses convert to strict pass, ZERO of the other
   published C rows change score, and every conversion is evented.
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
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_c_ground"):
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


g240 = load("0.0.2.40")
g241 = load("0.0.2.41")
ck(not g240.C_RULE_GROUND and g241.C_RULE_GROUND, "C rule-grounding flag ONLY from 2.41")

# ---- synthetic tasks with invented field names (over-fitting guard) ----
SYN = ("Порог аварии: когда load >= 4 и queue >= 10 на >= 2 минуты подряд. Что НАРУШАЕТ порог?\n"
       "Формат ответа: 'ОТВЕТ: <буквы>'.\n"
       "A: 5 load и 12 queue в течение 3 минут\n"
       "B: 4 load и 9 queue в течение 5 минут\n"
       "C: 6 load и 11 queue ровно 1 минута 59 секунд\n"
       "D: 4 load и 10 queue 2 минуты\n")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN}, "размышления\nОТВЕТ: A")
ck(out.endswith("ОТВЕТ: A,D"), "synthetic omission (D also crosses every predicate) is re-derived: %r" % out)
ck(any("v241_c_rule_ground_from_prompt" in e for e in (ev or [])), "conversion is evented: %s" % ev)
out, ev = g241.post_normalize_answer("C", {"prompt": SYN}, "ОТВЕТ: A,C")
ck(out.endswith("ОТВЕТ: A,D"), "synthetic over-inclusion (C is 1:59 < 2 минуты) is re-derived: %r" % out)
out, ev = g241.post_normalize_answer("C", {"prompt": SYN}, "ОТВЕТ: A,D")
ck(out == "ОТВЕТ: A,D" and any("v241_c_rule_ground_matched" in e for e in (ev or [])),
   "a model already matching the rule keeps its bytes and marks matched (live-wiring proof): %s" % ev)

# refusal paths leave bytes untouched
SYN_SILENT = SYN.replace("B: 4 load и 9 queue в течение 5 минут", "B: 4 load в течение 5 минут")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_SILENT}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A" and not any("v241" in str(e) for e in (ev or [])),
   "an option silent on a predicate refuses the WHOLE prompt")
SYN_DOUBLE = SYN.replace("A: 5 load и 12 queue в течение 3 минут", "A: 5 load, 6 load и 12 queue за 3 минуты")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_DOUBLE}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "a double-stated value is ambiguous -> refuse")
SYN_HOURS = SYN.replace("на >= 2 минуты подряд", "на >= 2 часа подряд")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_HOURS}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "an out-of-grammar time unit refuses")
SYN_COLFIRST = ("Порог: когда load >= 4 на >= 2 минуты подряд. Что НАРУШАЕТ?\n"
                "A: load 5 в течение 3 минут\nB: load 3 в течение 3 минут\n")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_COLFIRST}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "col-first value order is outside this grammar -> refuse")
SYN_NOWHEN = SYN.replace("когда load", "если load", 1)
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_NOWHEN}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "rule not introduced by «когда» refuses")
SYN_QPOL = SYN.replace("Что НАРУШАЕТ порог?", "Какие из этих вариантов вообще существуют?")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_QPOL}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "a question that does not ask for rule-satisfying options refuses")
# an answer without an ОТВЕТ line is the shape contract's class, not this one
out, ev = g241.post_normalize_answer("C", {"prompt": SYN}, "просто текст без строки ответа")
ck(out == "просто текст без строки ответа", "no answer line: this mechanism adds nothing")

# truth-table synthetic with different variables
SYN_TT = ("Таблица истинности: когда (c OR NOT d) AND a истинно?\n"
          "Формат: 'ОТВЕТ: <буквы>'.\n"
          "A: a=1,c=1,d=1\nB: a=0,c=1,d=0\nC: a=1,c=0,d=0\nD: a=1,c=0,d=1\nE: никогда\n")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_TT}, "ОТВЕТ: A")
ck(out.endswith("ОТВЕТ: A,C"), "truth-table omission (C: a=1,c=0,d=0 is also true) is re-derived: %r" % out)
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_TT + "F: a=1\n"}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "a partial assignment (not every variable stated) refuses")
SYN_TT_BAD = SYN_TT.replace("(c OR NOT d) AND a", "(c XOR d) AND a")
out, ev = g241.post_normalize_answer("C", {"prompt": SYN_TT_BAD}, "ОТВЕТ: A")
ck(out == "ОТВЕТ: A", "a formula outside AND/OR/NOT refuses")

# ---- the real bank prompts: coverage + zero mis-derivation ----
bank = json.load(open(str(HERE.parent / "benchmarks" / "hard" / "bank-hard-v6.json"), encoding="utf-8"))
B = {t["id"]: t for t in bank}
import gate_c_ground as CG

cov = CG.rule_coverage(bank)
parsed = {tid: d for tid, d, gold, ok in cov if d is not None}
ck(set(parsed) == {"C-ex6-03", "C-ex6-05"},
   "coverage is exactly the two rule-stated C prompts (judgment prompts must refuse): %s" % sorted(parsed))
ck(all(ok for tid, d, gold, ok in cov if d is not None),
   "ZERO mis-derivations on the bank: %s" % cov)

tc = B["C-ex6-03"]
out, ev = g241.post_normalize_answer("C", {"prompt": tc["prompt"]}, "ОТВЕТ: A")
ck(out.endswith("ОТВЕТ: A,D") and any("v241_c_rule_ground_from_prompt" in e for e in ev),
   "the chronic C-ex6-03 failing bytes convert at 2.41: %r" % out)
out0, ev0 = g240.post_normalize_answer("C", {"prompt": tc["prompt"]}, "ОТВЕТ: A")
ck(out0 == "ОТВЕТ: A" and not any("v241" in str(e) for e in (ev0 or [])),
   "2.40 keeps exactly what pair-240 measured: no C grounding at all")
out, ev = g241.post_normalize_answer("C", {"prompt": tc["prompt"]}, "ОТВЕТ: A,D")
ck(out == "ОТВЕТ: A,D" and any("v241_c_rule_ground_matched" in e for e in ev),
   "a right C-ex6-03 draw is marked matched, bytes identical")
for jid in ("C-ex6-00", "C-ex6-01", "C-ex6-02", "C-ex6-06", "C-ex6-07", "C-ex6-08"):
    inp = "ОТВЕТ: A"
    out, ev = g241.post_normalize_answer("C", {"prompt": B[jid]["prompt"]}, inp)
    ck(out == inp and not any("v241" in str(e) for e in (ev or [])),
       "judgment prompt %s refuses byte-identical (no C-ex6-00/01 reach is claimed)" % jid)

# ---- replay over the PUBLISHED bank-v6.1 C rows (CI-pinned) ----
import parb_check_v6 as CK  # noqa: E402

RES = HERE.parent / "benchmarks" / "hard" / "v6-results"
ARMS = [("pair-231", ["d29r0", "d29r1", "d29r2", "d31r0", "d31r1", "d31r2"]),
        ("pair-240", ["m39r0", "m39r1", "m39r2", "m40r0", "m40r1", "m40r2"]),
        ("full-229", ["c229full"]),
        ("reps-229", ["c229r12", "c229r3", "c229r45"]),
        ("four-arm-v61", ["c228v61"])]
rows = 0
conv = []
regr = []
for d, arms in ARMS:
    dd = RES / d
    if not dd.is_dir():
        ck(False, "published artifacts %s missing — the replay contract cannot run" % d)
    for arm in arms:
        for line in (dd / ("results-%s.jsonl" % arm)).read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            if not r["task"].startswith("C-ex"):
                continue
            rows += 1
            old = bool(float(r["content"]) == 1.0 and bool(r["format_ok"]))
            new_txt, ev = g241.post_normalize_answer("C", B[r["task"]], r.get("answer") or "")
            c2, f2, _ = CK.check(B[r["task"]], new_txt)
            new = bool(float(c2) == 1.0 and bool(f2))
            if not old and new:
                conv.append((r["task"], r["rep"], arm,
                             any("v241_c_rule_ground_from_prompt" in str(e) for e in (ev or []))))
                if new_txt != (r.get("answer") or "") and not any(
                        "v241_c_rule_ground_from_prompt" in str(e) for e in (ev or [])):
                    ck(False, "changed row without a conversion event: %s %s %s" % (r["task"], r["rep"], arm))
            if old and not new:
                regr.append((r["task"], r["rep"], arm))
ck(rows >= 100, "replay covers every published bank-v6.1 C row: %d" % rows)
ck(not regr, "ZERO regressions across the published C rows: %s" % regr)
ck({(t, rep) for t, rep, _, _ in conv} == {("C-ex6-03", 0), ("C-ex6-03", 5)},
   "the published failing C cells convert exactly (C-ex6-03 seeds 0 and 5): %s" % conv)
ck(len(conv) == 3 and all(m for _, _, _, m in conv),
   "three conversion rows (pair-231 d31r0 seed0, four-arm c228v61 seed0, reps-229 c229r45 seed5), all evented: %s" % conv)

print("gate_v55 PASS: %d checks | C rule-grounding only from 2.41 (2.40 byte-identical); synthetic "
      "conversions + every refusal path; bank coverage 2/8 with ZERO mis-derivations; published "
      "replay over %d C rows converts 3 with ZERO regressions" % (CHECKS, rows))
