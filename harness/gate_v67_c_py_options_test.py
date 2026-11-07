#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.53 contract: C PYTHON-LITERAL OPTIONS grounding (pair-250 candidate).

The adopted line strict-fails C-ex6-02 in 6/6 of the first bank-v6.6 draws (pair-249: both arms,
all three seeds) and 3/3 in both pair-246 arms: the model omits `list(set([1,2,3,3]))` by the
«set order is undefined» spec caveat while the task asks what the snippet PRINTS, and the
corrected bank gold IS the executed truth table (bank v6.2 changelog). The resampling route is
published-spent on this cell (pair-246: 2.47 fired 3/3, converted 0/3 — biased draw closed), so
the fix is deterministic grounding: shape C of gate_c_ground executes the task's own printed
snippets over a CLOSED allow-list and re-derives the letter set; every uncertainty refuses the
whole prompt; reference never read; zero model tokens; event names v53_* (the frozen 2.41 v241_*
names and function stay byte-frozen and cannot reach this shape).

Checks:
1. per-stamp flag matrix: 2.52 (the adopted line) runs WITHOUT C_PY_GROUND, 2.53 with it; the
   frozen 2.41 C_RULE_GROUND is False at both; event names are v53_c_py_from_prompt /
   v53_c_py_matched
2. coverage census over ALL 77 bank-v6.2 AND all 77 bank-v6.6 prompts: shape C parses EXACTLY
   {C-ex6-02} on both banks and derives {A,B,C,D} == gold on both (the executed truth table)
3. counterfactual replay over EVERY published C-ex6-02 contour answer on the v6.2-era line
   (cadence-246 + pair-246/247/248/249): every strict-fail row re-derives {A,B,C,D} == gold and
   converts via the v53 event, every strict-pass row is byte-identical with the matched event
   only, mis-derivations 0; the same bytes at stamp 2.52 produce ZERO v53 events (the control
   arm cannot carry the candidate's repair)
4. refusal branches on synthetic invented-name prompts (bank-independence): free-name options,
   second/missing target literal, non-contiguous option letters, unsafe call, comprehension,
   attribute access, an option raising while evaluating; a synthetic same-shape prompt with
   invented names/numbers derives the right set
"""
import importlib.util
import json
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
ROOT = HERE.parent
V6R = ROOT / "benchmarks" / "hard" / "v6-results"

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        raise SystemExit("FAIL: " + msg)


def load(ver):
    """Import THIS harness copy of gate_run at a given stamp (path forced: ~/parb shadowing)."""
    os.environ["PARB_GATE_VERSION"] = ver
    for m in ("gate_run", "gate_format_repair", "gate_loop_drive", "gate_versioning",
              "gate_j_rerank", "gate_c_ground"):
        sys.modules.pop(m, None)
    sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location("gate_run", str(HERE / "gate_run.py"))
    assert spec is not None and spec.loader is not None, "missing harness module: gate_run.py"
    mod = importlib.util.module_from_spec(spec)
    sys.modules["gate_run"] = mod
    spec.loader.exec_module(mod)
    assert str(mod.__file__).startswith(str(HERE)), "shadowed import: " + str(mod.__file__)
    return mod


def load_cg(ver):
    load(ver)  # ensures the module name resolves next to this harness
    cg = sys.modules.get("gate_c_ground")
    assert cg is not None and str(cg.__file__).startswith(str(HERE)), \
        "gate_c_ground must be THIS harness copy, got %r" % getattr(cg, "__file__", None)
    return cg


# ---------------------------------------------------------------- 1. flag matrix
g252 = load("0.0.2.52")
g253 = load("0.0.2.53")
ck(hasattr(g252, "C_PY_GROUND") and hasattr(g253, "C_PY_GROUND"), "flag exists at both stamps")
ck(g252.C_PY_GROUND is False, "2.52 (pair-250 control) runs WITHOUT C_PY_GROUND")
ck(g253.C_PY_GROUND is True, "2.53 runs WITH C_PY_GROUND")
ck(g252.C_RULE_GROUND is False and g253.C_RULE_GROUND is False,
   "frozen 2.41 C_RULE_GROUND is silent at 2.52 and 2.53 (separate function/flag/events)")

# the call-site predicate, proved at module level, not only via the helper:
def call_site_applies(mod):
    return bool(mod.C_PY_GROUND)


ck(not call_site_applies(g252) and call_site_applies(g253),
   "call-site predicate: OFF at 2.52, ON at 2.53")

cg = load_cg("0.0.2.53")


def call_site(prompt, text, mod=None):
    """The REAL gate_run 2.53 helper (NOT a mirror — the mirror let a wiring bug ship to
    smoke): (out_text, event-or-None). The event must be the bare registered name."""
    return (mod or g253).c_py_ground_answer("C", {"prompt": prompt}, text)


# ---------------------------------------------------------------- 2. bank census
def bankmap(p):
    return {t["id"]: t for t in json.load(open(p, encoding="utf-8"))}


b62 = bankmap(ROOT / "benchmarks/hard/bank-hard-v6.2.json")
b66 = bankmap(ROOT / "benchmarks/hard/bank-hard-v6.6.json")

# the control stamp's real helper must be inert: no event, answer bytes intact
_inert = "Разбор.\nОТВЕТ: A,C,D\n"
_io, _ie = call_site(b66["C-ex6-02"]["prompt"], _inert, mod=g252)
ck(_ie is None and _io == _inert,
   "the REAL helper is inert at 2.52 (pair-250 control): no event, bytes intact")
ck(json.dumps(b62["C-ex6-02"], sort_keys=True, ensure_ascii=False)
   == json.dumps(b66["C-ex6-02"], sort_keys=True, ensure_ascii=False),
   "C-ex6-02 task bytes byte-identical v6.2 -> v6.6 (chronic map transfers)")
for name, bank in (("v6.2", b62), ("v6.6", b66)):
    parsed = {}
    for tid, t in bank.items():
        if not tid.startswith("C-"):
            continue
        d = cg.ground_py_options(t.get("prompt") or "")
        if d is not None:
            parsed[tid] = d
    ck(set(parsed) == {"C-ex6-02"},
       "shape-C census on bank %s parses EXACTLY {C-ex6-02}, got %r" % (name, parsed))
    gold = tuple(sorted((bank["C-ex6-02"].get("ref") or {}).get("letters") or []))
    ck(parsed["C-ex6-02"] == gold,
       "derived set on C-ex6-02 (bank %s) equals the executed-truth-table gold %r, got %r"
       % (name, gold, parsed["C-ex6-02"]))

# frozen 2.41 grammar must NOT parse this prompt either (its own docstring's py gap):
old = load_cg("0.0.2.41")
ck(old.ground_set_from_prompt(b66["C-ex6-02"]["prompt"]) is None,
   "the frozen 2.41 ground_set_from_prompt still refuses the py-shape prompt (bytes frozen)")

# ---------------------------------------------------------------- 3. published-bytes replay
DIRS = ("cadence-246", "pair-246", "pair-247", "pair-248", "pair-249")
prompt62 = b62["C-ex6-02"]["prompt"]
gold62 = tuple(sorted(b62["C-ex6-02"]["ref"]["letters"]))
rows_seen = fails = passes = 0
for d in DIRS:
    dd = V6R / d
    for rf in sorted(dd.glob("results-*.jsonl")):
        stem = rf.name[len("results-"):-len(".jsonl")]
        lf = dd / ("ledger-%s.jsonl" % stem)
        if not lf.exists():
            continue
        led = {}
        for ln in open(lf, encoding="utf-8"):
            if ln.strip():
                r = json.loads(ln)
                led[(r["task"], r.get("rep"))] = r
        for ln in open(rf, encoding="utf-8"):
            if not ln.strip():
                continue
            r = json.loads(ln)
            if r["task"] != "C-ex6-02":
                continue
            k = (r["task"], r.get("rep"))
            l = led.get(k)
            if l is None:
                continue
            rows_seen += 1
            strict = float(l.get("content") or 0) == 1.0 and bool(l.get("format_ok"))
            out, ev = call_site(prompt62, r.get("answer") or "")
            if strict:
                passes += 1
                ck(out == (r.get("answer") or "") and ev == "v53_c_py_matched",
                   "strict-pass C-ex6-02 row %s/%s is byte-identical (matched only)" % (d, stem))
            else:
                fails += 1
                ck(ev == "v53_c_py_from_prompt",
                   "strict-fail C-ex6-02 row %s/%s converts with the v53 from_prompt event" % (d, stem))
                m = re.search(r"^\s*ОТВЕТ\s*:(.*)$", out, re.M)
                assert m is not None, "converted answer must carry the ОТВЕТ line"
                got = tuple(sorted(set(re.findall(r"(?<![A-Za-z])([A-F])(?![A-Za-z])", m.group(1)))))
                ck(got == gold62,
                   "converted row %s/%s re-derives the gold set %r, got %r" % (d, stem, gold62, got))
                head = re.sub(r"^\s*ОТВЕТ\s*:.*$", "<LINE>", r.get("answer") or "", flags=re.M)
                head2 = re.sub(r"^\s*ОТВЕТ\s*:.*$", "<LINE>", out, flags=re.M)
                ck(head == head2, "only the ОТВЕТ line changed on %s/%s" % (d, stem))
ck(rows_seen >= 21 and fails >= 18,
   "replay covered the published C-ex6-02 population (rows=%d fails=%d passes=%d)"
   % (rows_seen, fails, passes))

# ---------------------------------------------------------------- 4. refusals (synthetic)
S = "Выбери ПОДХОДЯЩИЕ варианты. Формат ответа: строка 'ОТВЕТ: ' ...\n"
P1 = "Python: какой вариант печатает [4, 5]?\n" + S + \
     "A: sorted({5,4})\nB: [5,4][::-1]\nC: sorted([4,5,4])\nD: [4,5][::1]\n"
ck(cg.ground_py_options(P1) == ("A", "B", "D"),
   "synthetic same-shape prompt derives A,B,D (sorted keeps duplicates: [4,4,5] != [4,5])")
P2 = P1 + "E: [4, 5]\n"  # contiguous extension still parses
ck(cg.ground_py_options(P2) == ("A", "B", "D", "E"), "contiguous letter extension parses")
ck(cg.ground_py_options("A: X\nB: Y\n" + P1) is None, "free-name option -> whole prompt refuses")
ck(cg.ground_py_options(P1.replace("D: [4,5][::1]", "D: open('x')")) is None, "unsafe call refuses")
ck(cg.ground_py_options(P1.replace("D: [4,5][::1]", "D: [i for i in [4,5]]")) is None,
   "comprehension refuses")
ck(cg.ground_py_options(P1.replace("D: [4,5][::1]", "D: (4,5).index(4)")) is None,
   "attribute access refuses")
ck(cg.ground_py_options(P1.replace("D: [4,5][::1]", "D: 1/0")) is None,
   "an option raising while evaluating refuses the WHOLE prompt")
ck(cg.ground_py_options(P1 + "\nпечатет ещё и [1]?\n") is not None,
   "single target literal still parses (sanity)")
ck(cg.ground_py_options(P1.replace("[4, 5]?", "[4, 5]? и еще печатает [1]?")) is None,
   "a second target literal is ambiguous -> refuses")
NOP = "какой вариант подходит?\n" + S + "A: sorted({5,4})\nB: [5,4][::-1]\n"
ck(cg.ground_py_options(NOP) is None, "no printed target literal -> refuses")
GAPS = "какой вариант печатает [4, 5]?\n" + S + "A: sorted({5,4})\nC: [5,4][::-1]\n"
ck(cg.ground_py_options(GAPS) is None, "non-contiguous option letters refuse")
ck(cg.ground_py_options(P1.replace("D: [4,5][::1]", "D: (5, 4)[::-1]")) == ("A", "B"),
   "strict type equality: a tuple printing like the list target does NOT match (list != tuple)")

# matched/no-op branch on the real answer bytes
ans = "Разбор.\nОТВЕТ: A,B,C,D\n"
out, ev = call_site(b66["C-ex6-02"]["prompt"], ans)
ck(out == ans and ev == "v53_c_py_matched", "already-correct real answer: matched event, bytes intact")
ans2 = "Разбор.\nОТВЕТ: A,C,D\n"
out2, ev2 = call_site(b66["C-ex6-02"]["prompt"], ans2)
_m2 = re.search(r"^\s*ОТВЕТ\s*:(.*)$", out2, re.M)
ck(ev2 == "v53_c_py_from_prompt" and _m2 is not None
   and tuple(sorted(set(re.findall(r"(?<![A-Za-z])([A-F])(?![A-Za-z])", _m2.group(1))))) == gold62,
   "the published single-mode wrong answer re-derives to the gold set")
ck(out2.startswith("Разбор.\n"), "answer body before the ОТВЕТ line is untouched")

print("gate_v67 PASS: %d checks | C python-literal grounding: matrix 2.52 off / 2.53 on, "
      "frozen 2.41 silent, census EXACTLY {C-ex6-02} on v6.2+v6.6 with derived==gold, "
      "published replay rows=%d fails=%d passes=%d all attributable, refusals closed"
      % (CHECKS, rows_seen, fails, passes))
