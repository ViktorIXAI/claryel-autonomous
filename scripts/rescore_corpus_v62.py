#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rescore EVERY published hard-v6 arm under the full v6.2 stack.

This is roadmap item R1+R2's consequence made mechanical: bank v6.2 corrected three
published defects, and contract v6.2 gave the scorer an identity. Both must be shown
cell by cell, not asserted. Every answer byte already published under
`benchmarks/hard/v6-results/` is re-scored twice from the same bytes:

  stack A (as run)      bank-hard-v6.json  + contract v6.1 bytes  + STRICT_RULE
  stack B (v6.2 stack)  bank-hard-v6.2.json + contract v6.2 module + STRICT_RULE

Contract v6.2 delegates to the frozen v6.1 callables, so it changes no score by
construction; the script PROVES that on every replayable cell (it compares the two
contracts on the same bank) and then reports the bank-only delta. Cells that cannot
be replayed offline (category E needs the docker battery, loop-D needs stored
trajectories) are counted and named, never scored as zero.

Writes:
  benchmarks/hard/v6-results/rescore-v62/CORPUS-CELLS-V62.csv   (one row per cell)
  benchmarks/hard/v6-results/rescore-v62/CORPUS-V62.md          (summary tables)
"""
from __future__ import annotations

import csv
import glob
import inspect
import json
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
import gate_scorer_contract as SC  # noqa: E402

RES = os.path.join(ROOT, "benchmarks", "hard", "v6-results")
BANK61 = json.load(open(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.json"), encoding="utf-8"))
BANK62 = json.load(open(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.2.json"), encoding="utf-8"))
T61 = {t["id"]: t for t in BANK61}
T62 = {t["id"]: t for t in BANK62}
INCLUDE_EXEC = "--include-exec" in sys.argv
FROZEN_SRC = os.path.realpath(os.path.join(ROOT, "harness", "parb_check_v6.py"))

# Contract v6.1 = the frozen bytes; contract v6.2 = the same callables plus identity.
V61 = SC.load_contract("v6.1")
V62 = SC.load_contract("v6.2")
# parb_check_v6.CHECKS omits K (its `check()` dispatches K specially), so both
# dispatch tables are built explicitly and are asserted equal below — two tables
# disagreeing is exactly how the 0.0.2.20 D-routing bug happened.
DISPATCH61 = {"A": V61.check_json_obj, "B": V61.check_json_obj, "C": V61.check_C_v6,
              "D": V61.check_D_plain_v6, "E": V61.run_battery, "F": V61.check_F_v6,
              "G": V61.check_G_v6, "H": V61.check_H_v6, "I": V61.check_json_obj,
              "J": V61.check_J_v6, "K": V61.check_K_v6}
DISPATCH62 = dict(V62.CHECK)
assert set(DISPATCH61) == set(DISPATCH62) == set("ABCDEFGHIJK"), "dispatch tables differ"
for _c in "ABCDEFGHIJK":
    _f1, _f2 = DISPATCH61[_c], DISPATCH62[_c]
    # The two contracts load the frozen module under different module names, so the
    # identity proof is: same function name, same source file, and that file is the
    # frozen scorer — not a copy somewhere on sys.path.
    assert _f1.__name__ == _f2.__name__ \
        and os.path.realpath(inspect.getsourcefile(_f1)) == FROZEN_SRC \
        and os.path.realpath(inspect.getsourcefile(_f2)) == FROZEN_SRC, \
        "contract v6.1 and v6.2 do not both run the frozen checker for %s" % _c
EXEC_CATS = set() if INCLUDE_EXEC else {"E"}

# Tasks whose PROMPT moved between banks (not just the gold): an old answer was not a
# reply to the new prompt, so its cell is reported but never read as a bank correction.
PROMPT_CHANGED = sorted(tid for tid in T61
                        if T61[tid].get("prompt") != T62[tid].get("prompt"))
GOLD_CHANGED = sorted(tid for tid in T61 if T61[tid].get("ref") != T62[tid].get("ref"))


def files():
    out = []
    # ONLY files that carry answer bytes. Ledger rows score but have no `answer`
    # field: an analysis that reads answers from a ledger re-scores an empty string
    # and fabricates a collapse diagnosis (that burned contour stamp 0.0.2.30).
    for pat in ("*/results-*.jsonl", "results-*.jsonl",
                "answers-*.jsonl", "*/answers-*.jsonl"):
        out += sorted(glob.glob(os.path.join(RES, pat)))
    return [f for f in dict.fromkeys(out)]


def rows_of(path):
    """Rows keyed by (task, rep); later rows win (results APPEND across attempts)."""
    out = {}
    for ln in open(path, encoding="utf-8"):
        ln = ln.strip()
        if not ln:
            continue
        try:
            r = json.loads(ln)
        except ValueError:
            continue
        if r.get("task"):
            out[(r["task"], r.get("rep"))] = r
    return out


def score(dispatch, task, row):
    """Return (content, format_ok, notes, why_not_replayable)."""
    cat = task["cat"]
    loop = cat == "D" and task.get("mode") == "loop"
    if cat in EXEC_CATS:
        return None, None, None, "needs_sandbox"
    if loop:
        try:
            tr = json.loads(row.get("answer") or "{}").get("_loop_rows")
        except (TypeError, ValueError):
            tr = None
        if not tr:
            return None, None, None, "trajectory_not_stored"
        c, f, n = V61.check_D_loop_v6(task, tr)
        return c, f, n, None
    try:
        c, f, n = dispatch[cat](task, row.get("answer") or "")
    except Exception as e:                      # never swallow silently: name the shape bug
        return None, None, None, "scorer_error:%s" % type(e).__name__
    return c, f, list(n), None


def main():
    out_dir = os.path.join(RES, "rescore-v62")
    os.makedirs(out_dir, exist_ok=True)
    cells = []
    not_replay = Counter()
    contract_flips = 0
    per_task_win = Counter()
    per_task_lose = Counter()
    per_arm = defaultdict(lambda: {"a": 0, "b": 0, "n": 0})
    blanks = Counter()

    for path in files():
        rel = os.path.relpath(path, RES)
        if "/e-sbx" in rel:
            continue
        R = rows_of(path)
        for (tid, rep), row in sorted(R.items()):
            t61, t62 = T61.get(tid), T62.get(tid)
            if t61 is None or t62 is None:
                not_replay["task_not_in_bank"] += 1
                continue
            ans = (row.get("answer") or "").strip()
            if not ans:
                blanks[rel] += 1
                not_replay["empty_answer"] += 1
                continue
            c1, f1, n1, why1 = score(DISPATCH61, t61, row)
            if why1:
                not_replay[why1] += 1
                continue
            # same bank, other contract: contract v6.2 must change nothing
            cc1, cf1, cn1, _ = score(DISPATCH62, t61, row)
            if (cc1, bool(cf1), list(cn1)) != (c1, bool(f1), list(n1)):
                contract_flips += 1
            c2, f2, n2, why2 = score(DISPATCH62, t62, row)
            if why2:
                not_replay[why2] += 1
                continue
            s1 = 1 if (float(c1) == 1.0 and bool(f1)) else 0
            s2 = 1 if (float(c2) == 1.0 and bool(f2)) else 0
            flip = "WIN" if (s2 and not s1) else ("LOSE" if (s1 and not s2) else "")
            if flip == "WIN":
                per_task_win[tid] += 1
            elif flip == "LOSE":
                per_task_lose[tid] += 1
            a = per_arm[rel]
            a["a"] += s1
            a["b"] += s2
            a["n"] += 1
            ax = SC.axes(c2, f2, n2, loop=(t62["cat"] == "D" and t62.get("mode") == "loop"),
                         ref=t62.get("ref") or {})
            cells.append({
                "arm": rel, "task": tid, "cat": t61["cat"], "rep": rep,
                "stack_a_strict": s1, "stack_b_strict": s2, "flip": flip,
                "a_content": c1, "a_format": int(bool(f1)),
                "b_content": c2, "b_format": int(bool(f2)),
                "a_notes": ";".join(str(x) for x in n1)[:160],
                "b_notes": ";".join(str(x) for x in n2)[:160],
                "codes_v62": ";".join(SC.typed_codes(n2)),
                "classes_v62": ";".join(sorted(SC.code_classes(n2))),
                "answer_axis": ax.get("answer_axis"), "protocol_axis": ax.get("protocol_axis"),
                "blocking_v62": ";".join(ax.get("blocking_codes") or []),
                "scorer_a": "v6.1", "scorer_b": SC.SCORER_CONTRACT,
                "bank_a_sha16": SC._sha16(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.json")),
                "bank_b_sha16": SC._sha16(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.2.json")),
                "comparable": "prompt_changed_in_v62" if tid in PROMPT_CHANGED else "yes",
            })

    csv_path = os.path.join(out_dir, "CORPUS-CELLS-V62.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cells[0].keys()))
        w.writeheader()
        w.writerows(cells)

    cells_by_task = Counter(r["task"] for r in cells)
    wins = sum(per_task_win.values())
    loses = sum(per_task_lose.values())
    tot_a = sum(a["a"] for a in per_arm.values())
    tot_b = sum(a["b"] for a in per_arm.values())
    n = len(cells)

    md = ["# Corpus re-score under the v6.2 measurement stack",
          "",
          "Bank **v6.1** `sha16 %s` + scorer contract **v6.1** (frozen bytes, hash-pinned by"
          % SC._sha16(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.json")),
          "`harness/gate_scorer_contract.py`) versus bank **v6.2** `sha16 %s` + scorer contract"
          % SC._sha16(os.path.join(ROOT, "benchmarks/hard/bank-hard-v6.2.json")),
          "**v6.2** (same frozen checkers, reached by delegation). Strict rule in both stacks:",
          "`%s`. Every cell was re-scored from the same published answer bytes; nothing here is"
          % SC.STRICT_RULE,
          "a model call, a contour run, or an edited artifact.",
          "",
          "| measure | value |",
          "|---|---|",
          "| re-scored cells (replayable) | %d |" % n,
          "| contract v6.1 vs v6.2 disagreements on the same bank | **%d** |" % contract_flips,
          "| cells that changed because of the bank correction | %d wins / %d losses |" % (wins, loses),
          "| strict total, stack A (v6.1 bank + v6.1 contract) | %d |" % tot_a,
          "| strict total, stack B (v6.2 bank + v6.2 contract) | %d |" % tot_b,
          "| empty answer rows (never scored) | %d |" % sum(blanks.values()),
          "",
          "Cells that cannot be re-scored offline, counted rather than guessed: "
          + ", ".join("`%s` x%d" % (k, v) for k, v in sorted(not_replay.items())) + ".",
          "",
          "## What changed, task by task",
          "",
          "Bank v6.2 moved the gold of %s and the prompt of %s. Any other task changing"
          % (", ".join("`%s`" % t for t in GOLD_CHANGED),
             ", ".join("`%s`" % t for t in PROMPT_CHANGED)),
          "would be a scorer-routing bug, not a correction.",
          "",
          "| task | cells re-scored | wins | losses |",
          "|---|---|---|---|"]
    for tid in sorted(set(per_task_win) | set(per_task_lose)):
        md.append("| `%s` | %d | %d | %d |"
                  % (tid, cells_by_task[tid], per_task_win[tid], per_task_lose[tid]))
    md += ["",
           "Reconciling with `rescore-v62/RESCORE-V62.md`: that run re-scored only the two",
           "defect cells over the 106 arm files published at the time (120 rows each, 44 and 27",
           "wins). This run covers every answer file in the tree — %d files, %d replayable cells —"
           % (len(per_arm), n),
           "so the same two defects show more converted cells (%d and %d): the arms published"
           % (per_task_win.get("A-ex6-03", 0), per_task_win.get("C-ex6-02", 0)),
           "after it (`pair-244`, `pair-245`, loop arms) are included. Same arithmetic, wider",
           "coverage; neither table replaces the other and both name this stack.",
           ""]
    md += ["",
           "## Per-arm totals over the replayable set",
           "",
           "| arm | cells | stack A strict | stack B strict | delta |",
           "|---|---|---|---|---|"]
    for rel in sorted(per_arm):
        a = per_arm[rel]
        md.append("| `%s` | %d | %d | %d | %+d |" % (rel, a["n"], a["a"], a["b"], a["b"] - a["a"]))
    md += ["",
           "## Reading rules",
           "",
           "- `comparable = prompt_changed_in_v62` marks cells whose prompt moved with the bank;",
           "  an answer recorded before v6.2 is not a reply to the v6.2 prompt, so those cells are",
           "  reported but never read as a correction (they need a fresh arm on v6.2).",
           "- Category E is scored by executing a battery in a docker sandbox; pass `--include-exec`",
           "  on an idle host (never while an arm is live) to replay it.",
           "- Loop-D cells are replayable only when the arm stored `_loop_rows`; arms that stored prose",
           "  are reported as `trajectory_not_stored`. That is a protocol gap in those old arms, not",
           "  a scoring result, and the axes/typed codes below come from the stored notes instead.",
           "- Published v6.1 tables keep their v6.1 numbers and their bank hash. A v6.1 number and a",
           "  v6.2 number never sit in one column.",
           "",
           "Reproduce: `python3 scripts/rescore_corpus_v62.py` (add `--include-exec` on an idle host).",
           "Stack identity for every element: `versions/MEASUREMENT-STACK.md`.",
           ""]
    with open(os.path.join(out_dir, "CORPUS-V62.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(md))

    print("cells %d | contract disagreements %d | bank wins %d losses %d | strict A %d -> B %d"
          % (n, contract_flips, wins, loses, tot_a, tot_b))
    print("not replayable:", dict(not_replay))
    print("wrote", os.path.relpath(csv_path, ROOT), "and",
          os.path.relpath(os.path.join(out_dir, "CORPUS-V62.md"), ROOT))
    if contract_flips:
        print("FATAL: contract v6.2 changed scores — the delegation claim is false")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
