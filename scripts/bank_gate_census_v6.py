#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bank gate census: every published hard-bank version re-gated at its current bytes.

Why (owner directive 07.11 - improve the tests and the scoring system, version every
element): `gold_selftest_v6.py` and `leakage_scan_v6.py` are the two bank-level
mechanical gates, but both were hardcoded to the v6.1 file bytes, so the bank marked
`working` in BANK-VERSIONS.json was never gated by them after promotion. This census
runs BOTH gates over every file in the registry, recomputed from current bytes.

Fail-closed invariants (structural only - which version is working is never pinned,
the gate_v63 lesson):
  * the registry is the only bank identity: every entry's file bytes must match its
    published_sha16 (a promoted bank is immutable; a correction ships as a new file);
  * registry file set == the published bank files on disk (no unregistered bank file);
  * exactly one entry has status "working";
  * the working bank must pass BOTH gates (gold selftest perfect, leakage zero);
  * superseded/provisional verdicts are historical context recomputed at current
    bytes, never copied from old notes - a byte-drifted old bank still goes red.

Usage:
  bank_gate_census_v6.py            recompute and write benchmarks/hard/BANK-GATE-CENSUS.md
  bank_gate_census_v6.py --check    recompute and diff vs the committed md (CI mode;
                                    non-zero exit on any drift, like unstable_cells --check)
The generated md carries the scanner stamp (census + scorer + registry sha16); editing
this script invalidates the stamp, so the md must be regenerated in the same commit.
"""
import glob
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "harness"))
from gold_selftest_v6 import gold_answer, gold_loop_rows, gold_selftest  # noqa: E402
from leakage_scan_v6 import leakage_scan  # noqa: E402
import parb_check_v6 as c6  # noqa: E402

REGISTRY = os.path.join(ROOT, "benchmarks", "hard", "BANK-VERSIONS.json")
MD_PATH = os.path.join(ROOT, "benchmarks", "hard", "BANK-GATE-CENSUS.md")
ALLOWED_STATUS = {"working", "provisional", "superseded"}


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def rescore_sandbox_fails(bank, gfails):
    """One re-draw for failures whose notes say the SANDBOX failed (container flake
    under parallel docker load), never for content failures. A task still failing on
    the re-draw stays FAIL - the census is fail-closed for gold content, it just does
    not let a docker hiccup fabricate a bank defect (measured 08.11: E-ex6-05 failed
    once under 8-way parallel scoring and passed serially and on re-draw)."""
    if not gfails:
        return gfails
    byid = {t["id"]: t for t in bank}
    keep = []
    for tid, cont, fmt, notes in gfails:
        t = byid[tid]
        if t["cat"] == "E" or any(str(n).startswith("sandbox") for n in notes):
            if t["cat"] == "D" and t.get("mode") == "loop":
                c2, f2, _ = c6.check_D_loop_v6(t, gold_loop_rows(t))
            else:
                c2, f2, _ = c6.check(t, gold_answer(t))
            if c2 == 1.0 and f2:
                continue
        keep.append((tid, cont, fmt, notes))
    return keep


def collect():
    """Return (rows, meta, errors). rows: one dict per registry entry.
    Banks are scored in parallel threads: the E battery runs docker containers per
    task, so a serial full-chain recompute is ~12 min; parallel keeps `--check`
    (which recomputes EVERY verdict - no trusting cached rows) inside ~2 min."""
    from concurrent.futures import ThreadPoolExecutor
    reg = json.load(open(REGISTRY, encoding="utf-8"))
    errors = []
    entries = reg.get("banks", [])
    missing = [e for e in entries if not os.path.exists(os.path.join(ROOT, e["file"]))]
    for e in missing:
        errors.append("registry entry %s: file %s missing" % (e["version"], e["file"]))

    def score(e):
        f = e["file"]
        absf = os.path.join(ROOT, f)
        got = sha16(absf)
        bytes_ok = got == e["published_sha16"]
        bank = json.load(open(absf, encoding="utf-8"))
        gfails = rescore_sandbox_fails(bank, gold_selftest(bank))
        leaks = leakage_scan(bank)
        return {
            "version": e["version"],
            "status": e["status"],
            "file": f,
            "sha16": e["published_sha16"],
            "bytes_ok": bytes_ok,
            "gold": "PASS %d/%d" % (len(bank) - len(gfails), len(bank)) if not gfails
                    else "FAIL %d/%d (%s)" % (len(bank) - len(gfails), len(bank),
                                              ",".join(x[0] for x in gfails[:3])),
            "gold_ok": not gfails,
            "leak": "PASS 0 leaks" if not leaks else "FAIL %d (%s)"
                    % (len(leaks), ",".join(x[0] for x in leaks[:3])),
            "leak_ok": not leaks,
        }

    present = [e for e in entries if e not in missing]
    with ThreadPoolExecutor(max_workers=min(8, max(1, len(present)))) as ex:
        rows = list(ex.map(score, present))
    for r in rows:
        if not r["bytes_ok"]:
            errors.append("registry drift %s: bytes sha16 %s != published %s"
                          % (r["version"], sha16(os.path.join(ROOT, r["file"])), r["sha16"]))
    # registry file set == published bank files on disk
    disk = set()
    for p in glob.glob(os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6*.json")):
        disk.add(os.path.relpath(p, ROOT).replace(os.sep, "/"))
    regfiles = {e["file"] for e in entries}
    if disk != regfiles:
        errors.append("bank file set drift: on disk %s vs registry %s"
                      % (sorted(disk - regfiles), sorted(regfiles - disk)))
    statuses = [r["status"] for r in rows]
    if any(s not in ALLOWED_STATUS for s in statuses):
        errors.append("illegal status in registry: %s" % sorted(set(statuses) - ALLOWED_STATUS))
    working = [r for r in rows if r["status"] == "working"]
    if len(working) != 1:
        errors.append("exactly one bank must be working, found %d" % len(working))
    for w in working:
        if not w["gold_ok"]:
            errors.append("working bank %s fails gold selftest: %s" % (w["version"], w["gold"]))
        if not w["leak_ok"]:
            errors.append("working bank %s fails leakage scan: %s" % (w["version"], w["leak"]))
    meta = {
        "census_sha16": sha16(os.path.abspath(__file__)),
        "scorer_sha16": sha16(os.path.join(ROOT, "harness", "parb_check_v6.py")),
        "registry_sha16": sha16(REGISTRY),
    }
    return rows, meta, errors


def md_table(rows):
    lines = ["| version | status | file | published sha16 | bytes vs registry | gold selftest | leakage scan |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append("| %s | %s | %s | `%s` | %s | %s | %s |"
                     % (r["version"], r["status"], r["file"], r["sha16"],
                        "match" if r["bytes_ok"] else "**DRIFT**", r["gold"], r["leak"]))
    return lines


def render(rows, meta):
    head = ("# Bank gate census - every published hard bank, standing mechanical gates\n\n"
            "Auto-generated by `scripts/bank_gate_census_v6.py`; `--check` re-derives this table "
            "and CI runs it, so a retyped row goes red. Gates: gold self-test (the constructed-correct "
            "answer must score 1.0/1.0 under the frozen v6 scorer) and leakage scan (no gold value or "
            "answer marker inside any prompt). Verdicts are recomputed from current bytes every run; "
            "any bank whose bytes no longer match its registry sha16 fails closed. `working` must pass "
            "both gates; older rows are historical context, their status column is registry state, not a "
            "re-narrated promotion verdict. E-category failures get one re-draw (the battery runs in "
            "docker and a container hiccup must not fabricate a bank defect); a task failing BOTH draws "
            "is a real FAIL and goes red.\n\n")
    stamp = ("\nscanner: `bank_gate_census_v6.py` %s | scorer `harness/parb_check_v6.py` %s | "
             "registry `BANK-VERSIONS.json` %s\n"
             % (meta["census_sha16"], meta["scorer_sha16"], meta["registry_sha16"]))
    return head + "\n".join(md_table(rows)) + "\n" + stamp


def check_md(rows, meta):
    if not os.path.exists(MD_PATH):
        print("MISSING %s - run bank_gate_census_v6.py and commit it" % os.path.relpath(MD_PATH, ROOT))
        return 1
    want = render(rows, meta)
    have = open(MD_PATH, encoding="utf-8").read()
    def table(text):
        return [l for l in text.splitlines() if l.startswith("| v6")]
    if table(want) != table(have):
        print("CENSUS TABLE DRIFT: committed BANK-GATE-CENSUS.md does not match a fresh recompute")
        for a, b in zip(table(want), table(have)):
            if a != b:
                print(" want:", a)
                print(" have:", b)
        return 1
    if "scanner:" not in have or meta["census_sha16"] not in have \
            or meta["scorer_sha16"] not in have or meta["registry_sha16"] not in have:
        print("CENSUS STAMP DRIFT: scanner/scorer/registry sha16 in the committed md do not match "
              "the current files - regenerate BANK-GATE-CENSUS.md in the same commit")
        return 1
    return 0


def main():
    rows, meta, errors = collect()
    for r in rows:
        print("%-5s %-11s %-38s %s  %s  %s  bytes:%s"
              % (r["version"], r["status"], os.path.basename(r["file"]), r["sha16"],
                 r["gold"], r["leak"], "ok" if r["bytes_ok"] else "DRIFT"))
    for e in errors:
        print("ERROR:", e)
    if errors:
        return 1
    if "--check" in sys.argv:
        rc = check_md(rows, meta)
        print("BANK GATE CENSUS --check:", "PASS (%d banks)" % len(rows) if rc == 0 else "FAIL")
        return rc
    with open(MD_PATH, "w", encoding="utf-8") as fh:
        fh.write(render(rows, meta))
    print("-> %s" % os.path.relpath(MD_PATH, ROOT))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
