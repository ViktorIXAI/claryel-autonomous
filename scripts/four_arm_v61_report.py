#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Four-arm scoreboard on the CURRENT bank (issue: cadence every 5 contour stamps).

Arms (hard bank v6.1, one rep, same prompts, pinned scorer `harness/parb_check_v6.py`):
  contour  - full 77 tasks incl. loop-D (loop cells exist only for this arm)
  basalt   - bare model, direct HTTP, no contour, no fixers
  codex    - ChatGPT via Codex CLI, reasoning xhigh, read-only
  grok     - Grok 4.7 via hermes CLI, toolsets disabled, prompt inline

Raw arms cannot emit loop-D trajectories, so every multi-arm table uses the common set of
71 single-shot tasks and states that loop-D is N/A for raw arms. Category E is scored by
running a sandbox battery: it is included only when `--include-exec` is passed on a host
with docker, otherwise reported as `exec pending` and excluded from the paired test.
"""
import glob
import importlib.util
import json
import os
import sys
from collections import Counter
from math import comb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "harness"))
_spec = importlib.util.spec_from_file_location("parb_check_v6", os.path.join(ROOT, "harness", "parb_check_v6.py"))
assert _spec and _spec.loader
CK = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CK)

BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
RAW = os.path.expanduser("~/parb-v61-raw")
CONTOUR_WS = os.path.expanduser("~/parb-v61-contour")
EXEC_CATS = {"E"}
INCLUDE_EXEC = "--include-exec" in sys.argv


def bank_rows():
    rows = json.load(open(BANK, encoding="utf-8"))
    return {t["id"]: t for t in (rows if isinstance(rows, list) else rows.get("tasks", []))}


def strict(c, f):
    return 1 if float(c) == 1.0 and bool(f) else 0


def score_answer(task, ans):
    if task["cat"] in EXEC_CATS and not INCLUDE_EXEC:
        return None, None, ["exec_pending"]
    return CK.check(task, ans or "")


def load_raw(path, bank):
    out = {}
    if not os.path.exists(path):
        return out
    for line in open(path, encoding="utf-8"):
        r = json.loads(line)
        t = bank.get(r["task"])
        if t is None or (t["cat"] == "D" and t.get("mode") == "loop"):
            continue
        c, f, n = score_answer(t, r.get("answer"))
        out[r["task"]] = (c, f, n)
    return out


def load_contour(ws, bank):
    res, led = {}, {}
    for line in glob.glob(os.path.join(ws, "results-c228v61.jsonl")):
        for l in open(line, encoding="utf-8"):
            r = json.loads(l)
            res[(r["task"], r.get("rep"))] = r
    for line in glob.glob(os.path.join(ws, "ledger-c228v61.jsonl")):
        for l in open(line, encoding="utf-8"):
            r = json.loads(l)
            led[(r["task"], r.get("rep"))] = r
    out, loop_cells = {}, {}
    for (tid, rep), r in res.items():
        t = bank[tid]
        if t["cat"] == "D" and t.get("mode") == "loop":
            lr = led.get((tid, rep))
            loop_cells[tid] = strict(lr["content"], lr.get("format_ok")) if lr else 0
            continue
        c, f, n = score_answer(t, r.get("answer"))
        out[tid] = (c, f, n)
    return out, loop_cells


def mcnemar(a, b, keys):
    p_ = sum(1 for k in keys if a[k][0] is not None and strict(a[k][0], a[k][1])
             and not (b[k][0] is not None and strict(b[k][0], b[k][1])))
    q = sum(1 for k in keys if b[k][0] is not None and strict(b[k][0], b[k][1])
            and not (a[k][0] is not None and strict(a[k][0], a[k][1])))
    n = p_ + q
    if n == 0:
        return p_, q, 1.0
    k = min(p_, q)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2 ** n)
    return p_, q, min(1.0, 2 * tail)


def main():
    bank = bank_rows()
    arms = {
        "contour": load_contour(CONTOUR_WS, bank)[0],
        "basalt": load_raw(os.path.join(RAW, "answers-basalt.jsonl"), bank),
        "codex": load_raw(os.path.join(RAW, "answers-codex.jsonl"), bank),
        "grok": load_raw(os.path.join(RAW, "answers-grok.jsonl"), bank),
    }
    _, loop_cells = load_contour(CONTOUR_WS, bank)
    present = {k: v for k, v in arms.items() if v}
    if not present:
        sys.exit("no arm answer files found yet")
    scored = {k: {t: v for t, v in d.items() if v[0] is not None} for k, d in present.items()}
    common = sorted(set.intersection(*[set(d) for d in scored.values()])) if scored else []
    md = ["# Four-arm on bank v6.1 (contour 0.0.2.28)", "",
          "Bank `benchmarks/hard/bank-hard-v6.json` (v6.1), scorer `harness/parb_check_v6.py`, one rep.",
          "Common set = %d single-shot tasks scored in every listed arm; loop-D is N/A for raw arms"
          " (single-shot chat cannot emit the loop trajectory), category E = %s."
          % (len(common), "scored" if INCLUDE_EXEC else "exec pending, excluded"), "",
          "| arm | answers scored | strict on common set /%d | wins vs contour | losses vs contour | exact sign-test p |" % len(common),
          "|---|---|---|---|---|---|"]
    c = scored.get("contour", {})
    for name in ("contour", "codex", "grok", "basalt"):
        d = scored.get(name)
        if not d:
            md.append("| %s | (no answers yet) | - | - | - | - |" % name)
            continue
        on_common = sum(strict(*d[t][:2]) for t in common if t in d)
        if name == "contour" or not c:
            md.append("| %s | %d | **%d/%d** | - | - | - |"
                      % (name, len(d), on_common, len(common)))
            continue
        w, l, p = mcnemar(c, d, common)
        md.append("| %s | %d | **%d/%d** | %d | %d | %.4f |"
                  % (name, len(d), on_common, len(common), w, l, p))
    md += ["", "## Per category (strict / n on the common set)", "",
           "| cat | " + " | ".join(arms) + " | n |",
           "|---|" + "---|" * (len(arms) + 1)]
    cats = sorted({bank[t]["cat"] for t in common})
    for cat in cats:
        ids = [t for t in common if bank[t]["cat"] == cat]
        cells = []
        for name in arms:
            d = scored.get(name, {})
            have = [t for t in ids if t in d]
            cells.append("%d/%d" % (sum(strict(*d[t][:2]) for t in have), len(have)) if have else "-")
        md.append("| %s | " % cat + " | ".join(cells) + " | %d |" % len(ids))
    if loop_cells:
        md += ["", "Loop-D (contour arm only): %d/%d strict — %s"
               % (sum(loop_cells.values()), len(loop_cells),
                  ", ".join("%s=%s" % (k, v) for k, v in sorted(loop_cells.items())))]
    md += ["", "Raw-arm transports: basalt direct HTTP temp 0.7 seed 1000+rep; codex CLI xhigh",
           "read-only; grok hermes CLI with toolsets disabled and the prompt inline (finding S3).",
           "Reproduce: `python3 scripts/four_arm_v61_report.py` (add `--include-exec` on a docker host)."]
    out = os.path.join(ROOT, "benchmarks", "hard", "v6-results", "four-arm-v61", "FOUR-ARM-V61.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write("\n".join(md) + "\n")
    print("\n".join(md))
    print("\nwrote benchmarks/hard/v6-results/four-arm-v61/FOUR-ARM-V61.md")


if __name__ == "__main__":
    main()
