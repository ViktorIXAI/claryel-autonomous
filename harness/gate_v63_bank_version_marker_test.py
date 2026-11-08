#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Release 0.0.2.49 contract: the run record names the bank VERSION, not just bytes.

Cadence-246-era run records wrote `stack.bank_version: ""` — the label was fed only
by `PARB_BANK_VERSION`, which no runner ever set — while the published version chain
(v6.1 -> v6.2 -> v6.3 -> v6.4) made the label as load-bearing as the sha16. The fix
must be proven, not asserted, and must not disturb any contour byte:

  1. registry identity — `BANK-VERSIONS.json` maps each published bank file to its
     version + sha16, `check_registry` fails CLOSED if a published byte moved
     (the immutability rule enforced at build time), and the v6.1 file-name trap
     is recorded exactly (bank-hard-v6.json carries the v6.1 bytes);
  2. resolution — `run_record_bank_version` prefers the workspace marker but only
     after validating it against the LIVE bank.json bytes (marker drift fails
     closed even with a hostile env set), then content match from a repo
     checkout, then explicit env, then empty with a source reason (never a guess);
  3. wiring — `gate_run`'s stack block calls the resolver (no direct env read
     left), and the builder imports the module, fails closed on an unregistered
     bank, stamps the marker, and pins `bank-version.json`;
  4. tooling-only — 2.49 registers no contour feature, is outside the reserved
     band, resolves to the same behavior axis as 2.48, and moves ZERO contour
     flags versus 2.48; CURRENT_REVISION >= (2,49), CURRENT_STAMP derived.

Zero model calls, zero endpoint.
"""
import importlib.util
import json
import os
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
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
import gate_bank_versions as GBV  # noqa: E402

# ---- 1. registry identity + immutability guard -------------------------------------
reg = GBV.check_registry(str(REPO))
# (stale-pin repair, 2026-11-07: the old `len(reg) == 4` went red the day v6.5/v6.6
# joined the registry — exactly the CURRENT_REVISION exact-pin lesson. The invariant
# is structural: the registry covers EXACTLY the published bank files, and EXACTLY
# one bank carries `working` at any time.)
import glob as _glob
published = sorted(os.path.basename(p) for p in
                   _glob.glob(str(REPO / "benchmarks" / "hard" / "bank-hard-v6*.json")))
ck(sorted(e["file"].rsplit("/", 1)[-1] for e in reg) == published,
   "registry must cover exactly the published bank files: reg=%r files=%r" % (len(reg), published))
ck(sum(1 for e in reg if e.get("status") == "working") == 1,
   "exactly one bank is `working` at any time: %r"
   % [e["version"] for e in reg if e.get("status") == "working"])
byver = {e["version"]: e for e in reg}
ck(byver["v6.1"]["file"] == "benchmarks/hard/bank-hard-v6.json"
   and byver["v6.1"]["published_sha16"] == "9ec86dfca4a6f85f",
   "identity trap recorded: bank-hard-v6.json carries the v6.1 bytes forever")
ck(byver["v6.2"]["published_sha16"] == "3c866ea7daae611c", "v6.2 published bytes pinned")
ck(byver["v6.3"]["status"] == "provisional", "v6.3 stays PROVISIONAL in the registry")
ck(byver["v6.4"]["status"] == "superseded", "v6.4 superseded by the v6.6 promotion")
ck(byver["v6.5"]["status"] == "provisional", "v6.5 stays provisional (frozen verdict)")
# (stale-pin repair, 2026-11-08: this line pinned v6.6 as `working` — a CURRENT-state
# claim — and went red the day the v6.8 promotion moved the slot. Which version holds
# `working` is mutable by design; the structural assertion above (exactly one working)
# is the invariant. Statuses of PAST versions are frozen history and stay pinned.)
ck(byver["v6.6"]["status"] == "superseded", "v6.6 demoted at a later promotion (frozen history)")
ck(byver["v6.7"]["status"] == "provisional", "v6.7 stays provisional (frozen probe rule)")
try:
    GBV.load_registry("/nonexistent-dir-xyz")
    ck(False, "missing registry must raise BankIdentityError")
except GBV.BankIdentityError:
    ck(True, "missing registry raises BankIdentityError (fail closed)")
# drift: same registry, but one bank byte on disk differs -> check_registry refuses
with tempfile.TemporaryDirectory() as td:
    hard = os.path.join(td, "benchmarks", "hard")
    os.makedirs(hard)
    doc = json.load(open(GBV.registry_path(str(REPO)), encoding="utf-8"))
    json.dump(doc, open(os.path.join(hard, "BANK-VERSIONS.json"), "w", encoding="utf-8"))
    for e in doc["banks"]:
        open(os.path.join(td, e["file"]), "w", encoding="utf-8").write("bank contents")
    try:
        GBV.check_registry(td)
        ck(False, "check_registry accepted registered sha16 vs different bytes")
    except GBV.BankIdentityError as ex:
        ck("published bytes moved" in str(ex),
           "byte drift message names the immutability rule")
ck(GBV.resolve_for_file(os.path.join(str(REPO), "benchmarks/hard/bank-hard-v6.4.json"),
                        str(REPO))["version"] == "v6.4",
   "resolve_for_file matches v6.4 by name AND bytes")
with tempfile.TemporaryDirectory() as td:
    p = os.path.join(td, "bank-hard-v6.4.json")
    open(p, "w").write("[]")
    ck(GBV.resolve_for_file(p, str(REPO)) is None,
       "same-name file with different bytes resolves to None (builder then fails closed)")

# ---- 2. resolution order: marker (bytes-validated) > content > env > none ----------
entry64 = byver["v6.4"]
with tempfile.TemporaryDirectory() as td:
    shutil_bank = json.load(open(os.path.join(str(REPO), entry64["file"]), encoding="utf-8"))
    json.dump(shutil_bank, open(os.path.join(td, "bank.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    ws_sha = GBV.file_sha16(os.path.join(td, "bank.json"))
    GBV.write_marker(td, entry64, ws_sha)
    ck(GBV.run_record_bank_version(td, ws_sha) == ("v6.4", "marker"),
       "valid marker wins: ws copy hash equals live bank.json hash")
    ck(GBV.run_record_bank_version(td, ws_sha, repo_root=str(REPO)) == ("v6.4", "marker"),
       "marker beats content match (no ambiguity when both resolve)")
    ck(GBV.run_record_bank_version(td, "0" * 16, repo_root=str(REPO))[1] == "marker-drift"
       and GBV.run_record_bank_version(td, "0" * 16, repo_root=str(REPO))[0] == "",
       "marker drift fails CLOSED: bank.json moved under the marker, no label even "
       "though content match would answer v6.4")
    os.environ["PARB_BANK_VERSION"] = "v9.9-hostile"
    ck(GBV.run_record_bank_version(td, "0" * 16)[0] == "",
       "marker drift also beats a hostile PARB_BANK_VERSION env")
    os.environ.pop("PARB_BANK_VERSION")
    os.remove(os.path.join(td, "bank-version.json"))
    ck(GBV.run_record_bank_version(td, ws_sha, repo_root=str(REPO)) == ("v6.4", "content"),
       "ws bank.json (re-serialized) content-matches the published v6.4 file")
    json.dump([{"id": "other"}], open(os.path.join(td, "bank.json"), "w", encoding="utf-8"))
    os.environ["PARB_BANK_VERSION"] = "v7.7-manual"
    ck(GBV.run_record_bank_version(td, GBV.file_sha16(os.path.join(td, "bank.json")),
                                   repo_root=str(REPO)) == ("v7.7-manual", "env"),
       "unmatched bank bytes fall to explicit env (manual/ad-hoc runs)")
    os.environ.pop("PARB_BANK_VERSION")
    res = GBV.run_record_bank_version(td, "abc", repo_root=str(REPO))
    ck(res == ("", "none"), "no marker, no match, no env -> empty label with source 'none'")
    open(os.path.join(td, "bank-version.json"), "w").write("{not json")
    ck(GBV.run_record_bank_version(td, "abc", repo_root=str(REPO)) == ("", "none"),
       "malformed marker behaves as absent (and never fabricates a label)")
    open(os.path.join(td, "bank-version.json"), "w").write('{"version": "v6.4"}')
    ck(GBV.run_record_bank_version(td, "abc", repo_root=str(REPO)) == ("", "none"),
       "marker missing the bank_version key (wrong schema) is not trusted")

# ---- 3. wiring: call site + builder, not just the function -------------------------
src = open(HERE / "gate_run.py", encoding="utf-8").read()
ck('"bank_version": _bver' in src and "GBV.run_record_bank_version(ROOT" in src,
   "gate_run stack block calls the resolver (module-level, testable)")
ck('os.environ.get("PARB_BANK_VERSION"' not in src,
   "no direct env read left in gate_run: env fallback lives ONLY in the resolver")
bsrc = open(str(REPO / "scripts" / "build_hard_v6_ws.py"), encoding="utf-8").read()
ck("import gate_bank_versions as GBV" in bsrc, "builder imports the identity module")
ck("GBV.check_registry(ROOT)" in bsrc and "BANK NOT IN REGISTRY" in bsrc,
   "builder checks the registry and fails closed on an unregistered bank")
ck("GBV.write_marker(OUT" in bsrc, "builder stamps the marker into every generated ws")
ck('"bank-version.json"' in bsrc and '"gate_bank_versions.py"' in bsrc,
   "marker and module are hash-pinned in WS_PINNED")

# ---- 4. tooling-only release: matrix, axes, stamp discipline -----------------------
ck(GV.CURRENT_REVISION >= (2, 49), "CURRENT_REVISION advanced to at least (2, 49)")
ck(GV.CURRENT_STAMP == "0.0.%d.%d" % GV.CURRENT_REVISION,
   "CURRENT_STAMP derives from CURRENT_REVISION (pair-244 bump lesson)")
ck((2, 49) not in GV.CONTOUR_FEATURES,
   "2.49 registers no contour feature — an identity fix must not fake a contour change")
ck((2, 49) not in GV.RESERVED_TOOLING_REVISIONS,
   "2.49 outside the reserved tooling band")
try:
    GV.registered_stamp("0.0.2.49")
    ck(True, "registered_stamp accepts 0.0.2.49 (arms would die at launch otherwise)")
except ValueError as e:
    ck(False, "registered_stamp rejected 2.49: %s" % e)
ck(GV.behavior_tuple("0.0.2.49") == GV.behavior_tuple("0.0.2.48") == (2, 48),
   "reporting axis unchanged: 2.49 resolves to the newest registered feature 2.48")
ck(GV.summary("0.0.2.49")["contour_changed_at_this_release"] is False,
   "run record states 2.49 did not change the contour")

_FLAGS = ("CONTRACT_GUARANTEE", "SELFCONSIST", "J_RERANK", "J_RERANK_V2", "A_TABLE_ARITH",
          "B_FIELD_COMPLETE", "B_TABLE_AGGREGATE", "G4_LOTTERY", "J_MEMBERSHIP_V3",
          "C_RULE_GROUND", "LOOP_POLICY_REGROUND", "D_BEST2_BANNED", "D_BEST2_CLAIM",
          "D_BEST2", "H_BEST2", "C_BEST2", "C_BEST2_SET", "K_FIELDS_ENUM",
          "E_MULTIERR", "CODE_FIX", "FORMAT_REPAIR")
g248 = load_gate("0.0.2.48")
g249 = load_gate("0.0.2.49")
missing = [f for f in _FLAGS if not hasattr(g249, f) or not hasattr(g248, f)]
ck(not missing, "every flag name exists at both stamps (%s)" % missing)
moved = [f for f in _FLAGS if getattr(g249, f) != getattr(g248, f)]
ck(not moved, "2.49 moves ZERO contour flags versus 2.48 (%s)" % moved)
ck(g249.K_FIELDS_ENUM and g249.C_BEST2_SET and g249.D_BEST2_BANNED,
   "2.49 still runs the adopted 2.48 line (2.43/2.47/2.48 features on)")
ck(not g249.CONTRACT_GUARANTEE and not g249.SELFCONSIST and not g249.D_BEST2_CLAIM,
   "frozen negatives stay off at 2.49")
ck(getattr(g249, "GBV", None) is not None
   and hasattr(g249.GBV, "run_record_bank_version"),
   "the stamped gate_run carries the resolver as a module attribute (call site live)")

# end-to-end shape of the exact stack field an arm writes
with tempfile.TemporaryDirectory() as td:
    bank = json.load(open(os.path.join(str(REPO), entry64["file"]), encoding="utf-8"))
    json.dump(bank, open(os.path.join(td, "bank.json"), "w", encoding="utf-8"),
              ensure_ascii=False)
    ws_sha = GBV.file_sha16(os.path.join(td, "bank.json"))
    GBV.write_marker(td, entry64, ws_sha)
    ver, src_how = g249.GBV.run_record_bank_version(td, ws_sha)
    ck(ver == "v6.4" and src_how == "marker",
       "a workspace built on bank v6.4 yields stack.bank_version == 'v6.4'")

print("gate_v63 PASS: %d checks | bank version resolves marker(validated) > content > env > "
      "empty; registry immutability enforced at check time; tooling release 2.49 moves zero "
      "contour flags" % CHECKS)
