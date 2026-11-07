#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Release 0.0.2.46 contract: the run record names the REAL harness commit.

Cadence-246 shipped run records with `harness_git_sha: ""` — `gate_run` derived it with
`git -C PARB_ROOT`, but a generated run workspace is a copy, not a git checkout. The fix
must be proven, not asserted, and must not disturb any contour byte:

  1. resolution — `harness_git_sha(root)` prefers the `HARNESS_GIT_SHA` file stamped by
     `scripts/build_hard_v6_ws.py` (the only correct source inside a generated ws),
     falls back to `git -C root` (repo checkouts), and fails CLOSED to "" (never a guess);
     a malformed stamp file is rejected by the hex grammar and falls back;
  2. tooling-only — 2.46 registers no contour feature, is outside the reserved band,
     resolves to the same behavior axis as 2.45 (newest registered = 2.44), and moves
     ZERO contour flags versus 2.45 (same flag matrix gate_v49 pins);
  3. bump discipline — CURRENT_STAMP is derived from CURRENT_REVISION (never a literal
     that survives a bump unnoticed), CURRENT_REVISION >= (2, 46).

Zero model calls, zero endpoint.
"""
import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
os.environ.setdefault("PARB_ROOT", os.getcwd())

CHECKS = 0


def ck(cond, what):
    global CHECKS
    CHECKS += 1
    if not cond:
        print("FAIL:", what)
        raise SystemExit(1)


def load_gate(ver):
    """Per-stamp load by PATH (multi-stamp lesson: never reuse a stale handle, never
    let an older workspace shadow the repo copy)."""
    os.environ["PARB_GATE_VERSION"] = ver
    spec = importlib.util.spec_from_file_location(
        "gate_run_%s" % ver.replace(".", "_"), str(HERE / "gate_run.py"))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__file__.startswith(str(HERE)), "stale module path: " + mod.__file__
    return mod


import gate_versioning as GV  # noqa: E402

# ---- 1. resolution order ----------------------------------------------------------
sha_full = "a" * 40
with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "HARNESS_GIT_SHA"), "w").write(sha_full + "\n")
    g0 = load_gate("0.0.2.46")
    ck(g0.harness_git_sha(td) == sha_full, "stamped HARNESS_GIT_SHA is authoritative inside a generated ws")

with tempfile.TemporaryDirectory() as td:
    open(os.path.join(td, "HARNESS_GIT_SHA"), "w").write("not-a-sha\n")
    ck(g0.harness_git_sha(td) == "", "malformed stamp file fails closed (non-hex, no git in tmp -> empty)")

with tempfile.TemporaryDirectory() as td:
    ck(g0.harness_git_sha(td) == "", "no stamp file, no git checkout -> empty (caller warns, publisher labels)")

with tempfile.TemporaryDirectory() as td:
    try:
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        subprocess.run(["git", "init", "-q"], cwd=td, check=True, env=env)
        open(os.path.join(td, "f"), "w").write("x")
        subprocess.run(["git", "add", "f"], cwd=td, check=True, env=env)
        subprocess.run(["git", "commit", "-q", "-m", "t"], cwd=td, check=True, env=env)
        want = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=td,
                              capture_output=True, text=True, env=env).stdout.strip()
        ck(g0.harness_git_sha(td) == want, "fallback `git -C root` reproduces the repo-checkout sha")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("NOTE: git unavailable in this environment — fallback branch not exercised")

# ---- 2/3. tooling-only release, flag matrix, stamp discipline ----------------------
ck(GV.CURRENT_REVISION >= (2, 46), "CURRENT_REVISION advanced to at least (2, 46)")
ck(GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION,
   "CURRENT_STAMP derives from CURRENT_REVISION (pair-244 bump lesson)")
ck((2, 46) not in GV.CONTOUR_FEATURES,
   "2.46 registers no contour feature — a provenance fix must not fake a contour change")
ck((2, 46) not in GV.RESERVED_TOOLING_REVISIONS,
   "2.46 outside the reserved tooling band (contract test enforces the band itself)")
try:
    GV.registered_stamp("0.0.2.46")
    ck(True, "registered_stamp accepts 2.46 (official arms would die at launch otherwise)")
except ValueError as e:
    ck(False, "registered_stamp rejected 2.46: %s" % e)
ck(GV.behavior_tuple("0.0.2.46") == GV.behavior_tuple("0.0.2.45"),
   "reporting axis unchanged: 2.46 resolves to the same newest registered feature as 2.45")
ck(GV.summary("0.0.2.46")["contour_changed_at_this_release"] is False,
   "run record states 2.46 did not change the contour")

_FLAGS = ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "J_RERANK_V2", "A_TABLE_ARITH",
          "B_FIELD_COMPLETE", "B_TABLE_AGGREGATE", "G4_LOTTERY", "J_MEMBERSHIP_V3",
          "C_RULE_GROUND", "LOOP_POLICY_REGROUND", "D_BEST2_BANNED", "D_BEST2_CLAIM",
          "D_BEST2", "H_BEST2", "C_BEST2", "E_MULTIERR", "CODE_FIX", "FORMAT_REPAIR")
g245 = load_gate("0.0.2.45")
g246 = load_gate("0.0.2.46")
missing = [f for f in _FLAGS if not hasattr(g246, f) or not hasattr(g245, f)]
ck(not missing, "every flag name exists at both stamps (%s)" % missing)
moved = [f for f in _FLAGS if getattr(g246, f) != getattr(g245, f)]
ck(not moved, "2.46 moves ZERO contour flags versus 2.45 (%s)" % moved)
ck(g246.D_BEST2_BANNED and g246.D_BEST2 and not g246.D_BEST2_CLAIM,
   "2.46 still runs the adopted 2.43 line with the 2.44 trigger frozen off")
ck(hasattr(g246, "harness_git_sha"), "the resolution helper is a module-level function (testable)")

print("gate_v60 PASS: %d checks | run-record harness identity resolves stamped-file > git > empty; "
      "tooling release 2.46 moves zero contour flags" % CHECKS)
