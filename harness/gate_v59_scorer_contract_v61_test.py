#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scorer contract v6.1: the published scoring bytes are frozen and provable.

Contract v6.1 is the scorer that produced every hard-v6 number up to contour
0.0.2.44. It has no version identity of its own (that is what v6.2 adds), so this
test pins it from the OUTSIDE: the registry must carry exactly the bytes that are
published, the published manifest must agree with the registry, and re-scoring
published answer bytes with the registry's dispatch must reproduce the stored
scores. If any of the three drifts, "strict pass" no longer means what the
scoreboards say it means, and the release must fail closed here rather than in an
audit six pairs later.

Checks:
1. registry shape + strict rule string + seed protocol published
2. verify_contract("v6.1") passes on the repo copy and on the run workspace
3. tamper: one wrong pinned hash raises ContractDrift (the guard is real)
4. MANIFEST.v6.sha256 agrees with the registry pins (one identity, no two books)
5. replay: published rows re-score byte-identically (sanitized rows counted, not
   silently forgiven)
6. every note code in published rows is typed; no free-text leftovers
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


def sha16(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


# ---------------------------------------------------------------- 1. registry
ck(SC.SCORER_CONTRACT in SC.CONTRACT_HISTORY, "current contract is registered")
ck(SC.CONTRACT_HISTORY == ("v6.1", "v6.2"), "contract history is explicit")
for cid in SC.CONTRACT_HISTORY:
    ck(cid in SC.CONTRACT_MODULES and cid in SC.CONTRACT_STATUS, "%s has module + status" % cid)
    ck(bool(SC.CONTRACT_PINS[cid]), "%s pins at least one module" % cid)
ck(SC.STRICT_RULE == "content == 1.0 and format_ok",
   "strict rule string is the published one (changing it means a NEW contract)")
ck(SC.SEED_PROTOCOL == "sp1" and "sha256" in SC.SEED_PROTOCOL_TEXT,
   "seed protocol identity is published, not implied")

# ------------------------------------------- 2. verify on repo copy and in a ws
pins61 = SC.verify_contract("v6.1")
ck(pins61["parb_check_v6.py"] == SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"],
   "repo parb_check_v6.py matches its pin")
for name, h in SC.verify_contract("v6.1", extra=[os.path.expanduser("~/parb-v61-contour")]).items():
    ck(len(h) == 16, "workspace contract module %s resolves and hashes" % name)

# ----------------------------------- 2b. the run workspace is checked BY CONTENT
# `module_path` resolves through `search_dirs`, which lists the repo harness first, so
# asking it about a workspace silently re-reads the repo copy — the check below would
# have passed even with a corrupt workspace. The first 0.0.2.45 arm proved the real
# failure mode: in a generated workspace the frozen loop module sits in
# `parb_loop_mech.py` while the GENERATED ADAPTER owns the name `parb_loop.py`, so a
# filename-first hash compares the adapter against the frozen pin and dies with
# CONTRACT DRIFT before the endpoint is reserved. Both facts are pinned here.
for _ws in (os.path.expanduser("~/parb-v61-contour"), os.path.expanduser("~/parb-v62-contour")):
    if not os.path.isdir(_ws):
        continue
    _ws_name = "v6.2 workspace" if _ws.endswith("v62-contour") else "v6.1 workspace"
    ck(sha16(os.path.join(_ws, "parb_check_v6.py")) == SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"],
       "%s carries the frozen scorer bytes verbatim" % _ws_name)
    ck(sha16(os.path.join(_ws, "parb_loop_mech.py")) == SC.CONTRACT_PINS["v6.1"]["parb_loop.py"],
       "%s carries the frozen loop module as parb_loop_mech.py" % _ws_name)
    ck(sha16(os.path.join(_ws, "e_sandbox.py")) == SC.CONTRACT_PINS["v6.1"]["e_sandbox.py"],
       "%s carries the frozen sandbox verbatim" % _ws_name)
    ck(sha16(os.path.join(_ws, "parb_loop.py")) != SC.CONTRACT_PINS["v6.1"]["parb_loop.py"],
       "%s: `parb_loop.py` is generated adapter glue, NOT the pinned module "
       "(it is pinned in WS-GENERATED.v6*.sha256 instead)" % _ws_name)
    ck(SC.verify_contract("v6.1", extra=[_ws])["parb_loop.py"] == SC.CONTRACT_PINS["v6.1"]["parb_loop.py"],
       "%s verifies through the mech copy (the arm that used to die here now starts)" % _ws_name)
    for _p in SC.MODULE_ALIASES["parb_loop.py"]:      # declaration order = resolution order
        if os.path.exists(os.path.join(_ws, _p)):
            ck(_p == "parb_loop_mech.py",
               "%s: the alias that resolves first must be the verbatim copy, got %s" % (_ws_name, _p))
            break

# ------------------------------------------------------------------ 3. tamper
_real = SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"]
SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"] = "0" * 16
try:
    SC.verify_contract("v6.1")
    ck(False, "a wrong pinned hash must raise ContractDrift")
except SC.ContractDrift as e:
    ck("pinned" in str(e) and "on disk" in str(e),
       "ContractDrift names pinned vs on-disk hashes (%s)" % str(e)[:80])
finally:
    SC.CONTRACT_PINS["v6.1"]["parb_check_v6.py"] = _real
ck(SC.verify_contract("v6.1")["parb_check_v6.py"] == _real, "registry restored after tamper")

# ------------------------------------------------------- 4. manifest agreement
man = {}
for ln in open(ROOT / "benchmarks/hard/MANIFEST.v6.sha256", encoding="utf-8"):
    parts = ln.split()
    if len(parts) >= 2 and not ln.startswith("#"):
        man[parts[1]] = parts[0]
for name, sha16_pin in SC.CONTRACT_PINS["v6.1"].items():
    key = "harness/" + name
    if key in man:
        ck(man[key].startswith(sha16_pin),
           "MANIFEST.v6 %s (%s...) == registry pin %s (one identity, two files is drift)"
           % (key, man[key][:16], sha16_pin))
    else:
        ck(name in ("parb_loop.py",),
           "%s not in MANIFEST.v6: a deciding scorer module must be pinned there" % name)

# ------------------------------------------------------------------- 5. replay
BASE = ROOT / "benchmarks/hard/v6-results"
bank = {t["id"]: t for t in json.load(open(ROOT / "benchmarks/hard/bank-hard-v6.json",
                                           encoding="utf-8"))}
V6 = SC.load_contract("v6.1")
DISPATCH = {"A": V6.check_json_obj, "B": V6.check_json_obj, "C": V6.check_C_v6,
            "D": V6.check_D_plain_v6, "F": V6.check_F_v6, "G": V6.check_G_v6,
            "H": V6.check_H_v6, "I": V6.check_json_obj, "J": V6.check_J_v6,
            "K": V6.check_K_v6}
FILES = ["pair-245/results-q43r0.jsonl", "pair-244/results-p43r1.jsonl",
         "pair-240/results-m40r2.jsonl"]
replayed = masked = skipped = 0
for rel in FILES:
    path = BASE / rel
    ck(path.exists(), "published artifact present for replay: %s" % rel)
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        r = json.loads(ln)
        t = bank.get(r["task"])
        if t is None or t["cat"] == "E" or (t["cat"] == "D" and t.get("mode") == "loop"):
            skipped += 1          # E needs the sandbox battery, loop needs trajectories
            continue
        ans = r.get("answer") or ""
        if any(m in ans for m in ("<LOCAL_PATH>", "<LAN_IP>", "<HOST>")):
            masked += 1           # publication masking changed the bytes; not a scoring bug
            continue
        c, f, _ = DISPATCH[t["cat"]](t, ans)
        replayed += 1
        ck(abs(float(r["content"]) - float(c)) < 1e-9 and bool(r["format_ok"]) == bool(f),
           "stored score reproduced for %s in %s (stored %s/%s, replay %s/%s)"
           % (r["task"], rel, r["content"], r["format_ok"], c, f))
ck(replayed >= 150, "replay covered a real sample of published rows (%d)" % replayed)

# ------------------------------------------------------- 6. typed-code closure
seen = set()
for ln in open(BASE / FILES[0], encoding="utf-8"):
    r = json.loads(ln)
    for n in (r.get("notes") or []):
        seen.add(SC.code_of(n))
unclassified = sorted(c for c in seen if SC.classify(c) == "unclassified")
ck(not unclassified, "every note code in published rows is typed (%s)" % unclassified[:6])
ck(SC.classify("banned_attempted") == "protocol"
   and SC.classify("set_mismatch") == "content"
   and SC.classify("false_completion_claim") == "integrity"
   and SC.classify("engine_stalled") == "infra",
   "the four failure classes are distinguished")

# every note code the frozen scorer can emit must be typed: a new scorer note
# without a registered class breaks CI instead of polluting the failure map
import re  # noqa: E402
src = open(HERE / "parb_check_v6.py", encoding="utf-8").read()
emitted = set()
for pat in (r'notes\.append\(\s*"([a-z_][a-z0-9_]*)', r'\breturn\s+[^\n]*?\[\s*"([a-z_][a-z0-9_]*)',
            r'notes \+= \["([a-z_][a-z0-9_]*)', r'\]\s*\+\s*\["([a-z_][a-z0-9_]*)'):
    emitted |= set(re.findall(pat, src))
missing = sorted(c for c in emitted if SC.classify(c) == "unclassified")
ck(not missing, "every note the frozen scorer emits is classified (%s)" % missing[:8])

print("gate_v59 scorer contract v6.1: %d checks PASS "
      "(replay %d rows byte-identical, %d masked rows skipped, %d rows not replayable offline)"
      % (CHECKS, replayed, masked, skipped))
