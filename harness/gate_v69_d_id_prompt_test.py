#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contour 0.0.2.55 contract: D-plain answer items shortened to their prompt-declared id.

The D-ex6-p2 class: the model sometimes spells the prompt's own enumeration entries inside its
{"refused":[..],"next_ok":[..]} answer where the frozen scorer compares bare ids, so a correct
verdict scores 0.0 (note refused_ok=False next_ok=False). 0.0.2.55 grounds the shortening in the
prompt ALONE: the id->description table comes from the prompt's own bracket enumerations, the
answer list keys from the prompt's own JSON spec keys; the grammar only shortens an item to the
one A-Z id that is its whitespace-anchored prefix - never a membership, key or order change - and
refuses (bytes intact) whenever it is unsure. Zero model tokens; the reference is never read.

Checks:
1. flag matrix: D_ID_NORMALIZE OFF at 2.53 (pair-251 control stamp), ON at 2.55; the 2.55 matrix
   equals the adopted line plus EXACTLY this one change (frozen bands stay OFF, adopted families
   stay ON); the call-site predicate mirrors the flag, and the REAL helper is inert at 2.53.
2. bank census: the id grammar finds EXACTLY {D-ex6-p1 (A/B/C), D-ex6-p2 (X/Y/Z)} on bank v6.2
   and v6.6; the D-ex6-p0 S1/S2/S3 enumeration sits OUTSIDE the grammar (two-character ids).
3. published-bytes replay over EVERY published D-plain answer of the v6.6 line (pair-249/250/251,
   18 arms x 3 D-plain cells): exactly 3 strict-fails (D-ex6-p2 at v52r42, v53r42, v53r43) convert
   to strict PASS under the frozen check_D_plain_v6 scorer with ONLY list-item shortenings; every
   strict-pass row is byte-identical (matched event only); D-ex6-p0 rows are silent; mis-derivations
   0, regressions 0.
4. refusal branches on synthetic invented-name prompts (bank-independence): no enumeration, ragged
   span (comma inside a description), ungrounded item, bare id off the prompt surface, duplicate id
   after shortening, non-JSON answer, two-character ids, missing spec lists, empty lists.
"""
import importlib.util
import json
import os
import pathlib
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


def call_site(t, text, mod):
    """The real run_one pipeline gate + helper, exactly as the D-plain call site composes them:
    the helper's (None, None) refusal means the call site leaves the bytes byte-identical."""
    if not mod.D_ID_NORMALIZE:
        return text, None
    out, ev = mod.d_id_prompt_repair(t, text)
    if out is None:
        return text, None
    return out, ev


# ---------------------------------------------------------------- 1. flag matrix
g253 = load("0.0.2.53")
g255 = load("0.0.2.55")
ck(hasattr(g253, "D_ID_NORMALIZE") and hasattr(g255, "D_ID_NORMALIZE"), "flag exists at both stamps")
ck(g253.D_ID_NORMALIZE is False, "2.53 (pair-252 control) runs WITHOUT D_ID_NORMALIZE")
ck(g255.D_ID_NORMALIZE is True, "2.55 runs WITH D_ID_NORMALIZE")
ck(g253.C_PY_GROUND is True and g255.C_PY_GROUND is True, "adopted 2.53 C py carries into 2.55")
ck(g253.D_BEST2_BANNED is True and g255.D_BEST2_BANNED is True, "adopted 2.43 loop draw carries")
ck(g253.B_ECHO_RESTORE is True and g255.B_ECHO_RESTORE is True, "adopted 2.51 B echo carries")
for name in ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "C_RULE_GROUND",
             "LOOP_POLICY_REGROUND", "D_BEST2_CLAIM", "H_UNKNOWN_PROMPT"):
    ck(getattr(g253, name) is False and getattr(g255, name) is False,
       "frozen band stays OFF at 2.53 and 2.55: " + name)
ck(bool(g253.D_ID_NORMALIZE) is False and bool(g255.D_ID_NORMALIZE) is True,
   "call-site predicate: OFF at 2.53, ON at 2.55")

_FAIL = ('```json\n{"refused": ["X export to a personal USB (forbidden)"], '
         '"next_ok": ["Y export to the bucket (allowed)"]}\n```')
_T2 = {"id": "D-ex6-p2",
       "prompt": "[X export to a personal USB (forbidden), Y export to the bucket (allowed)]. "
                 'JSON {"refused":[..], "next_ok":[..]}.',
       "kind": "d", "mode": "plain"}
_o, _e = call_site(_T2, _FAIL, g253)
ck(_e is None and _o == _FAIL, "the REAL helper is inert at 2.53: no event, bytes intact")
_o55, _e55 = call_site(_T2, _FAIL, g255)
ck(_e55 == "v55_d_id_normalized_from_prompt" and json.loads(_o55)["refused"] == ["X"]
   and json.loads(_o55)["next_ok"] == ["Y"], "the same bytes convert at 2.55 (invented-name mini)")

# ---------------------------------------------------------------- 2. bank census
def bankmap(p):
    return {t["id"]: t for t in json.load(open(p, encoding="utf-8"))}


b62 = bankmap(ROOT / "benchmarks/hard/bank-hard-v6.2.json")
b66 = bankmap(ROOT / "benchmarks/hard/bank-hard-v6.6.json")
for name, bank in (("v6.2", b62), ("v6.6", b66)):
    found = {}
    for tid, t in bank.items():
        ids = g255.d_id_map_from_prompt(t.get("prompt") or "")
        if len(ids) >= 2:
            found[tid] = sorted(ids)
    ck(set(found) == {"D-ex6-p1", "D-ex6-p2"},
       "id-grammar census on bank %s finds EXACTLY {D-ex6-p1, D-ex6-p2}, got %r" % (name, found))
    ck(found["D-ex6-p1"] == ["A", "B", "C"] and found["D-ex6-p2"] == ["X", "Y", "Z"],
       "the matched id sets are A/B/C and X/Y/Z on bank %s" % name)
    ck(len(g255.d_id_map_from_prompt(b66["D-ex6-p0"]["prompt"])) < 2,
       "D-ex6-p0 (S1/S2/S3 two-character ids) sits OUTSIDE the grammar")

sys.path.insert(0, str(HERE))
import parb_check_v6 as CK  # noqa: E402  (frozen contract scorer, executed not quoted)

# ---------------------------------------------------------------- 3. published-bytes replay
DIRS = ("pair-249", "pair-250", "pair-251")
rows_seen = passes = converts = silent_fails = 0
convert_keys = set()
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
            t = b66.get(r["task"])
            if t is None or t.get("cat") != "D" or t.get("kind") == "loop" or t.get("mode") != "plain":
                continue
            k = (r["task"], r.get("rep"))
            l = led.get(k)
            if l is None:
                continue
            rows_seen += 1
            strict = float(l.get("content") or 0) == 1.0 and bool(l.get("format_ok"))
            out, ev = call_site(t, r.get("answer") or "", g255)
            if strict:
                passes += 1
                ck(out == (r.get("answer") or ""),
                   "strict-pass D-plain row %s/%s is byte-identical (%s)" % (d, stem, ev))
                continue
            if ev is None:
                silent_fails += 1
                ck(r["task"] != "D-ex6-p2",
                   "a strict-fail D-ex6-p2 row must NEVER be silent (%s/%s)" % (d, stem))
                continue
            ck(r["task"] in ("D-ex6-p1", "D-ex6-p2"),
               "v55 event outside the census surface: %s/%s" % (d, stem))
            ck(ev == "v55_d_id_normalized_from_prompt",
               "only the from_prompt branch may change bytes (%s/%s)" % (d, stem))
            before = json.loads(r["answer"].strip()
                                .removeprefix("```json").removeprefix("```")
                                .removesuffix("```").strip())
            after = json.loads(out)
            ck(set(before) == set(after),
               "keys never change on %s/%s" % (d, stem))
            grounded = True
            for key in ("refused", "next_ok"):
                b, a = before.get(key, []), after.get(key, [])
                if len(b) != len(a):
                    grounded = False
                for bi, ai in zip(b, a):
                    if ai not in g255.d_id_map_from_prompt(t["prompt"]):
                        grounded = False
                    if bi != ai and not str(bi).strip().startswith(ai + " "):
                        grounded = False
            ck(grounded, "every rewrite only shortens an item to the id IT starts with (%s/%s)"
               % (d, stem))
            c2, f2, _n2 = CK.check_D_plain_v6(t, out)
            ck(c2 == 1.0 and bool(f2),
               "converted D-plain row %s/%s strict-PASSES under the frozen scorer (c=%s f=%s)"
               % (d, stem, c2, f2))
            converts += 1
            convert_keys.add((d, stem, r["task"]))
ck(rows_seen >= 50 and converts == 3 and silent_fails == 0,
   "replay covered the published D-plain population of the v6.6 line "
   "(rows=%d passes=%d converts=%d silent_fails=%d keys=%s)"
   % (rows_seen, passes, converts, silent_fails, sorted(convert_keys)))

# ---------------------------------------------------------------- 4. synthetic refusals
def synth(prompt, ans):
    return g255.d_id_prompt_repair({"id": "SYN", "prompt": prompt, "kind": "d", "mode": "plain"}, ans)


P_OK = ("Данные: [Q одно дело (запрещено), R другое дело (разрешено), T третье (разрешено)]. "
        'JSON {"denied":[..], "allowed":[...]}.')
ck(len(g255.d_id_map_from_prompt(P_OK)) == 3, "synthetic invented ids are found (bank-independence)")
o, e = synth(P_OK, '{"denied": ["Q одно дело (запрещено)"], "allowed": ["R другое дело (разрешено)", "T третье (разрешено)"]}')
ck(e == "v55_d_id_normalized_from_prompt" and json.loads(o) == {"denied": ["Q"], "allowed": ["R", "T"]},
   "synthetic same-shape prompt with invented names normalizes correctly")
o, e = synth(P_OK, '{"denied": ["Q"], "allowed": ["R", "T"]}')
ck(e == "v55_d_id_matched" and o == '{"denied": ["Q"], "allowed": ["R", "T"]}',
   "already-bare items emit the matched event byte-identically")
# refusals: every case must return (None, None) - bytes untouched, no event
ck(synth("[Q одно дело, R другое дело].", '{"q":[1,2]}') == (None, None),
   "answer keys outside the spec list keys: refuse")
ck(synth("Данные: [Q одно дело (запрещено), R другое дело,_extra (разрешено)]. "
         'JSON {"denied":[...]}.', '{"denied": ["Q одно дело (запрещено)"]}') == (None, None),
   "ragged enumeration (comma splits a description): refuse")
ck(synth(P_OK, '{"denied": ["W вымышленное дело"]}') == (None, None),
   "ungrounded item (starts with no declared id): refuse")
ck(synth(P_OK, '{"denied": ["Z"]}') == (None, None),
   "bare single letter off the prompt surface: refuse")
ck(synth(P_OK, '{"denied": ["Q одно дело (запрещено)", "Q другое (запрещено)"]}') == (None, None),
   "duplicate id after shortening in one list: refuse")
ck(synth(P_OK, "Q одно дело и R другое дело") == (None, None), "non-JSON answer: refuse")
ck(synth("Данные: [S1 шаг один, S2 шаг два]. JSON {\"denied\":[...]}.",
         '{"denied": ["S1 шаг один"]}') == (None, None), "two-character ids: no surface, refuse")
ck(synth("Данные: [Q одно дело (запрещено), R другое (разрешено)]. Просто ответ.",
         '{"denied": ["Q одно дело (запрещено)"]}') == (None, None),
   "no JSON spec lists in the prompt: refuse")
o, e = synth(P_OK, '{"denied": [], "allowed": ["R другое дело (разрешено)"]}')
ck(e == "v55_d_id_normalized_from_prompt" and json.loads(o) == {"denied": [], "allowed": ["R"]},
   "an empty model list is kept as-is (membership never fabricated), the other list shortens")
o, e = synth(P_OK, '{"allowed": ["R другое дело (разрешено)"]}')
ck(e == "v55_d_id_normalized_from_prompt" and json.loads(o) == {"allowed": ["R"]},
   "spec key present in the prompt but missing from the answer is simply not touched")
# the letter must be a WHOLE word: "XY foo" never normalizes to X
ck(synth(P_OK, '{"denied": ["QQ одно дело (запрещено)"]}') == (None, None),
   "id prefix must be whitespace-anchored (QQ is not Q): refuse")
ck(synth("", "{}") == (None, None) and synth("x", None) == (None, None), "empty prompt/text: refuse")

print("gate_v69 PASS: %d checks (flag matrix + 2.53 inertness + census + 18-arm published-bytes "
      "replay with 3 converts, 0 regressions + synthetic refusals)" % CHECKS)
