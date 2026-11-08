#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Adopted-line live-rate (measurability) map for ONE contour stamp.

Why this exists: a candidate stamp may only be launched if the ADOPTED line
strict-FAILS its target cell on the current seeds (the "live target" rule).
That claim needs a table regenerated from published arms, never a map left over
from an older stamp — pair-251 burned an endpoint window on a zero-live-target
pair, and the 2.53-era map went stale the day 2.55 was adopted. This is the
parameterized generator the hand-written maps should never have replaced.

Guards (all fail closed, because a wrong map silently funds a dead pair):
  * every ledger row of every arm must carry --stamp in `contour_version`
  * every arm must hold exactly the bank's task set, one row per task, no dups
  * every arm must agree on stack.bank_version / bank_sha16 / scorer_contract
  * the --bank file's bytes must match its BANK-VERSIONS.json published sha16
  * answers join the ledger by (task, rep); >5% blank answers = refuse
    (a blank answer re-scored as "" fabricates a parse-collapse diagnosis)

Usage:
  python3 scripts/unstable_cells_v62.py \
      --bank benchmarks/hard/bank-hard-v6.6.json --stamp 0.0.2.55 \
      --out benchmarks/hard/v6-results/UNSTABLE-CELLS-V66-255.md \
      --csv benchmarks/hard/v6-results/UNSTABLE-CELLS-V66-255.csv \
      benchmarks/hard/v6-results/pair-252/x55r48 ... 6 arms ...
An arm is "<dir>/<rid>"; the dir must hold ledger-<rid>.jsonl,
results-<rid>.jsonl and run-record-<rid>.json.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V6 = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
BANK_REGISTRY = os.path.join(ROOT, "benchmarks", "hard", "BANK-VERSIONS.json")

# Notes whose parameter varies per draw: group by stem, like the trigger rules do.
PARAMETRIZED = {"banned_attempted"}
# Notes that describe the harness, not the answer: never a failure family.
INFRA_NOTES = {"sandbox"}
FIRED_PREFIXES = ("contour:", "fix:", "gate:blocked")


def sha16(path: str) -> str:
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def strict(c, f) -> bool:
    return c == 1.0 and bool(f)


def fired(events) -> bool:
    return any(str(e).startswith(FIRED_PREFIXES) for e in (events or []))


def note_family(note: str) -> str:
    stem = str(note).split(":")[0]
    return stem if stem in PARAMETRIZED else str(note)


def main() -> int:
    ap = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    ap.add_argument("arms", nargs="+", help="<dir>/<rid> of a published arm")
    ap.add_argument("--bank", required=True, help="published bank json (list form)")
    ap.add_argument("--stamp", required=True, help="expected contour_version, e.g. 0.0.2.55")
    ap.add_argument("--out", help="write markdown here instead of stdout")
    ap.add_argument("--csv", help="also write a machine-readable cell matrix")
    ap.add_argument("--seeds-note", default="", help="one line about seed freshness")
    ap.add_argument("--check", action="store_true",
                    help="compare the regenerated cell table against --out and fail on any "
                         "difference (CI reproducibility guard); the dated header line and the "
                         "prose above the provenance table are not compared")
    args = ap.parse_args()

    bank_path = args.bank if os.path.isabs(args.bank) else os.path.join(ROOT, args.bank)
    bank = {t["id"]: t for t in json.load(open(bank_path, encoding="utf-8"))}
    loop = {k for k, t in bank.items() if t.get("mode") == "loop"}
    pub_sha = sha16(bank_path)
    reg = json.load(open(BANK_REGISTRY, encoding="utf-8"))
    entry = next((b for b in reg["banks"] if sha16(os.path.join(ROOT, b["file"])) == pub_sha), None)
    if entry is None:
        raise SystemExit("bank %s (sha16 %s) is not a published entry in BANK-VERSIONS.json — "
                         "a map over unpublished bank bytes is not comparable to anything"
                         % (bank_path, pub_sha))
    if entry["published_sha16"] != pub_sha:
        raise SystemExit("bank %s bytes (sha16 %s) differ from the registry's published_sha16 %s — "
                         "the file was edited in place, which is the identity trap this rule exists "
                         "to prevent" % (bank_path, pub_sha, entry["published_sha16"]))

    per = collections.defaultdict(dict)      # task -> rid -> bool
    notes = {}                              # (task, rid) -> list[str]
    events = {}                             # (task, rid) -> list[str]
    stacks, provenance = {}, []
    for arm in args.arms:
        d, rid = os.path.split(arm)
        if not d:
            raise SystemExit("arm must be <dir>/<rid>, got %r" % arm)
        lp, rp, jp = (os.path.join(d, "ledger-%s.jsonl" % rid),
                      os.path.join(d, "results-%s.jsonl" % rid),
                      os.path.join(d, "run-record-%s.json" % rid))
        for p in (lp, rp, jp):
            if not os.path.exists(p):
                raise SystemExit("missing %s for arm %s" % (p, arm))
        rr = json.load(open(jp, encoding="utf-8"))
        st = rr.get("stack") or {}
        if st.get("contour_stamp") and st["contour_stamp"] != args.stamp.removeprefix("0.0."):
            raise SystemExit("arm %s run record stamps contour %s, expected %s"
                             % (arm, st["contour_stamp"], args.stamp))
        for key in ("bank_version", "bank_sha16", "scorer_contract", "contract_sha16",
                    "seed_protocol", "harness_git_sha"):
            stacks.setdefault(key, set()).add(str(st.get(key)))
        provenance.append((rid, rr.get("box"), rr.get("model"), st.get("bank_version"),
                           st.get("bank_sha16"), st.get("scorer_contract"),
                           (st.get("harness_git_sha") or "")[:7], st.get("seed_protocol")))

        raw, seen = {}, set()
        for line in open(rp, encoding="utf-8"):
            q = json.loads(line)
            k = (q["task"], str(q.get("rep")))
            if k in seen:
                raise SystemExit("arm %s has duplicate results row %s — dedup before mapping"
                                 % (arm, k))
            seen.add(k)
            raw[k] = q.get("answer") or q.get("text") or ""
            notes[(q["task"], rid)] = [str(n) for n in (q.get("notes") or [])]
        rows = [json.loads(l) for l in open(lp, encoding="utf-8")]
        if {r.get("contour_version") for r in rows} != {args.stamp}:
            raise SystemExit("arm %s ledger stamps %s, expected %s: an unregistered or malformed "
                             "stamp means the arm measured a DIFFERENT contour"
                             % (arm, sorted({r.get('contour_version') for r in rows}), args.stamp))
        if len(rows) != len(bank):
            raise SystemExit("arm %s has %d ledger rows for a %d-task bank: a partial arm is a "
                             "probe, not an arm — printing its pass rate would be a fabrication"
                             % (arm, len(rows), len(bank)))
        if {r["task"] for r in rows} != set(bank):
            raise SystemExit("arm %s task set does not match bank %s" % (arm, entry["version"]))
        blank = sum(1 for r in rows if not raw.get((r["task"], str(r.get("rep"))), "").strip())
        if blank > 0.05 * len(rows):
            raise SystemExit("arm %s: %d/%d answers blank from the results file — the join key or "
                             "file layout changed; refusing to score empty strings" % (arm, blank, len(rows)))
        for r in rows:
            per[r["task"]][rid] = strict(r.get("content") or 0, r.get("format_ok"))
            events[(r["task"], rid)] = [str(e) for e in (r.get("events") or [])]

    for key, vals in stacks.items():
        if len(vals) > 1:
            raise SystemExit("arms disagree on %s: %s — cells from different stacks are never "
                             "joinable into one map" % (key, sorted(vals)))

    rids = [os.path.basename(a) for a in args.arms]
    ws_sha = next(iter(stacks["bank_sha16"]))
    contract = next(iter(stacks["scorer_contract"]))
    contract_sha = next(iter(stacks["contract_sha16"]))
    stamp_behaviour = args.stamp.split(".", 2)[-1] if args.stamp.count(".") >= 2 else args.stamp

    stable_pass, stable_fail, unstable = [], [], []
    for tid in sorted(per):
        vals = [per[tid].get(rid) for rid in rids]
        n = sum(1 for v in vals if v)
        if n == len(rids):
            stable_pass.append(tid)
        elif n == 0:
            stable_fail.append(tid)
        else:
            unstable.append((tid, n, vals))

    out = []
    w = out.append
    w("# Adopted-line live-rate map — contour %s (behavior %s), bank %s, %s"
      % (args.stamp, stamp_behaviour, entry["version"],
         datetime.now(timezone.utc).strftime("%Y-%m-%d")))
    w("")
    w("%d arms of the ADOPTED line, one per seed: %s. Strict rule `content==1.0 and format_ok`, "
      "scorer contract %s `%s`, bank %s published `%s` (workspace copy `%s`), seed protocol %s. "
      "%s" % (len(rids), " + ".join(rids), contract, contract_sha, entry["version"], pub_sha,
              ws_sha, next(iter(stacks["seed_protocol"])), args.seeds_note.strip()))
    w("Regenerated by `scripts/unstable_cells_v62.py` from the published ledgers + results files "
      "named above; no number in this file is typed by hand. This is the measurability gate table: "
      "a candidate stamp needs >=1 strict-fail HERE, never a base rate from older eras.")
    w("")
    w("| arm | box | model | bank | bank sha16 | contract | harness git | seed protocol |")
    w("|---|---|---|---|---|---|---|---|")
    for p in provenance:
        w("| %s | %s | %s | %s | %s | %s | %s | %s |" % p)
    w("")
    w("Legend per cell: `P` strict pass, `.` strict fail, in arm order %s. "
      "`contour-fired` string: `E` = a contour action was recorded on that cell/seed "
      "(event prefix %s), `-` = none. Loop cells are marked and included: they are the "
      "agent-loop pool whose ceiling is the bank minus single-shot-only tasks."
      % (" ".join(rids), ", ".join("`%s`" % p for p in FIRED_PREFIXES)))
    w("")
    w("stable pass %d, stable fail %d, seed-unstable %d of %d cells"
      % (len(stable_pass), len(stable_fail), len(unstable), len(per)))
    w("")
    w("Stable fails (bank or model ceiling, not a contour hypothesis): "
      + (", ".join(sorted(stable_fail)) or "none"))
    w("")
    for tid, n, vals in sorted(unstable, key=lambda x: (x[1], x[0])):
        fam = collections.Counter()
        for i, v in enumerate(vals):
            if v:
                continue
            for note in notes.get((tid, rids[i]), []):
                if note_family(note) in INFRA_NOTES:
                    continue
                fam[note_family(note)] += 1
        bits = "".join("P" if v else "." for v in vals)
        fired_bits = "".join("E" if fired(events.get((tid, rid), [])) else "-" for rid in rids)
        tag = " (loop)" if tid in loop else ""
        fams = "; ".join("%sx%d" % (f, c) for f, c in fam.most_common()) or "no scored note"
        w("- **%s**%s %d/%d pass [%s]; fail-note families: %s; contour-fired per arm: %s"
          % (tid, tag, n, len(rids), bits, fams, fired_bits))
        for i, v in enumerate(vals):
            if v:
                continue
            keep = [x for x in notes.get((tid, rids[i]), []) if note_family(x) not in INFRA_NOTES]
            w("    - %s: content/fail notes: %s" % (rids[i], keep if keep else "[]"))
    w("")
    loop_fail = sum(1 for t in loop if t in per and not all(per[t].values()))
    w("Summary: %d/%d cells strict-pass every arm; %d/%d have >=1 live failure. Loop pool (%d tasks) "
      "with >=1 failure: %d. Per-cell draw flips are expected at ~5%% (measured noise floor), so an "
      "%d/%d cell is lottery, not a hypothesis; a hypothesis needs repeat failures (<=%d/%d) with a "
      "STABLE note family."
      % (len(stable_pass), len(per), len(unstable) + len(stable_fail), len(per), len(loop),
         loop_fail, len(rids) - 1, len(rids), len(rids) - 2, len(rids)))
    w("")
    ev_census = collections.Counter()
    for (tid, rid), evs in events.items():
        if not per[tid].get(rid):
            for e in evs:
                ev_census[e.split(":")[0] + ":" + (e.split(":")[1] if ":" in e else "")] += 1
    w("Contour events recorded on FAILING cells (what the contour was doing while it failed): %s"
      % (", ".join("%s x%d" % (k, c) for k, c in ev_census.most_common(12)) or "none"))

    text = "\n".join(out) + "\n"

    def cell_table(s: str) -> str:
        """Everything from the provenance table down: the dated title and the prose
        above it may legitimately differ between generations, the numbers may not."""
        i = s.find("| arm |")
        return s[i:] if i >= 0 else s

    def repo_path(p: str) -> str:
        return p if os.path.isabs(p) else os.path.join(ROOT, p)

    if args.check:
        if not args.out:
            raise SystemExit("--check needs --out pointing at the committed map")
        committed = repo_path(args.out)
        if not os.path.exists(committed):
            raise SystemExit("committed map missing: %s" % committed)
        want, got = cell_table(open(committed, encoding="utf-8").read()), cell_table(text)
        if want != got:
            wl, gl = want.splitlines(), got.splitlines()
            for i in range(max(len(wl), len(gl))):
                a = wl[i] if i < len(wl) else "<eof>"
                b = gl[i] if i < len(gl) else "<eof>"
                if a != b:
                    raise SystemExit("MAP NOT REPRODUCIBLE at line %d:\n  committed: %s\n  "
                                     "regenerated: %s" % (i + 1, a[:160], b[:160]))
        print("map reproducible: %s matches the regenerated cell table "
              "(%d cells, %d unstable, stamp %s)"
              % (os.path.basename(committed), len(per), len(unstable), args.stamp))
        return 0

    if args.out:
        path = repo_path(args.out)
        open(path, "w", encoding="utf-8").write(text)
        print("wrote %s (%d cells, %d unstable)" % (path, len(per), len(unstable)))
    else:
        print(text)
    if args.csv:
        path = repo_path(args.csv)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("task,cat,loop,stamp,bank_version,bank_sha16,contract,fails,"
                     + ",".join(rids) + ",fail_note_families\n")
            for tid in sorted(per):
                vals = [per[tid].get(rid) for rid in rids]
                fam = sorted({note_family(x) for i, rid in enumerate(rids) if not vals[i]
                              for x in notes.get((tid, rid), []) if note_family(x) not in INFRA_NOTES})
                fh.write("%s,%s,%s,%s,%s,%s,%s,%d,%s,%s\n" % (
                    tid, bank[tid]["cat"], int(tid in loop), args.stamp, entry["version"], pub_sha,
                    contract, sum(1 for v in vals if not v),
                    ",".join("1" if v else "0" for v in vals), ";".join(fam)))
        print("wrote %s" % path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
