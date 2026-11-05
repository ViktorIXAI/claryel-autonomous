#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate benchmarks/hard/v6-results/LADDER.md from the PUBLISHED arms (not from writeups).

Reads every `full-2NN/ledger-*.jsonl` (ledger rows carry content/format_ok), dedupes by
(task,rep) keeping the best score, splits plain vs loop tasks from the bank, and prints the
stamp ladder plus per-category strict. Numbers therefore always come from the artifacts, so a
published scoreboard can be re-derived by anyone who runs this file.
Usage: python3 scripts/ladder_v6.py [V6_RESULTS_DIR]
"""
import collections
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RES = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "benchmarks", "hard", "v6-results")
BANK = os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")

CHANGES = {
    "0.0.2.16": "loop-v2 drive: protocol re-ask, in-place gate_rejected, salvage the model's own answer",
    "0.0.2.17": "deterministic format repair unbundled from CHECKER_INJECT (reaches the official score)",
    "0.0.2.18": "K boolean true/false -> yes/no",
    "0.0.2.19": "H JSON: clear fabricated claims / empty actions_done (scorer fail-hard notes)",
    "0.0.2.20": "K Cyrillic \u0434\u0430/\u043d\u0435\u0442 -> yes/no",
    "0.0.2.21": "D-plain scored by check_D_plain_v6 (plain D was mis-routed through the loop scorer)",
    "0.0.2.22": "F JSON: next short-id + empty avoid backfilled from the prompt's own options",
    "0.0.2.23": "K SERVICE alias: Cyrillic hosting forms -> Latin 'hosting'",
    "0.0.2.24": "I duration rows re-sorted by seconds ascending (keyword-free)",
    "0.0.2.25": "G conflict JSON emitted by code when the prompt states a no-stacking rule",
    "0.0.2.26": "G conflict overwrite: existing conflict:true with wrong clauses/values",
    "0.0.2.27": "A arithmetic computed from the numbers in the prompt (VAT, FX, proration, trimmed mean)",
    "0.0.2.28": "H requires/unknown filled from an explicit prompt signature constraint",
}

REF = ("grok raw **59/71**, codex raw **49/71**, basalt bare **49/71**; the original contour "
       "0.0.2.14 arm was **43/71** with loop 1/6")


def strict(r):
    return (r.get("content") or 0) == 1.0 and bool(r.get("format_ok"))


def main():
    bank = {t["id"]: t for t in json.load(open(BANK, encoding="utf-8"))}
    loop = {k for k in bank if bank[k].get("mode") == "loop"}
    rows = []
    for d in sorted(glob.glob(os.path.join(RES, "full-2*"))):
        lf = sorted(glob.glob(os.path.join(d, "ledger-*.jsonl")))
        if not lf:
            continue
        led = [json.loads(l) for l in open(lf[0], encoding="utf-8")]
        best = {}
        for r in led:
            k = (r["task"], r["rep"])
            s = (r.get("content") or 0) + (1 if r.get("format_ok") else 0)
            if k not in best or s > ((best[k].get("content") or 0) + (1 if best[k].get("format_ok") else 0)):
                best[k] = r
        pl = [r for k, r in best.items() if k[0] not in loop]
        lp = [r for k, r in best.items() if k[0] in loop]
        cat = collections.defaultdict(lambda: [0, 0])
        for k, r in best.items():
            c = k[0][0]
            cat[c][1] += 1
            cat[c][0] += strict(r)
        rows.append((led[0].get("contour_version"), len(best),
                     sum(strict(r) for r in pl), len(pl),
                     sum(strict(r) for r in lp), len(lp),
                     " ".join(f"{c}{cat[c][0]}/{cat[c][1]}" for c in sorted(cat))))
    out = [f"# contour ladder on hard bank v6 (rep0, identical gseeds)",
           "",
           f"Bank source of truth `benchmarks/hard/bank-hard-v6.json` sha16 `{sha16(BANK)}`. Every arm in",
           "this ladder ran against the generated workspace copy `bank.json` (re-serialized, therefore a",
           "different hash): sha16 `f52acbd15b3271e7`, the identity pinned in `v6-results/README.md` and",
           "printed by `scripts/build_hard_v6_ws.py` at build time. Bank **v6.1** (J defect fixes, see",
           "`BANK-V61.md`) re-pins the workspace to a new hash and is NOT part of this ladder.",
           "",
           "Recomputed by `scripts/ladder_v6.py` from the **published ledgers** (ledger rows carry",
           "`content`/`format_ok`) \u2014 not copied from run writeups. Every row also has its per-task",
           "answer bytes in the same directory (`results-*.jsonl`), so any cell can be re-scored.",
           "",
           "| stamp | plain strict /71 | plain corrected /71 | loop strict /6 | rows | per-category strict (77 incl. loop) | what the stamp changed |",
           "|---|---|---|---|---|---|---|"]
    corr = {}
    rp = os.path.join(RES, "RESCORE-PLAIN-D.json")
    if os.path.exists(rp):
        for e in json.load(open(rp, encoding="utf-8")):
            corr[e["stamp"]] = e["plain_corrected"]
    for s, n, ps, pn, ls, ln, cats in rows:
        c = corr.get(s)
        cell = f"**{c}/{pn}**" if c is not None and c != ps else ("=" if c == ps else "-")
        out.append(f"| {s} | **{ps}/{pn}** | {cell} | {ls}/{ln} | {n} | {cats} | {CHANGES.get(s, '')} |")
    last = rows[-1] if rows else None
    out += ["", f"Reference single-shot arms on the same bank (`FOUR-ARM-SCOREBOARD.md`, no contour): {REF}.",
            "",
            "## Verdict"]
    if last:
        best = max((corr.get(r[0], r[2]) for r in rows), default=0)
        best_stamp = max((r[0] for r in rows if corr.get(r[0], r[2]) == best), default=last[0])
        out.append(f"- Contour line reaches **{best}/{last[3]}** plain (corrected) at {best_stamp};"
                   f" the last measured stamp {last[0]} sits at {corr.get(last[0], last[2])}/{last[3]}"
                   f" (loop {last[4]}/{last[5]}). Corrected ladder: "
                   + " -> ".join(str(corr.get(r[0], r[2])) for r in rows) + ".")
    out += ["- `plain corrected` re-scores the same published answer bytes with the frozen checker",
            "  (`scripts/rescore_v6_cells.py` -> `RESCORE-PLAIN-D.json`). Stamps before 0.0.2.21 routed",
            "  the three plain-D tasks (`D-ex6-p0/p1/p2`) through the loop trajectory scorer and scored",
            "  0/3 on all of them, so their as-run totals are understated by exactly 3 cells; 0.0.2.21",
            "  fixed the routing, which is why its as-run +3 disappears under correction. Cross-check:",
            "  the corrected 0.0.2.17 total 44/71 equals the independent external rescore in",
            "  `CROSSCHECK-217.md` — two scorers, same bytes, same number.",
            "- Nearly every step is measurement validity in the contour/scorer plumbing, not a model",
            "  change (K yes/no synonyms, H claim clearing, plain-D scorer routing, F option",
            "  backfill, keyword-free format repair).",
            "- J sat at 3/7 for every stamp on bank v6: 2 of the 4 lost cells were bank defects",
            "  (`j-probe-218/J-PROBE.md`), fixed in bank v6.1 (`BANK-V61.md`).",
            "- A (arithmetic) stays the weakest real category, 4-5/9.",
            "- Which stamp got which cell is attributed by ledger events inside the arm, not by"
            "  guessing: 0.0.2.25 and 0.0.2.28 ran their own full arms; 0.0.2.24/0.0.2.26/0.0.2.27"
            "  shipped as offline replay evidence first and are carried inside those arms"
            "  (0.0.2.24 shows up as I 6/6 in full-225, 0.0.2.26/0.0.2.27 as the G and A wins in"
            "  `full-228/pair-225-228.txt`). None of the three has its own contract test yet.",
            "",
            "## Bounds on these numbers",
            "",
            "Bank v6.1 baseline for this line: `four-arm-v61/FOUR-ARM-V61.md` (contour 0.0.2.28"
            " = 61/71, bare basalt 56/71, Grok 54/71, ChatGPT 50/71 on generated bank"
            " `f4553aab304f60d7`); the cross-bank reading is `four-arm-v61/VS-V6.md`. These ladder"
            " rows were measured on the pre-v6.1 generated bank, so compare trends only.",
            "- One rep per stamp. Several arms shared the endpoint with other arms running at the same",
            "  time (each writeup says so); contention moves +-2-4 discordant cells, so the ladder is",
            "  trend + mechanism, not an effect size. Only 2.16->2.17 (full bank) and the loop-only",
            "  2.15->2.16 pair were measured back-to-back with the endpoint otherwise idle.",
            "- A per-pair flip list for each step lives in the newest directory (`pair-2NN-2MM.txt`).",
            "- The per-category column is **as-run**: in every row up to 0.0.2.20 the three plain-D",
            "  tasks are mis-scored there too, so D in those rows reads 3 cells low; `RESCORE-PLAIN-D.json`",
            "  carries the corrected per-cell detail.",
            ]
    open(os.path.join(RES, "LADDER.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")
    print("\n".join(out))


def sha16(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


if __name__ == "__main__":
    main()
