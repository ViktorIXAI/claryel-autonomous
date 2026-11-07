"""Build the v6 hard-run workspace (NO runs; ready-to-launch on owner GO).

Usage: python3 scripts/build_hard_v6_ws.py [outdir]  (default ~/parb-2005-hardv6)

Integration contract (issue #15 item 5, P0-INTEGRATION):
  - workspace `parb_check.py` is an ADAPTER: gate_run's `import parb_check as CK`
    resolves to v6 semantics ONLY (CHECK dict, run_py inside e_sandbox, D-loop
    conversion to check_D_loop_v6). The frozen v5 scorer never lands in the ws.
  - workspace `parb_loop.py`: mechanics re-exported from copied v5 module
    (`parb_loop_mech.py`), scoring strictly via check_D_loop_v6.
  - `e_sandbox.py` copied next to the scorer: E batteries run ONLY in docker
    (fail closed otherwise).
  - RUN-README names the manifests; hashes are never hard-coded here.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import gate_bank_versions as GBV    # bank version identity (release 0.0.2.49)
WRITE_PINS = "--write-pins" in sys.argv
# --bank <file> builds a workspace on a DIFFERENT bank version; --pins <file> keeps that
# workspace's pin set separate, because a bank swap changes the pinned `bank.json` hash and
# must not invalidate the v6.1 pin file (published v6.1 artifacts stay verifiable).
_args = [x for x in sys.argv[1:] if x != "--write-pins"]
BANK_OVERRIDE = None
PINS_OVERRIDE = None
if "--bank" in _args:
    i = _args.index("--bank")
    BANK_OVERRIDE = _args[i + 1]
    _args = _args[:i] + _args[i + 2:]
if "--pins" in _args:
    i = _args.index("--pins")
    PINS_OVERRIDE = _args[i + 1]
    _args = _args[:i] + _args[i + 2:]
OUT = _args[0] if _args else os.path.expanduser("~/parb-2005-hardv6")
# Generated shim/adapter files are hash-pinned here (itself pinned in MANIFEST.v6).
WS_PINS = os.path.join(ROOT, "benchmarks", "hard",
              PINS_OVERRIDE or "WS-GENERATED.v6.sha256")
WS_PINNED = ("parb_check.py", "parb_loop.py", "parb_check_v6.py", "e_sandbox.py",
               "gate_run.py", "gate_versioning.py", "gate_engine_guard.py",
               "parb_bank_v6.py", "parb_loop_mech.py", "bank.json", "plan.json",
               "parb_check_v6_2.py", "gate_scorer_contract.py",
               "gate_bank_versions.py", "bank-version.json")

bank_src = os.path.join(ROOT, "benchmarks", "hard",
             BANK_OVERRIDE or "bank-hard-v6.json")
bank = json.load(open(bank_src, encoding="utf-8"))
assert len(bank) == 77
os.makedirs(OUT, exist_ok=True)
json.dump(bank, open(os.path.join(OUT, "bank.json"), "w", encoding="utf-8"), ensure_ascii=False)

# Bank version identity (release 0.0.2.49): every generated workspace names the
# bank VERSION next to its hash. The registry is checked first — a published bank
# file whose bytes moved without a new version fails the build closed (published
# bytes of a version are immutable; corrections ship as new files). Then the
# resolved version is stamped into the ws as `bank-version.json`, which
# `gate_run` reads back into the run record (2.46 HARNESS_GIT_SHA pattern).
GBV.check_registry(ROOT)
_bank_entry = GBV.resolve_for_file(bank_src, ROOT)
if _bank_entry is None:
    sys.exit("BANK NOT IN REGISTRY: %s is not a versioned published bank in "
             "benchmarks/hard/BANK-VERSIONS.json (name and bytes must match). "
             "Every element carries a version: register a NEW file + NEW version "
             "with its sha16 before building a workspace on it." % os.path.basename(bank_src))
_ws_bank_sha16 = hashlib.sha256(open(os.path.join(OUT, "bank.json"), "rb").read()).hexdigest()[:16]
GBV.write_marker(OUT, _bank_entry, _ws_bank_sha16,
                 time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
print("bank version marker:", _bank_entry["version"],
      "published", _bank_entry["published_sha16"], "-> ws copy", _ws_bank_sha16)

plan = []
for t in bank:
    g = int(hashlib.sha256(t["id"].encode()).hexdigest()[:6], 16)
    plan.append({"task": t["id"], "cat": t["cat"], "rep": 0, "rep_group": "hardv6", "series": "main", "stage": "main",
                 "level": "ex6", "gseed": g,
                 "mode": "loop" if (t["cat"] == "D" and t.get("mode") == "loop") else "plain"})
json.dump(plan, open(os.path.join(OUT, "plan.json"), "w", encoding="utf-8"))

# pull the two frozen regex constants from the v5 scorer so contour fixers
# behave identically without importing any v5 scoring logic
v5 = open(os.path.join(ROOT, "harness", "parb_check.py"), encoding="utf-8").read()
m_unk = re.search(r'^UNK = \(.*?"\)\n', v5, re.S | re.M)
m_claim = re.search(r"^ACTION_CLAIM = .*?$", v5, re.M)
assert m_unk and m_claim, "cannot extract frozen fixer constants from v5 scorer"
unk, claim = m_unk.group(0), m_claim.group(0)

adapter = ('"""v6 workspace scorer adapter: gate_run `import parb_check as CK` lands here.\n'
           'Every score resolves to parb_check_v6; model code executes ONLY in e_sandbox.\n'
           'Generated by scripts/build_hard_v6_ws.py; adapter source is this builder.\n"""\n'
           "import json\n"
           "import re\n\n"
           "import e_sandbox\n"
           "import parb_check_v6 as V6\n\n"
           "check = V6.check\n"
           "check_D_loop_v6 = V6.check_D_loop_v6\n\n"
           "CHECK = {'A': V6.check_json_obj, 'B': V6.check_json_obj, 'C': V6.check_C_v6,\n"
           "         'D': V6.check_D_plain_v6, 'E': V6.run_battery, 'F': V6.check_F_v6,\n"
           "         'G': V6.check_G_v6, 'H': V6.check_H_v6, 'I': V6.check_json_obj,\n"
           "         'J': V6.check_J_v6, 'K': V6.check_K_v6}\n\n"
           "# fixer regex constants copied from the frozen v5 module (constants only)\n"
           + unk + "\n" + claim + "\n\n"
           "_FENCE = re.compile(r\"```(?:\\w+)?\\s*(.+?)```\", re.S)\n"
           "def strip_fence(t):\n"
           "    m = _FENCE.search(t or '')\n"
           "    return m.group(1).strip() if m else (t or '')\n\n"
           "def check_D_loop(t, rec):\n"
           "    rows = []\n"
           "    for s in (rec.get('agent_steps') or []):\n"
           "        p = s.get('parsed')\n"
           "        rows.append(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))\n"
           "    return V6.check_D_loop_v6(t, rows)\n\n"
           "def run_py(code, tests, env, fails=1, detail=False):\n"
           "    \"\"\"v5-signature E runner; executes ONLY inside the e_sandbox container.\"\"\"\n"
           "    payload = (\n"
           "        'import json\\n'\n"
           "        'src = json.loads(%r)\\n'\n"
           "        'TESTS = json.loads(%r)\\n'\n"
           "        'MAXF = %d\\n'\n"
           "        'exec(compile(src, \"sol.py\", \"exec\"))\\n'\n"
           "        'ok = tot = 0\\nerrs = []\\n'\n"
           "        'for _ln in TESTS.splitlines():\\n'\n"
           "        '    if not _ln.strip():\\n        continue\\n'\n"
           "        '    tot += 1\\n'\n"
           "        '    try:\\n        exec(compile(_ln, \"<t>\", \"exec\"), globals())\\n        ok += 1\\n'\n"
           "        '    except Exception as _e:\\n'\n"
           "        '        if len(errs) < MAXF:\\n'\n"
           "        '            errs.append((type(_e).__name__ + \": \" + str(_e))[:120])\\n'\n"
           "        'print(\"RESULT\", ok, \"/\", tot, \" | \".join(errs) if errs else \"нет вывода\")\\n'\n"
           "        % (json.dumps(code), json.dumps(tests), max(1, int(fails)))\n"
           "    )\n"
           "    res = e_sandbox.run_docker(payload, wall_sec=90.0)\n"
           "    for ln in (res.stdout or '').splitlines():\n"
           "        if ln.startswith('RESULT'):\n"
           "            parts = ln.split()\n"
           "            try:\n"
           "                okc, totc = int(parts[1]), int(parts[3])\n"
           "            except Exception:\n"
           "                okc, totc = 0, 1\n"
           "            return okc, totc, (' '.join(parts[4:]) or 'нет вывода')\n"
           "    tail = (res.stderr or '').strip().splitlines() or [res.detail or 'sandbox_failure']\n"
           "    return 0, 1, tail[-1][:120]\n")
open(os.path.join(OUT, "parb_check.py"), "w", encoding="utf-8").write(adapter)

loop_ad = ('"""loop driver adapter: mechanics from copied v5 module; scoring is v6-only."""\n'
           "import json\n\n"
           "from parb_loop_mech import mock_exec, parse_action  # mechanics only, no v5 scorer\n"
           "import parb_check_v6 as V6\n\n"
           "def check_D_loop(t, rec):\n"
           "    rows = []\n"
           "    for s in (rec.get('agent_steps') or []):\n"
           "        p = s.get('parsed')\n"
           "        if p is None and 'gate_block' in s:\n"
           "            rows.append({'tool': s['gate_block'], 'arg': None})\n"
           "            continue\n"
           "        if s.get('gate_rejected'):\n"
           "            rows.append(dict(p, gate_rejected=True) if isinstance(p, dict)\n"
           "                        else {'gate_rejected': True})\n"
           "            continue\n"
           "        rows.append(p if isinstance(p, str) else json.dumps(p, ensure_ascii=False))\n"
           "    return V6.check_D_loop_v6(t, rows)\n")
open(os.path.join(OUT, "parb_loop.py"), "w", encoding="utf-8").write(loop_ad)

# generated-adapter integrity pins (issue #15 review item: shim must be pinned):
# MANIFEST.v6 carries "# generated: <file> sha256=<h>" lines; build fails closed on drift.
man = open(os.path.join(ROOT, "benchmarks/hard", "MANIFEST.v6.sha256"), encoding="utf-8").read()
for fname in ("parb_check.py", "parb_loop.py"):
    got = hashlib.sha256(open(os.path.join(OUT, fname), "rb").read()).hexdigest()
    m = re.search(r"# generated: %s sha256=([0-9a-f]{64})" % re.escape(fname), man)
    if m:
        assert m.group(1) == got, ("generated adapter drift vs MANIFEST.v6 pin", fname, got[:16], m.group(1)[:16])
    print("generated", fname, "sha256", got)

for f in ("parb_check_v6.py", "e_sandbox.py", "parb_bank_v6.py"):
    shutil.copy2(os.path.join(ROOT, "harness", f), os.path.join(OUT, f))
# The scorer contract (v6.2) ships with the workspace: the registry verifies the frozen
# scorer bytes at run start and stamps every row, so the arm's numbers carry their scorer.
for f in ("parb_check_v6_2.py",):
    shutil.copy2(os.path.join(ROOT, "harness", f), os.path.join(OUT, f))
for f in ("gate_run.py", "gate_versioning.py", "gate_engine_guard.py"):
    shutil.copy2(os.path.join(ROOT, "harness", f), os.path.join(OUT, f))
# Copy every harness module the contour imports, not a hand-kept list: the contour grows siblings
# (gate_format_repair, gate_loop_drive, gate_j_rerank, ...) and a forgotten one burns an arm.
for _f in sorted(os.listdir(os.path.join(ROOT, "harness"))):
    if _f.startswith("gate_") and _f.endswith(".py") and "test" not in _f:
        shutil.copy2(os.path.join(ROOT, "harness", _f), os.path.join(OUT, _f))
assert "def plan_loop" in open(os.path.join(OUT, "gate_run.py"), encoding="utf-8").read(), "loop driver missing"
# Fail closed on a workspace that cannot import: contour keeps gaining sibling modules and a
# missing one only shows up as a traceback minutes into an arm (gate_engine_guard did exactly
# that on 2026-11-05, killing an arm after the endpoint was already reserved).
_STDLIB = set(sys.stdlib_module_names)
for _m in re.finditer(r"^(?:from|import)\s+([a-zA-Z_][a-zA-Z0-9_]*)", open(os.path.join(OUT, "gate_run.py"), encoding="utf-8").read(), re.M):
    _mod = _m.group(1)
    if _mod in _STDLIB:
        continue
    if not os.path.exists(os.path.join(OUT, _mod + ".py")):
        sys.exit("WS IMPORT GAP: gate_run imports local module %r, workspace does not carry it" % _mod)
shutil.copy2(os.path.join(ROOT, "harness", "parb_loop.py"), os.path.join(OUT, "parb_loop_mech.py"))

readme = """# Hard-v6 run workspace

Gate artifacts: `bank.json` (built from the bank named in the Bank line at the bottom of
this file), scorer adapter `parb_check.py`
(imports `parb_check_v6` + `e_sandbox`, both copied verbatim; `parb_loop.py` ->
`check_D_loop_v6`). Verify integrity BEFORE any launch:
  python3 <repo>/harness/verify_manifest.py --v6
Injection flags must stay OFF (contour >= 0.0.2.14 default). E batteries execute
only inside docker via e_sandbox (fail closed).

LAUNCH ONLY AFTER THE OWNER'S EXPLICIT GO (issue #15). Planned arms:
  contour (local, current stamp) -> single rep, contour first per owner order
  basalt raw / codex raw / grok raw -> same bank, same v6 scorer via
  scripts/score_answers_v6.py (offline scoring of archived answers)
Results: results-<arm>-v6.jsonl under benchmarks/hard/v6-results/ (not ignored).
"""
readme += ("\nBank line: built from `benchmarks/hard/%s` (sha16 %s). Bank version: **%s** "
           "(status %s, published sha16 %s, ws copy sha16 %s) — identity stamped in "
           "`%s` and pinned. Pins for this workspace: `benchmarks/hard/%s`.\n"
           % (os.path.basename(bank_src),
              hashlib.sha256(open(bank_src, "rb").read()).hexdigest()[:16],
              _bank_entry["version"], _bank_entry.get("status", "?"),
              _bank_entry["published_sha16"], _ws_bank_sha16,
              GBV.MARKER_NAME,
              os.path.basename(WS_PINS)))
open(os.path.join(OUT, "RUN-README.md"), "w").write(readme)   # bank line added above


def _ws_sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def _ws_sha(name):
    return hashlib.sha256(open(os.path.join(OUT, name), "rb").read()).hexdigest()


# Harness provenance for the run record (release 0.0.2.46): a generated run workspace is a
# copy, not a git checkout, so `gate_run.harness_git_sha()` can only be correct if the
# builder stamps the build commit. Deliberately NOT hash-pinned: it is build metadata that
# rotates with every commit, not a scoring byte.
try:
    _hsha = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                           capture_output=True, text=True, timeout=10).stdout.strip()
except Exception:
    _hsha = ""
if re.fullmatch(r"[0-9a-f]{40}", _hsha or ""):
    open(os.path.join(OUT, "HARNESS_GIT_SHA"), "w", encoding="utf-8").write(_hsha + "\n")
    print("harness git sha stamped:", _hsha[:12])
else:
    print("WARNING: not built from a git checkout — workspace gets no HARNESS_GIT_SHA; "
          "arms launched from it will record an unattributed harness")

if WRITE_PINS:
    with open(WS_PINS, "w", encoding="utf-8") as fh:
        fh.write("# generated v6 workspace shim/adapter pins (issue #15 review item 3)\n")
        fh.write("# format: sha256  ws-relative/path; regenerate: build_hard_v6_ws.py <tmp> --write-pins\n")
        for n in WS_PINNED:
            fh.write("%s  %s\n" % (_ws_sha(n), n))
    print("wrote", WS_PINS)
else:
    want = {}
    for ln in open(WS_PINS, encoding="utf-8"):
        parts = ln.split()
        if len(parts) >= 2 and not ln.startswith("#"):
            want[parts[1]] = parts[0]
    drift = [n for n in WS_PINNED if want.get(n) != _ws_sha(n)]
    if drift:
        for n in drift:
            print("WS DRIFT", n, "want", (want.get(n) or "MISSING")[:16], "got", _ws_sha(n)[:16])
        raise SystemExit("generated workspace shim drift vs WS-GENERATED.v6.sha256 (fail closed)")
    print("ws shim pins OK:", len(WS_PINNED), "files; parb_check.py", want["parb_check.py"])
print("workspace:", OUT)
print("bank sha16:", hashlib.sha256(open(os.path.join(OUT, "bank.json"), "rb").read()).hexdigest()[:16])
print("plan rows:", len(plan), "loop:", sum(1 for p in plan if p["mode"] == "loop"))
