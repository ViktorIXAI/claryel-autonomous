#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""raw_gold_disagreement.py — mechanical gold-defect census from published raw arms.

Pattern (owner doctrine, executed by code): when EVERY external raw brain, on EVERY
rep, gives an answer the frozen scorer strict-fails, the gold — not the brains — is
the candidate defect. This is the machine form of the H-ex6-01 promotion evidence
("three independent raw brains 0/3") and complements the gold-atom scanners:
audit-v1/v2 see unnameable gold ATOMS in the prompt; this one sees gold VALUES
that every honest brain, asked the byte-identical prompt, refuses to produce.

Input: a cadence directory containing `cadence-cells-v62.csv` (published strict
scores from scripts/cadence_score_v62.py, contract-pinned) plus `answers-*.jsonl`
for the raw arms (used only to show the disagreeing answer signature).
Raw arms = every arm NOT named contour-*; the contour arm is reported but never
makes a candidate (scaffolding changes the comparison). Loop-task rows from raw
arms are absent by construction (single-shot transport ceiling), so no D-loop task
can be flagged from raw rows.

Census = CANDIDATES, not verdicts: a candidate becomes a published defect only
after the answer-byte read (both values + the task's rule text quoted) in the
bank changelog. Exit 0 always (census, not gate).
"""
import csv, hashlib, json, os, re, sys

def _sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]

ANSWER_SIG_LEN = 90

def answer_signature(txt):
    """Compact readable form of a raw answer for the census line."""
    s = " ".join((txt or "").split())
    m = re.findall(r"ОТВЕТ[:\s]*(.+)", s)
    if m:
        return "ОТВЕТ: " + m[-1][:40]
    return s[:ANSWER_SIG_LEN]

def main():
    if len(sys.argv) != 2:
        print(__doc__.splitlines()[1])
        return 2
    d = sys.argv[1]
    rows = list(csv.DictReader(open(os.path.join(d, "cadence-cells-v62.csv"))))
    if not rows:
        print("empty csv"); return 1
    bsha = rows[0]["bank_sha16"]
    contract = rows[0]["contract"]
    per = {}
    arms = set()
    for r in rows:
        arm = r["arm"]
        arms.add(arm)
        if arm.startswith("contour"):
            continue
        per.setdefault(r["task"], []).append((arm, r["rep"], r["strict"], r["cat"]))
    answers = {}
    for fn in sorted(os.listdir(d)):
        if fn.startswith("answers-") and fn.endswith(".jsonl"):
            for line in open(os.path.join(d, fn)):
                try: row = json.loads(line)
                except Exception: continue
                answers[(fn, row.get("task"), row.get("rep"))] = row.get("answer")
    raw_arms = sorted(set(a for rows_ in per.values() for (a, _, _, _) in rows_))
    flagged = []
    for tid, rr in sorted(per.items()):
        seen = set(a for (a, _, _, _) in rr)
        if len(seen) < 2 or not rr:
            continue
        if all(s == "False" for (_, _, s, _) in rr):
            sigs = set()
            for (a, rep, _, _) in rr:
                sig = answer_signature(answers.get((f"answers-{a}.jsonl", tid, rep), ""))
                sigs.add(f"{a}: {sig}")
            flagged.append((tid, len(rr), sorted(sigs)[:3]))
    print(f"SCAN-ID scanner=raw-gold-disagreement/{_sha16(__file__)} dir={os.path.basename(d)} "
          f"bank-sha16={bsha} contract={contract} raw-arms={raw_arms} "
          f"cells-scored={len(rows)} tasks-covered={len(per)}")
    print(f"CANDIDATES (every raw-arm row strict-fails, >=2 brains): {len(flagged)}")
    for tid, n, sigs in flagged:
        print(f"  {tid:12s} raw-rows={n:3d} disagreeing answers:")
        for s in sigs:
            print(f"      {s}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
