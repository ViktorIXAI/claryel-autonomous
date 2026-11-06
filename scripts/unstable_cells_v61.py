#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cell stability map for one contour stamp over many seeds: which cells are coin flips, and why they fail.

The repeated-seed protocol says a single number is noise-limited; the more useful product of repetitions is
the stability map: cells that pass every seed, cells that fail every seed, and the coin-flip cells in
between. Coin flips are where a contour mechanism can earn *stability*, which is cheaper to prove than a
mean shift: converting a 3/6 cell into a 6/6 cell is visible per cell.

For each unstable cell this prints the per-seed pass pattern, the frozen scorer's reason string in the
failing seeds (recomputed from the published answer bytes), and any contour events recorded in the ledger.

Usage: python3 scripts/unstable_cells_v61.py > UNSTABLE-CELLS-V61.md
"""
import collections
import glob
import importlib.util
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
V6 = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
CATS_ORDER = 0


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))


def strict(c, f):
    return c == 1.0 and bool(f)


def main() -> int:
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    ledgers = [os.path.join(V6, "full-229", "ledger-c229full.jsonl")] + sorted(
        glob.glob(os.path.join(V6, "reps-229", "ledger-c229r*.jsonl")))
    answers = {}
    events = {}
    per = collections.defaultdict(dict)   # task -> rep -> bool
    for p in ledgers:
        for line in open(p, encoding="utf-8"):
            r = json.loads(line)
            if "_loop_rows" in r or r["task"] in loop:
                continue
            rep = str(r.get("rep"))
            per[r["task"]][rep] = strict(r.get("content") or 0, r.get("format_ok"))
            answers[(r["task"], rep)] = r.get("answer") or ""
            events[(r["task"], rep)] = r.get("contour_events") or []
    reps = sorted({rep for d in per.values() for rep in d})
    print("# Contour cell stability across %d seeds (stamp 0.0.2.29, bank v6.1)" % len(reps))
    print()
    print("Ledgers: %s. Reason strings are recomputed from the published answer bytes with the frozen "
          "scorer; contour events come from the same ledger rows." % ", ".join(
              os.path.basename(p) for p in ledgers))
    print()
    stable_pass, stable_fail, unstable = [], [], []
    for tid, d in sorted(per.items()):
        vals = [d.get(rep) for rep in reps]
        n = sum(1 for v in vals if v)
        if n == len(vals):
            stable_pass.append(tid)
        elif n == 0:
            stable_fail.append(tid)
        else:
            unstable.append((tid, n, vals))
    print("stable pass %d, stable fail %d, seed-unstable %d of %d cells" % (
        len(stable_pass), len(stable_fail), len(unstable), len(per)))
    print()
    print("Stable fails (candidate bank or model ceiling): " + ", ".join(sorted(stable_fail)))
    print()
    print("| task | cat | passes / seeds | reason in a failing seed | contour events in a failing seed |")
    print("|---|---|---|---|---|")
    for tid, n, vals in sorted(unstable, key=lambda x: (x[1], x[0])):
        task = bank[tid]
        fail_rep = next((reps[i] for i, v in enumerate(vals) if not v), None)
        reason = ""
        if fail_rep is not None:
            ans = answers.get((tid, fail_rep), "")
            if task["cat"] == "E":
                reason = "E category: executed in docker, see E-EXEC.json"
            else:
                c, f, det = CK.check(task, ans)
                reason = "%s content=%.2f format=%s %s" % (task.get("kind", "?"), c, f,
                                                           (det or "")[:80] if det else "")
        ev = ""
        if fail_rep is not None:
            ev = ",".join(events.get((tid, fail_rep), []))[:80]
        print("| %s | %s | %d/%d (%s) | %s | %s |" % (
            tid, task["cat"], n, len(vals),
            "".join("P" if v else "." for v in vals), reason.replace("|", "/"), ev.replace("|", "/") or "—"))
    print()
    print("Reading rule: a cell that flips between seeds is not a scoring mystery, it is the model giving a")
    print("different answer under a different seed. Only a mechanism that makes the model re-check that")
    print("answer can convert it, and converting it is measurable cell by cell.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
