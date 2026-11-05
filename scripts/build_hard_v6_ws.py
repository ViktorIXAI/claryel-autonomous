"""Build the v6 hard-run workspace (NO runs; ready-to-launch on owner GO).

Usage: python3 scripts/build_hard_v6_ws.py [outdir]  (default ~/parb-2005-hardv6)
Creates: bank.json (77 tasks from bank-hard-v6.json), plan.json (77 x rep0,
single-shot for plain tasks; D-loop tasks flagged mode=loop for the loop driver),
check_v6_shim.py (overrides scorer dispatch to parb_check_v6), gate/copied
harness files pinned by MANIFEST, RUN-README.md stating the launch commands and
the GO requirement.
"""
import hashlib
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser("~/parb-2005-hardv6")

bank_src = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
bank = json.load(open(bank_src, encoding="utf-8"))
assert len(bank) == 77
os.makedirs(OUT, exist_ok=True)
json.dump(bank, open(os.path.join(OUT, "bank.json"), "w", encoding="utf-8"), ensure_ascii=False)

plan = []
for t in bank:
    g = int(hashlib.sha256(t["id"].encode()).hexdigest()[:6], 16)
    plan.append({"task": t["id"], "cat": t["cat"], "rep": 0, "rep_group": "hardv6",
                 "level": "ex6", "gseed": g,
                 "mode": "loop" if (t["cat"] == "D" and t.get("mode") == "loop") else "plain"})
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"))

shim = '''"""Scorer shim: dispatch every category to parb_check_v6 semantics."""
import parb_check_v6 as V6
import parb_check as BASE


def check(task, ans):
    return V6.check(task, ans)


def check_D_loop(task, art_rows):
    # art_rows: list of raw step answer strings in driver order
    return V6.check_D_loop_v6(task, art_rows)


# re-export the rest so gate_run imports keep working
for _n in dir(BASE):
    if not _n.startswith("_") and _n not in ("check", "check_D_loop"):
        globals()[_n] = getattr(BASE, _n)
'''
open(os.path.join(OUT, "check_v6_shim.py"), "w").write(shim)

for f in ("parb_check_v6.py", "parb_bank_v6.py"):
    shutil.copy2(os.path.join(ROOT, "harness", f), os.path.join(OUT, f))

readme = """# Hard-v6 run workspace

Inputs are hash-pinned in benchmarks/hard/MANIFEST.sha256 of the repo
(see benchmarks/hard/MANIFEST.v6.sha256 for current bank/scorer/sandbox pins).
Scoring goes through check_v6_shim.py -> parb_check_v6 (semantic; D loop via
check_D_loop_v6). Injection flags must stay OFF (contour >= 0.0.2.14 default).

LAUNCH ONLY AFTER THE OWNER'S EXPLICIT GO (issue #15). Planned arms:
  contour (local, 0.0.2.14) -> single rep, contour first per owner order
  basalt raw  -> strict single-shot, v6 checkers
  codex raw / grok raw -> same bank, same checkers
Results filenames are not .gitignore-blocked: results-<arm>-v6.jsonl.
"""
open(os.path.join(OUT, "RUN-README.md"), "w").write(readme)
print("workspace:", OUT)
print("bank sha16:", hashlib.sha256(open(os.path.join(OUT, "bank.json"), "rb").read()).hexdigest()[:16])
print("plan rows:", len(plan), "loop:", sum(1 for p in plan if p["mode"] == "loop"))
