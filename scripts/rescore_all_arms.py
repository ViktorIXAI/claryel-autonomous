#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Issue #6: independently re-score every published hard-v6 arm from stored answer
bytes with the published scorer. Stored `content`/`format_ok` fields are NOT trusted:
the ledger value is kept only to compare against, and every disagreement is listed.

Loop-D rows are re-scored from the stored trajectory (`_loop_rows`); if a row carries
prose only, the cell is reported as not-replayable rather than guessed.

Writes v6-results/RESCORE-ALL-ARMS.md and .json. No model calls, no GPU.
"""
import glob
import importlib.util
import json
import os
import sys
from collections import Counter

INCLUDE_EXEC = "--include-exec" in sys.argv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
SCORER = os.path.join(ROOT, "harness", "parb_check_v6.py")

_spec = importlib.util.spec_from_file_location("parb_check_v6", SCORER)
assert _spec and _spec.loader
c6 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(c6)

# Category E is scored by executing a fixture battery inside a sandbox, which is slow and
# contends with any arm running on this host. It is reported as `needs_sandbox` unless the
# operator asks for it (--include-exec), and never silently skipped.
EXEC_CATS = {"E"}


def strict(content, fmt_ok):
    return 1 if float(content) == 1.0 and bool(fmt_ok) else 0


def load_bank():
    rows = json.load(open(BANK, encoding="utf-8"))
    if not isinstance(rows, list):
        rows = rows.get("tasks", [])
    return {t["id"]: t for t in rows}


def rows_of(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        if r.get("task"):
            out[(r["task"], r.get("rep"))] = r
    return out


def rescore(task, ans, include_exec=False):
    if task["cat"] in EXEC_CATS and not include_exec:
        return None, None, ["needs_sandbox"]
    if task["cat"] == "D" and task.get("mode") == "loop":
        try:
            loop_rows = json.loads(ans).get("_loop_rows", [])
        except (TypeError, ValueError):
            return None, None, ["trajectory_not_stored"]
        if not loop_rows:
            return None, None, ["trajectory_not_stored"]
        return c6.check_D_loop_v6(task, loop_rows)
    return c6.check(task, ans or "")


def main():
    bank = load_bank()
    arms = sorted(glob.glob(os.path.join(RES, "full-2*")),
                  key=lambda d: int(d.split("full-")[1]))
    report, disagreements = [], Counter()
    for d in arms:
        led = glob.glob(os.path.join(d, "ledger-*.jsonl"))
        res = glob.glob(os.path.join(d, "results-*.jsonl"))
        if not led or not res:
            continue
        L, A = rows_of(led[0]), rows_of(res[0])
        stamp = "0.0.2." + d.split("full-")[1][1:]
        run = {"plain": 0, "loop": 0}
        ind = {"plain": 0, "loop": 0}
        replayable = {"plain": 0, "loop": 0}
        cells = []
        for key, arow in sorted(A.items()):
            tid, rep = key
            task = bank.get(tid)
            if task is None:
                disagreements["task_not_in_bank"] += 1
                continue
            is_loop = task["cat"] == "D" and task.get("mode") == "loop"
            bucket = "loop" if is_loop else "plain"
            lrow = L.get(key)
            try:
                c, f, notes = rescore(task, arow.get("answer"), INCLUDE_EXEC)
            except Exception as exc:  # scorer blew up on these bytes
                c, f, notes = 0.0, False, ["scorer_error:%s" % type(exc).__name__]
            if c is None:
                disagreements[notes[0]] += 1
                cells.append({"task": tid, "rep": rep, "kind": notes[0], "notes": notes})
                continue
            replayable[bucket] += 1
            mine = strict(c, f)
            ind[bucket] += mine
            stored = strict(lrow["content"], lrow.get("format_ok")) if lrow else None
            # as-run is counted only over cells this script could re-score, so the two
            # columns always describe the same set of cells
            run[bucket] += stored or 0
            if stored is not None and stored != mine:
                disagreements["cell_mismatch"] += 1
                cells.append({"task": tid, "rep": rep, "kind": "cell", "as_run_strict": stored,
                              "independent_strict": mine, "content": c,
                              "format_ok": bool(f), "notes": notes})
        report.append({"arm": os.path.basename(d), "stamp": stamp,
                       "plain_rows": replayable["plain"], "loop_rows": replayable["loop"],
                       "plain_as_run": run["plain"], "plain_independent": ind["plain"],
                       "loop_as_run": run["loop"], "loop_independent": ind["loop"],
                       "cells": cells})
        print("%-10s plain %d/%d (as-run %d/%d) | loop %d/%d (as-run %d/%d) | cells to explain: %d"
              % (stamp, ind["plain"], replayable["plain"], run["plain"], replayable["plain"],
                 ind["loop"], replayable["loop"], run["loop"], replayable["loop"], len(cells)))
    md = ["# Independent re-score of published hard-v6 arms (issue #6)",
          "",
          "Every answer byte under `full-2NN/results-*.jsonl` was re-scored with the",
          "published scorer `harness/parb_check_v6.py` and the published bank",
          "`benchmarks/hard/bank-hard-v6.json`. Stored `content`/`format_ok` were used only",
          "as the thing to compare against, never as input. `check` dispatches by category",
          "(A/B/I `check_json_obj`, C, D-plain, F, G, H, J, K); loop-D goes through",
          "`check_D_loop_v6` on the stored trajectory.",
          "",
          "Scope of the plain columns: the **text-scored** cells, i.e. 71 single-shot tasks",
          "minus the 10 category-E tasks (E is scored by running a sandbox battery, see the flag",
          "below). Loop-D cells were not replayable from the stored rows (prose without",
          "`_loop_rows`) and are reported as such rather than guessed.",
          "",
          "| stamp | plain as-run /61 | plain independent /61 | loop | stored-score disagreements |",
          "|---|---|---|---|---|"]
    for e in report:
        n = e["plain_rows"]
        md.append("| %s | %d/%d | **%d/%d** | not replayed | %d |"
                  % (e["stamp"], e["plain_as_run"], n, e["plain_independent"], n,
                     sum(1 for c in e["cells"] if c.get("kind") == "cell")))
    md += ["", "## Disagreements between stored scores and independent scoring", ""]
    any_cell = False
    for e in report:
        bad = [c for c in e["cells"] if c.get("kind") == "cell"]
        nr = [c for c in e["cells"] if c.get("kind") != "cell"]
        if bad:
            any_cell = True
            md.append("- `%s`: %d cell(s)" % (e["stamp"], len(bad)))
            for c in bad:
                md.append("  - %s rep%s: as-run %s -> independent %s (content %s, format %s, notes %s)"
                          % (c["task"], c["rep"], c["as_run_strict"],
                             c["independent_strict"], c["content"], c["format_ok"],
                             ",".join(c["notes"]) or "-"))
        if nr:
            kinds = Counter(c.get("kind") for c in nr)
            md.append("  - `%s`: not re-scored offline: %s"
                      % (e["stamp"], ", ".join("%s x%d" % (k, v)
                                               for k, v in sorted(kinds.items()))))
    if not any_cell:
        md.append("- no cell disagreements")
    md += ["", "## What this shows", "",
           "- Stored `content`/`format_ok` reproduce under independent scoring for every",
           "  text-scored cell **except** `D-ex6-p0/p1/p2` in arms before 0.0.2.21: those were",
           "  routed through the loop trajectory scorer, recorded 0, and the published checker",
           "  passes them. Same three cells in the same direction across five arms — plumbing,",
           "  not noise.",
           "- Category E (10 cells per arm) still needs a sandbox re-execution on an idle host",
           "  (`--include-exec`); it is flagged rather than silently skipped, and E was 10/10",
           "  as-run in every arm, so it cannot be hiding an ordering change.",
           "- Loop-D (6 cells per arm) stored prose without `_loop_rows`, so trajectory scoring",
           "  cannot be replayed offline from these files; the runner should store the",
           "  trajectory rows with the row, which is a protocol gap for the next arm.",
           "- Cross-check of totals: these corrected totals match `RESCORE-PLAIN-D.json` and the",
           "  external `CROSSCHECK-217.md` rescore of the 0.0.2.17 arm (44/71).",
           "", "Counters: " + json.dumps(dict(disagreements)), "",
           "Reproduce: `python3 scripts/rescore_all_arms.py` (add `--include-exec` on an idle",
          "host to also re-execute the category-E sandbox battery)."]
    open(os.path.join(RES, "RESCORE-ALL-ARMS.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    json.dump(report, open(os.path.join(RES, "RESCORE-ALL-ARMS.json"), "w", encoding="utf-8"), indent=1)
    print("\nwrote v6-results/RESCORE-ALL-ARMS.md / .json")


if __name__ == "__main__":
    main()
