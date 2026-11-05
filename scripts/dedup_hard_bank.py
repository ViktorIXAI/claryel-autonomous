#!/usr/bin/env python3
"""Dedup guard for hard bank: fail if byte-identical or near-duplicate prompts.

Usage:
  python3 scripts/dedup_hard_bank.py [path/to/bank-hard.json]

Exit 0 iff all prompts unique under whitespace-normalized equality and
pairwise SequenceMatcher ratio < MAX_SIM (default 0.92).
"""
from __future__ import annotations
import json, sys, unicodedata, re
from pathlib import Path
from difflib import SequenceMatcher

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "benchmarks" / "hard" / "bank-hard.json"
MAX_SIM = 0.92
EXPECTED_N = 77
EXPECTED_CATS = {"A": 4, "B": 4, "C": 6, "D": 9, "E": 30, "F": 3, "G": 6, "H": 4, "I": 3, "J": 4, "K": 4}


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s or "")
    return re.sub(r"\s+", " ", s).strip().lower()


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    bank = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(bank, list):
        print("FAIL: bank is not a list", file=sys.stderr)
        return 2
    if len(bank) != EXPECTED_N:
        print(f"FAIL: expected {EXPECTED_N} tasks, got {len(bank)}", file=sys.stderr)
        return 2
    from collections import Counter
    cats = Counter(t.get("cat") for t in bank)
    if dict(cats) != EXPECTED_CATS:
        print(f"FAIL: cat counts {dict(cats)} != {EXPECTED_CATS}", file=sys.stderr)
        return 2

    prompts = [(t.get("id"), t.get("prompt") or "") for t in bank]
    norms = [(i, norm(p)) for i, p in prompts]
    # byte / normalized identical
    seen = {}
    dups = []
    for tid, n in norms:
        if n in seen:
            dups.append((seen[n], tid))
        else:
            seen[n] = tid
    if dups:
        print("FAIL: identical prompts:", dups, file=sys.stderr)
        return 1

    worst = (0.0, None, None)
    for i in range(len(norms)):
        for j in range(i + 1, len(norms)):
            # skip different categories for soft near-dup? No — all pairs.
            r = SequenceMatcher(None, norms[i][1], norms[j][1]).ratio()
            if r > worst[0]:
                worst = (r, norms[i][0], norms[j][0])
    print(f"unique={len(norms)} worst_sim={worst[0]:.4f} pair=({worst[1]},{worst[2]}) threshold={MAX_SIM}")
    if worst[0] >= MAX_SIM:
        print(f"FAIL: near-duplicate prompts {worst[1]} ~ {worst[2]} sim={worst[0]:.4f}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
