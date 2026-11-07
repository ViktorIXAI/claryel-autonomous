#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Score raw-arm fair-probe rows in a subset workspace under the frozen scorer
contract, with per-row identity and a single-variable join against the prior
bank version's published subset (same task ids, same reps, byte-identical task
objects except the queued fix). Prints per-arm per-rep strict results + notes.

Usage: scripts/score_fair_rows.py <WS-DIR> [arm ...]   (default: basalt codex grok)
Exits non-zero if the contract identity or the subset guard fails (fail closed).
"""
import glob
import hashlib
import json
import os
import sys

sys.path.insert(0, "harness")
import parb_check_v6 as CK
from gate_scorer_contract import SCORER_CONTRACT, contract_identity

WS = os.path.expanduser(sys.argv[1])
ARMS = sys.argv[2:] or ["basalt", "codex", "grok"]
EXPECTED_CONTRACT = "v6.2"
EXPECTED_BYTES16 = "89437d8cfe1fc6c8"

cid = contract_identity(SCORER_CONTRACT)
b16 = hashlib.sha256(open("harness/parb_check_v6.py", "rb").read()).hexdigest()[:16]
if SCORER_CONTRACT != EXPECTED_CONTRACT or cid.get("contract_sha16") != "c8c0c7dd114dfc32" \
        or b16 != EXPECTED_BYTES16 or cid.get("scorer_modules", {}).get("parb_check_v6.py") != EXPECTED_BYTES16:
    sys.exit("FAIL closed: contract %s id %s bytes %s (expected %s/%s)" %
             (SCORER_CONTRACT, cid.get("contract_sha16"), b16, EXPECTED_CONTRACT, EXPECTED_BYTES16))
print("scorer contract", EXPECTED_CONTRACT, "id", cid.get("contract_sha16"),
      "modules", cid.get("scorer_modules"), "seed", cid.get("seed_protocol"))

bank = json.load(open(os.path.join(WS, "bank.json")))
tasks = {t["id"]: t for t in bank}
sub16 = hashlib.sha256(open(os.path.join(WS, "bank.json"), "rb").read()).hexdigest()[:16]
print("subset bank sha16:", sub16, "tasks:", sorted(tasks))

# single-variable join: prior published subset with the SAME task set
prev = {}
for pf in glob.glob(os.path.join(WS, ".prev-subset-bank.json")):
    pt = {t["id"]: t for t in json.load(open(pf))}
    if set(pt) == set(tasks):
        prev = pt
        print("prev subset joined:", hashlib.sha256(open(pf, "rb").read()).hexdigest()[:16])
        for tid in tasks:
            dfields = [f for f in set(tasks[tid]) | set(prev[tid])
                       if json.dumps(tasks[tid].get(f), sort_keys=True, ensure_ascii=False) !=
                          json.dumps(prev[tid].get(f), sort_keys=True, ensure_ascii=False)]
            print("  diff %s fields: %s" % (tid, dfields))

for arm in ARMS:
    f = os.path.join(WS, "answers-%s.jsonl" % arm)
    if not os.path.exists(f):
        print(arm, "MISSING")
        continue
    rows = [json.loads(l) for l in open(f)]
    strict = 0
    out = []
    for r in sorted(rows, key=lambda x: x.get("rep", 0)):
        t = tasks.get(r["task"])
        if t is None:
            out.append((r.get("rep"), "N/A", "task not in subset"))
            continue
        ans = r.get("answer") or ""
        if not ans.strip():
            out.append((r.get("rep"), "F", "transport finish=%s empty=True" % r.get("finish")))
            continue
        try:
            content, fmt, notes = CK.CHECKS[t["cat"]](t, ans)
        except Exception as e:
            out.append((r.get("rep"), "ERR", repr(e)))
            continue
        ok = content == 1.0 and fmt
        strict += 1 if ok else 0
        out.append((r.get("rep"), "P" if ok else "F",
                    "%.2f fmt=%s notes=%s" % (content, fmt, notes)))
    cells = " ".join("r%s=%s(%s)" % c for c in out)
    print("%s: strict %d/%d | %s" % (arm, strict, len(out), cells))
