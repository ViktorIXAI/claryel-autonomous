#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate versions/MEASUREMENT-STACK.md (+ .json) — the full stack of every run.

Why: a number in this repo used to be interpretable only from prose. Bank identity
lived in a README sentence, the scorer had no version at all, and the seed protocol
was folklore. This script writes the stack down mechanically: bank version + sha16,
scorer contract version + pinned module hashes, seed-protocol version, contour stamp
vs contour behavior, harness commit, endpoint model, energy window — per artifact
directory, read from the published run records and ledgers.

Rules it publishes (and enforces for future runs):
* every published table must name the bank sha16 and the scorer contract version;
* from release 0.0.2.45 every run record carries `stack` — a results directory
  without it is refused by the publisher;
* artifacts produced before that release are attributed by construction: the pinned
  contract bytes are the bytes that produced them, and that is stated, not implied.
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import gate_scorer_contract as SC  # noqa: E402
from gate_versioning import (CONTOUR_FEATURES, CURRENT_REVISION, CURRENT_STAMP,  # noqa: E402
                             RESERVED_TOOLING_REVISIONS, behavior_tuple, summary)

RES = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
FROZEN_NOTE = {
    (2, 30): "contract guarantee (shape re-ask/salvage) — MEASURED NEGATIVE",
    (2, 31): "self-consistency vote — MEASURED NEGATIVE",
    (2, 32): "J ranking repair v1 — on target, under the noise floor",
    (2, 33): "A threshold-table arithmetic — zero live fires",
    (2, 34): "B field completeness — zero live fires",
    (2, 36): "group-4 lottery selection — MEASURED NEGATIVE",
    (2, 38): "A threshold-table re-land — UNMEASURED",
    (2, 41): "C rule-grounded membership — UNMEASURED",
    (2, 42): "D-loop policy re-ground — MEASURED NEGATIVE",
    (2, 44): "D-loop best-of-2 on false_completion_claim — UNMEASURED",
}


def sha16(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def git_sha():
    try:
        return subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"],
                              capture_output=True, text=True, timeout=8).stdout.strip()
    except Exception:
        return ""


def contour_block():
    feats = list(CONTOUR_FEATURES)
    frozen = [f for f in feats if f in FROZEN_NOTE]
    adopted = [f for f in feats if f not in frozen]
    return {
        "current_revision": "%d.%d" % CURRENT_REVISION,
        "current_stamp": CURRENT_STAMP,
        "behavior_at_current": "%d.%d" % behavior_tuple(CURRENT_STAMP),
        "contour_changed_at_current_release": summary(CURRENT_STAMP)["contour_changed_at_this_release"],
        "registered_features": ["%d.%d" % f for f in feats],
        "adopted_line_features": ["%d.%d" % f for f in adopted],
        "frozen_to_own_stamp": {"%d.%d" % f: FROZEN_NOTE[f] for f in frozen},
        "reserved_tooling_band": ["%d.%d" % f for f in RESERVED_TOOLING_REVISIONS],
        "note": ("the ADOPTED feature matrix of 0.0.2.45 equals 0.0.2.43; the behavior axis "
                 "reports the newest REGISTERED stamp (2.44), whose own flag is frozen OFF — "
                 "name BOTH axes in every table"),
    }


def element_block():
    banks = []
    for name, label in (("bank-hard-v6.json", "v6.1 (published dev bank)"),
                        ("bank-hard-v6.2.json", "v6.2 (defect corrections)"),
                        ("bank-hard-v6.3.json", "v6.3 (B-ex6-04 year fix; PROVISIONAL, superseded)"),
                        ("bank-hard-v6.4.json", "v6.4 (WORKING hard bank: + value-form hint)")):
        p = os.path.join(ROOT, "benchmarks/hard", name)
        if os.path.exists(p):
            banks.append({"file": name, "label": label, "sha16": sha16(p)})
    for wsdir, label in (("parb-v62-probe", "bank v6.2 probe-workspace copy"),
                         ("parb-v63-probe", "bank v6.3 probe-workspace copy"),
                         ("parb-v64-probe", "bank v6.4 probe-workspace copy (WORKING)")):
        p = os.path.expanduser(os.path.join("~", wsdir, "bank.json"))
        if os.path.exists(p):
            banks.append({"file": "%s/bank.json" % wsdir, "label": label, "sha16": sha16(p)})
    ws_bank = os.path.join(os.environ.get("PARB_WS", os.path.expanduser("~/parb-v61-contour")), "bank.json")
    if os.path.exists(ws_bank):
        banks.append({"file": "parb-v61-contour/bank.json",
                      "label": "generated run-workspace copy (v6.1 content)",
                      "sha16": sha16(ws_bank)})
    contracts = {}
    for cid in SC.CONTRACT_HISTORY:
        contracts[cid] = {"pins": SC.CONTRACT_PINS[cid],
                          "identity": SC.contract_identity(cid),
                          "status": SC.CONTRACT_STATUS[cid]}
    return {
        "banks": banks,
        "scorer_contracts": contracts,
        "strict_rule": SC.STRICT_RULE,
        "seed_protocol": {"id": SC.SEED_PROTOCOL, "definition": SC.SEED_PROTOCOL_TEXT},
        "harness_commit": git_sha(),
    }


def run_dirs():
    out = []
    for d in sorted(os.listdir(RES)):
        full = os.path.join(RES, d)
        if not os.path.isdir(full) or d in ("rescore-v62",):
            continue
        if not (glob.glob(os.path.join(full, "results-*.jsonl"))
                or glob.glob(os.path.join(full, "answers-*.jsonl"))):
            continue
        out.append((d, full))
    return out


def dir_block(name, full):
    recs = {}
    for p in sorted(glob.glob(os.path.join(full, "run-record-*.json"))):
        try:
            r = json.load(open(p, encoding="utf-8"))
        except (ValueError, OSError):
            continue
        rid = os.path.basename(p)[len("run-record/"):-len(".json")]
        recs[rid] = {"contour_stamp": r.get("contour_version"),
                     "contour_behavior": r.get("contour_behavior"),
                     "model": r.get("model"), "box": r.get("box"),
                     "plan_tasks": r.get("plan_tasks"),
                     "harness_git_sha": r.get("git_sha") or None,
                     "stack": r.get("stack")}
    ledgers = sorted(glob.glob(os.path.join(full, "ledger-*.jsonl")))
    rows = 0
    stamp = behavior = None
    for p in ledgers:
        for ln in open(p, encoding="utf-8"):
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            rows += 1
            stamp = stamp or r.get("contour_version")
            behavior = behavior or r.get("contour_behavior")
    epochs = {}
    for p in glob.glob(os.path.join(full, "*-start.epoch")):
        key = os.path.basename(p)[:-len("-start.epoch")]
        try:
            s = float(open(p).read().strip())
            e = os.path.join(full, key + "-end.epoch")
            epochs[key] = {"seconds": round(float(open(e).read().strip()) - s, 1)
                           if os.path.exists(e) else None}
        except (OSError, ValueError):
            pass
    stack_in_records = any(v.get("stack") for v in recs.values())
    return {
        "dir": "benchmarks/hard/v6-results/" + name,
        "arms": sorted(recs) or [os.path.basename(p)[len("ledger/"):-len(".jsonl")]
                                 for p in ledgers],
        "ledger_rows": rows,
        "contour_stamp": stamp, "contour_behavior": behavior,
        "run_records": recs,
        "run_record_has_stack": stack_in_records,
        "energy_windows_seconds": epochs,
        "bank_attribution": ("recorded in the run record" if stack_in_records
                             else "bank-hard-v6.json 9ec86dfca4a6f85f (ws copy f4553aab304f60d7): "
                                  "every published arm up to 0.0.2.44 scored that bank"),
        "scorer_contract_attribution": ("recorded per row" if stack_in_records
                                        else "v6.1 (the pinned bytes in gate_scorer_contract)"),
    }


def main():
    el = element_block()
    ct = contour_block()
    dirs = [dir_block(n, f) for n, f in run_dirs()]
    os.makedirs(os.path.join(ROOT, "versions"), exist_ok=True)
    json.dump({"elements": el, "contour": ct, "runs": dirs},
              open(os.path.join(ROOT, "versions", "measurement-stack.json"), "w",
                   encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# Measurement stack: what every number in this repo was produced under",
          "",
          "Regenerate: `python3 scripts/measurement_stack.py`. Every table in this repo must",
          "name the bank sha16 and the scorer contract version next to its numbers; this file is",
          "where those identities are defined, so a quoted number can be traced to bytes.",
          "",
          "## 1. The versioned elements",
          "",
          "| element | version | identity (sha16) | pinned by |",
          "|---|---|---|---|",
          "| dev bank (hard) | v6.1 | %s | `benchmarks/hard/MANIFEST.v6.sha256`, `bank-defect-v62-changelog.md` |"
          % next((b["sha16"] for b in el["banks"] if b["file"] == "bank-hard-v6.json"), "-"),
          "| dev bank (hard) | v6.2 | %s | `scripts/verify_bank_v62.py` (fails if v6.1 moves) |"
          % next((b["sha16"] for b in el["banks"] if b["file"] == "bank-hard-v6.2.json"), "-"),
          "| dev bank (hard) | v6.3 | %s | `scripts/verify_bank_v63.py` (one field vs v6.2; PROVISIONAL) |"
          % next((b["sha16"] for b in el["banks"] if b["file"] == "bank-hard-v6.3.json"), "-"),
          "| dev bank (hard) | **v6.4** | %s | `scripts/verify_bank_v64.py` (one field vs v6.3; WORKING hard bank) |"
          % next((b["sha16"] for b in el["banks"] if b["file"] == "bank-hard-v6.4.json"), "-"),
          ]
    for b in el["banks"]:
        if "bank.json" in b["file"]:
            md.append("| run workspace bank copy | %s | %s | run record `stack.bank_sha16` |"
                      % (b["label"], b["sha16"]))
    for cid in SC.CONTRACT_HISTORY:
        c = el["scorer_contracts"][cid]
        mods = ", ".join("%s %s" % (m, h) for m, h in sorted(c["pins"].items()))
        md.append("| scorer contract | **%s** | %s; modules: %s | `harness/gate_scorer_contract.py` + `MANIFEST.v6.sha256` |"
                  % (cid, c["identity"]["contract_sha16"], mods))
    md += ["| strict rule | (part of every contract) | `%s` | `gate_scorer_contract.STRICT_RULE` |"
           % el["strict_rule"],
           "| seed protocol | %s | per-(task,rep) gseed + per-task plan seed | `scripts/plan_reps.py`, `build_hard_v6_ws.py` |"
           % el["seed_protocol"]["id"],
           "| typed failure codes | registry in contract v6.2 | content / protocol / integrity / marker / infra | `gate_scorer_contract.CODE_CLASS`, gate_v59 tests |",
           "| two published axes | contract v6.2 | answer axis + protocol axis, additive to `strict` | `gate_v59_scorer_contract_v62_test.py` |",
           "| harness | commit %s | contour stamp %s (behavior %s) | git + `gate_versioning.py` |"
           % ((el["harness_commit"] or "-")[:12], ct["current_revision"], ct["behavior_at_current"]),
           "",
           "Scorer contract v6.2 delegates to the v6.1 bytes, so it changes no score; the equality",
           "is asserted cell by cell on published answers (`gate_v59_scorer_contract_v62_test.py`),",
           "and `verify_contract()` fails closed if a frozen scoring byte moves without a new version.",
           "",
           "## 2. Contour axes",
           "",
           "- stamped revision now: **%s** (`%s`); contour behavior reported: **%s**;"
           % (ct["current_revision"], ct["current_stamp"], ct["behavior_at_current"]),
           "- did this release change the contour? **%s** (a tooling release registers no feature)"
           % ct["contour_changed_at_current_release"],
           "- adopted line features: %s" % ", ".join(ct["adopted_line_features"]),
           "- frozen to their own stamp (never inherited): %s"
           % ", ".join("%s (%s)" % (k, v) for k, v in ct["frozen_to_own_stamp"].items()),
           "- reserved tooling band (behavior pinned forever): %s"
           % ", ".join(ct["reserved_tooling_band"]),
           "",
           ct["note"],
           "",
           "## 3. Per-artifact stack",
           "",
           "`stack` = the block written into `run-record-*.json` from release 0.0.2.45 onward.",
           "Earlier directories are attributed by construction: their rows carry",
           "`contour_version`/`contour_behavior`, and the only bank/contract bytes that could have",
           "produced them are the pinned ones named below.",
           "",
           "| directory | arms | rows | contour stamp / behavior | bank | scorer | stack in record |",
           "|---|---|---|---|---|---|---|"]
    for d in dirs:
        md.append("| `%s` | %d | %d | %s / %s | %s | %s | %s |"
                  % (os.path.basename(d["dir"]), len(d["arms"]), d["ledger_rows"],
                     d["contour_stamp"] or "-", d["contour_behavior"] or "-",
                     "recorded" if d["run_record_has_stack"] else "9ec86dfca4a6f85f",
                     "recorded" if d["run_record_has_stack"] else "v6.1",
                     "yes" if d["run_record_has_stack"] else "no (pre-0.0.2.45)"))
    md += ["",
           "## 4. Rules for new runs",
           "",
           "1. `gate_run.py` stamps `scorer_contract`, `contract_sha16`, typed `codes` and the two",
           "   axes into every results row and `scorer_contract`+`codes` into every ledger row.",
           "2. `run-record-<rid>.json` carries `stack`: bank sha16 + task count, scorer contract +",
           "   contract hash, strict rule, seed protocol, contour stamp + behavior, harness sha.",
           "3. Before the endpoint is reserved the runner calls `verify_contract()` and dies with",
           "   `SCORER CONTRACT DRIFT` if the workspace's scoring bytes are not the pinned ones.",
           "4. A results directory published without a `stack` block is refused by the publisher;",
           "   a table that cannot name its bank sha16 and contract version is invalid by definition.",
           "5. A correction to any scoring byte is a NEW contract version plus a re-score of every",
           "   published arm; published numbers are never re-labelled in place.",
           ""]
    with open(os.path.join(ROOT, "versions", "MEASUREMENT-STACK.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")
    print("wrote versions/MEASUREMENT-STACK.md (%d run dirs, banks %s, contracts %s)"
          % (len(dirs), [b["sha16"][:8] for b in el["banks"]], list(el["scorer_contracts"])))


if __name__ == "__main__":
    main()
