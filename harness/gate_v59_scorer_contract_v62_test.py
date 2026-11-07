#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorer contract v6.2: identity + typed codes + two axes, with ZERO re-scoring.

v6.2 must be strictly additive. If it changed any strict outcome, the published
v6.1 scoreboard would stop being comparable to the new arms and the "version every
element" rule would have been used to rewrite history. So the contract test asserts
equality cell by cell over published answer bytes, then pins what v6.2 actually
adds: the contract id in every row, the typed-code registry, and the two published
axes with their faithful loop decomposition.

Checks:
1. v6.1 and v6.2 dispatch are the same function objects on published rows
   (content, format_ok, notes identical), strict identical everywhere
2. the v6.2 module refuses to load if the frozen scorer bytes move (delegation is
   verified, not assumed)
3. score_row stamps contract id + contract hash + strict rule + seed protocol
4. axes are additive: axes.strict == frozen strict for every sampled row
5. loop-D decomposition is faithful: the frozen weights + published notes
   reproduce the stored content, and a banned-attempt row shows answer=1 /
   protocol=0 (the case one blended number hides)
6. v6.2 wrapper bytes are pinned in MANIFEST.v6.sha256
7. every published note code maps to a registered typed class
"""
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))

import gate_scorer_contract as SC  # noqa: E402

CHECKS = 0


def ck(cond, msg):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL: %s" % msg)
        raise SystemExit(1)


# ---------------------------------------------------------------- load both
v61 = SC.load_contract("v6.1")
v62 = SC.load_contract("v6.2")
ck(v62.SCORER_CONTRACT == "v6.2", "v6.2 module declares its contract id")
ck(not hasattr(v61, "SCORER_CONTRACT"),
   "v6.1 has no identity of its own — that is exactly the gap v6.2 closes")
_FROZEN_NAMES = {"A": "check_json_obj", "B": "check_json_obj", "C": "check_C_v6",
                 "D": "check_D_plain_v6", "F": "check_F_v6", "G": "check_G_v6",
                 "H": "check_H_v6", "I": "check_json_obj", "J": "check_J_v6",
                 "K": "check_K_v6"}
for cat in "ABCDFGHIJK":
    fn = getattr(v62, "CHECK")[cat]
    ck(fn.__name__ == _FROZEN_NAMES[cat] and fn.__module__.startswith("parb_check_v6"),
       "category %s dispatch delegates to the frozen scorer, it is not a local copy "
       "(%s.%s)" % (cat, fn.__module__, fn.__name__))
ck(v62.check_D_loop_v6.__module__.startswith("parb_check_v6"),
   "loop scorer delegates to the frozen module")
ck(v62.BASE_CONTRACT == "v6.1" and v62.BASE_MODULE == "parb_check_v6.py",
   "v6.2 declares which frozen contract it delegates to")

# delegation is verified: move a frozen byte and the v6.2 module must refuse
_real = SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"]
SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"] = "f" * 16
try:
    SC.load_contract("v6.2", extra=[])
    ck(False, "v6.2 must refuse to load when the frozen scorer bytes drift")
except SC.ContractDrift:
    ck(True, "v6.2 refuses to load on frozen-scorer drift")
finally:
    SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"] = _real

# ------------------------------------------------------- 1/3/4. row-by-row replay
BASE = ROOT / "benchmarks/hard/v6-results"
bank = {t["id"]: t for t in json.load(open(ROOT / "benchmarks/hard/bank-hard-v6.json",
                                           encoding="utf-8"))}
FILES = ["pair-245/results-q43r0.jsonl", "pair-245/results-q44r1.jsonl",
         "pair-244/results-p43r0.jsonl", "pair-240/results-m40r1.jsonl"]
ident = masked = 0
strict_flips = 0
codes_seen = set()
axes = {}
for rel in FILES:
    path = BASE / rel
    ck(path.exists(), "published artifact present: %s" % rel)
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        t = bank.get(r["task"])
        if t is None or t["cat"] == "E" or (t["cat"] == "D" and t.get("mode") == "loop"):
            continue
        ans = r.get("answer") or ""
        if any(m in ans for m in ("<LOCAL_PATH>", "<LAN_IP>", "<HOST>")):
            masked += 1
            continue
        c1, f1, n1 = v62.CHECK[t["cat"]](t, ans)
        c2, f2, n2 = getattr(v61, _FROZEN_NAMES[t["cat"]])(t, ans)
        ident += 1
        ck((c1, bool(f1), list(n1)) == (c2, bool(f2), list(n2)),
           "v6.1 and v6.2 disagree on %s (%s vs %s)" % (r["task"], (c1, f1, n1), (c2, f2, n2)))
        row = v62.score_row(dict(t, rep=r.get("rep")), ans)
        frozen_strict = 1 if (float(c1) == 1.0 and f1) else 0
        strict_flips += int(row["strict"] != frozen_strict)
        ck(row["axes"]["strict"] == bool(frozen_strict),
           "axes.strict stays frozen-identical on %s" % r["task"])
        ck(row["scorer_contract"] == "v6.2" and len(row["contract_sha16"]) == 16
           and row["strict_rule"] == SC.STRICT_RULE and row["seed_protocol"] == "sp1",
           "score_row carries full scorer identity (%s)" % r["task"])
        codes_seen |= set(row["codes"])
        axes.setdefault(t["cat"], set()).update(row["axes"].keys())
ck(ident >= 200, "equality replay covered published rows (%d)" % ident)
ck(strict_flips == 0, "v6.2 changed ZERO strict outcomes over %d published rows" % ident)

# -------------------------------------- 5. loop-D decomposition is faithful + useful
loop_rows = 0
recon_ok = 0
mixed_case = 0
for rel in FILES:
    for ln in open(BASE / rel, encoding="utf-8"):
        r = json.loads(ln)
        t = bank.get(r["task"])
        if t is None or not (t["cat"] == "D" and t.get("mode") == "loop"):
            continue
        loop_rows += 1
        ref = t.get("ref") or {}
        lc = SC.loop_criteria(r.get("notes"), must_read_first=bool(ref.get("must_read_first")),
                              must_admit=bool(ref.get("must_admit")), content=r.get("content"))
        if lc["derivable"] and lc["matches_stored_content"] is not None:
            recon_ok += int(lc["matches_stored_content"])
            ck(lc["matches_stored_content"],
               "frozen loop weights + published notes must reproduce stored content on %s "
               "(stored %s, reconstructed %s, notes %s)"
               % (r["task"], r["content"], lc["reconstructed_content"], r.get("notes")))
        a = SC.axes(r["content"], r["format_ok"], r.get("notes"), loop=True, ref=ref)
        ck(a["strict"] == (float(r["content"]) == 1.0 and bool(r["format_ok"])),
           "loop axes.strict matches the frozen strict rule")
        if lc["answer_correct"] and not lc["no_banned_attempt"]:
            mixed_case += 1
            ck(a["answer_axis"] > 0.0 and a["protocol_axis"] < 1.0,
               "answer-right / trajectory-wrong shows BOTH facts for %s" % r["task"])
            ck("banned_attempted" in a["blocking_codes"],
               "the blocking code is typed, not prose (%s)" % r["task"])
ck(loop_rows >= 12, "loop rows sampled (%d)" % loop_rows)
ck(recon_ok == loop_rows, "the frozen loop weights reproduce stored content for every "
                          "published loop row (%d/%d)" % (recon_ok, loop_rows))
ck(mixed_case >= 1, "the answer/protocol split is exercised on a real published row")

# ------------------------------------------------------------ 6. wrapper pins
man = {}
for ln in open(ROOT / "benchmarks/hard/MANIFEST.v6.sha256", encoding="utf-8"):
    parts = ln.split()
    if len(parts) >= 2 and not ln.startswith("#"):
        man[parts[1]] = parts[0]
import hashlib  # noqa: E402
for name in SC.CONTRACT_WRAPPERS["v6.2"]:
    key = "harness/" + name
    ck(key in man, "%s is pinned in MANIFEST.v6.sha256" % key)
    ck(man[key] == hashlib.sha256(open(ROOT / key, "rb").read()).hexdigest(),
       "%s matches its MANIFEST.v6 pin" % key)

# ----------------------------------------------------- 7. typed-code closure
ck(all(SC.classify(c) != "unclassified" for c in codes_seen),
   "every code seen in published rows is registered (%s)"
   % sorted(c for c in codes_seen if SC.classify(c) == "unclassified")[:6])
ident62 = SC.contract_identity("v6.2")
ident61 = SC.contract_identity("v6.1")
ck(ident61["contract_sha16"] != ident62["contract_sha16"] or ident61["scorer_contract"] != ident62["scorer_contract"],
   "two contract ids never collapse to one identity hash")
print("gate_v59 scorer contract v6.2: %d checks PASS "
      "(%d rows v6.1==v6.2 with 0 strict flips, %d loop rows decomposed faithfully, "
      "%d masked rows skipped)" % (CHECKS, ident, recon_ok, masked))
