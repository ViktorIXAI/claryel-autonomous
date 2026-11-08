#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item P0 (contour parity): stage a PUBLIC-benchmark workspace for the frozen runtime.

What this is. The owner asked for a with-harness row on every published public set, produced by
the FROZEN contour runtime `0.0.2.56` (tag `stable-hard-0.0.2.56`) over the SAME pinned task
ids, and scored by the SAME public checker contract. This script stages that workspace the way
`scripts/build_hard_v6_ws.py` stages a hard-bank one: the harness modules are copied verbatim,
including the frozen deciding bytes the runner's contract guard hashes (`parb_check_v6.py`,
`parb_loop.py`, `e_sandbox.py`). No new contour stamp and no new contour feature is registered
here — the stamp is pinned to the frozen line and the runner itself refuses any unregistered
stamp before the endpoint is reserved.

The one deliberate difference: a public task gets category "P". `gate_run`'s contour routing is
keyed to the hard-bank families A..K, so a "P" task reaches only the generic ladder path and no
hard-bank family grammar (Russian invoice fields, coverage-choice nudges, plan gates) is grafted
onto a public prompt. Scoring goes through the public checker module (`scripts/pub_bench_score.py`,
loaded by path), i.e. the same bytes that decided the bare row. If the frozen runtime cannot
serve a public class at all, that refusal is the published finding — no contour row is faked.

Usage: pub_bench_contour_ws.py <bench> <limit> [out-dir]
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HARN = os.path.join(REPO, "harness")
STAMP = "0.0.2.56"                      # the frozen line; a newer stamp is not allowed here
# The runner fail-closes unless these deciding bytes are present unmodified; the builder
# checks them first so a launch is never burned on a staging mistake.
PINS = {"parb_check_v6.py": "89437d8cfe1fc6c8",
        "parb_loop.py": "f5f5b78ab46a0f0c",
        "e_sandbox.py": "424c04126e9b6c1e"}
MODULES = ("gate_run.py", "gate_versioning.py", "gate_engine_guard.py", "gate_j_rerank.py",
           "gate_c_ground.py", "gate_fixers.py", "gate_scorer_contract.py",
           "gate_bank_versions.py", "os_record.py", "parb_check.py", "parb_check_v6.py",
           "parb_check_v6_2.py", "parb_loop.py", "e_sandbox.py")

SHIM = '''

# ---- public-benchmark validator shim (workspace-only, written by pub_bench_contour_ws.py) ----
# Category "P" is a public benchmark task: gate_run's contour routing is keyed to the hard-bank
# families A..K, so a "P" task reaches only the generic ladder path and no family grammar is
# grafted onto a public prompt. The verdict is decided by the PUBLIC checker contract (the same
# bytes that scored the bare arm), not by the hard-bank scorers. format_ok is fixed to 1 because
# the public contract has no separate format axis, so strict (content == 1.0 and format_ok) is
# exactly the public verdict.
import hashlib as _shim_hashlib
import importlib.util as _shim_ilu
_PUB_SCORE_PATH = @@PUBPATH@@
_spec = _shim_ilu.spec_from_file_location("pub_bench_score_shim", _PUB_SCORE_PATH)
PBS = _shim_ilu.module_from_spec(_spec)
_spec.loader.exec_module(PBS)
PUB_CHECKER_CONTRACT = PBS.CHECKER_CONTRACT
PUB_SCORER_SHA16 = _shim_hashlib.sha256(open(_PUB_SCORE_PATH, "rb").read()).hexdigest()[:16]


def check_public(t, text):
    """Public checker verdict mapped onto the harness score slots (documented above)."""
    ok = PBS.check(t.get("checker", ""), t.get("gold"), text or "")
    if ok is None:
        return None, None, ["pub_unscored_checker:%s" % t.get("checker", "")]
    if ok:
        return 1.0, 1, ["pub:ok"]
    return 0.0, 1, ["pub:mismatch"]


CHECK["P"] = check_public
'''


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    bench, limit = sys.argv[1], int(sys.argv[2])
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.expanduser("~/parb-pub-contour/%s" % bench)
    os.makedirs(out, exist_ok=True)
    for m in MODULES:
        shutil.copy2(os.path.join(HARN, m), os.path.join(out, m))
    for name, want in PINS.items():
        got = sha16(os.path.join(out, name))
        if got != want:
            sys.exit("PIN DRIFT %s: contract wants %s, ws has %s" % (name, want, got))
    with open(os.path.join(out, "parb_check.py"), "a", encoding="utf-8") as fh:
        fh.write(SHIM.replace("@@PUBPATH@@",
                              json.dumps(os.path.join(REPO, "scripts", "pub_bench_score.py"))))

    tasks_f = os.path.join(REPO, "benchmarks", "public", "%s.tasks.jsonl" % bench)
    rows = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()][:limit]
    if len(rows) != limit:
        sys.exit("task file holds fewer than %d rows" % limit)
    # Public tasks carry no hard-bank family fields: no sys prompt, no ref, no assembled_doc.
    bank = [{"id": t["id"], "cat": "P", "kind": "public", "level": "pub",
             "prompt": t["prompt"], "checker": t["checker"], "gold": t["gold"],
             "meta": t.get("meta", {}),
             "seed": int(hashlib.sha256(t["id"].encode()).hexdigest()[:6], 16)}
            for t in rows]
    json.dump(bank, open(os.path.join(out, "bank.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    # sp1 seed protocol, identical to the hard bank, so a public pair is cell-comparable
    # the same way: gseed = int(sha256(task|rep)[:8], 16) % 999983.
    plan = [{"task": b["id"], "rep": 0, "series": "main", "rep_group": "pub", "stage": 1,
             "gseed": int(hashlib.sha256(("%s|0" % b["id"]).encode()).hexdigest()[:8], 16) % 999983}
            for b in bank]
    json.dump(plan, open(os.path.join(out, "plan.json"), "w", encoding="utf-8"))

    bank_sha = sha16(os.path.join(out, "bank.json"))
    json.dump({"bank_version": "pub-%s-%d" % (bench, len(bank)),
               "ws_bank_sha16": bank_sha,
               "source": "benchmarks/public/%s.tasks.jsonl (first %d ids, file order)"
                         % (bench, len(bank)),
               "written": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
              open(os.path.join(out, "bank-version.json"), "w", encoding="utf-8"), indent=2)
    sha = subprocess.run(["git", "-C", REPO, "rev-parse", "HEAD"],
                         capture_output=True, text=True).stdout.strip()
    open(os.path.join(out, "HARNESS_GIT_SHA"), "w").write(sha + "\n")
    ident = {"contour_stamp": STAMP, "harness_git_sha": sha,
             "tasks_file": "benchmarks/public/%s.tasks.jsonl" % bench,
             "tasks_file_sha16": sha16(tasks_f), "tasks": len(bank),
             "bank_ws_sha16": bank_sha, "plan_sha16": sha16(os.path.join(out, "plan.json")),
             "seed_protocol": "sp1 (gseed = int(sha256(task|rep)[:8],16) % 999983)",
             "validator": {"contract": "pub-checkers-v2",
                           "module": "scripts/pub_bench_score.py",
                           "sha16": sha16(os.path.join(REPO, "scripts", "pub_bench_score.py"))},
             "frozen_scorer_bytes_present": PINS,
             "ws_modules": {m: sha16(os.path.join(out, m)) for m in MODULES}}
    json.dump(ident, open(os.path.join(out, "WS-IDENTITY.json"), "w", encoding="utf-8"), indent=2)
    print("ws ready:", out)
    print("stamp", STAMP, "tasks", len(bank), "bank", bank_sha,
          "tasks-file", ident["tasks_file_sha16"], "harness", sha[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
