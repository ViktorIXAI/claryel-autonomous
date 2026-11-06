#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bank validity probe: does the prompt contain what the reference asks for?

The H/K/F scorers are generic: they score token coverage of the model answer against the bank's gold
`ask` items (`harness/parb_check_v6.py`, `check_H_v6` and friends). That makes the bank, not the scorer,
the place where an unreachable requirement lives: if a gold ask item contains tokens the prompt never
states, no answer can earn that point honestly. Two such cells are already documented
(`bank-defect-b04.md`: B-ex6-04 asks for a year the prompt never gives, H-ex6-01 requires an artifact
name the prompt never names).

This probe runs the scorer's own token-coverage function over every task's gold ask items against the
task prompt, so the check uses the same definition of "covered" that scoring uses. It reports candidates,
not verdicts: an ask item can be legitimately inferable (a computed total, a paraphrase) without sharing
surface tokens.

Usage: python3 scripts/bank_ask_coverage.py [BANK.json] > BANK-ASK-COVERAGE.md
"""
import importlib.util
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None, "missing harness module: " + path
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CK = _load("ck", os.path.join(ROOT, "harness", "parb_check_v6.py"))


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "benchmarks", "hard", "bank-hard-v6.json")
    tasks = json.load(open(path, encoding="utf-8"))
    print("# Gold-ask coverage probe (bank vs prompt, scorer's own coverage rule)")
    print()
    print("Bank: `%s`. For every task, each gold `ask` item is tested against the prompt with the same "
          "`_token_cover` the scorer uses. Flagged items are **candidates**: some are legitimately "
          "inferable (computed sums, paraphrases), so the row is a question to answer, not a verdict." % os.path.basename(path))
    print()
    print("| task | cat | gold ask item | covered by prompt? | tokens missing |")
    print("|---|---|---|---|---|")
    flagged = []
    checked = 0
    for t in tasks:
        ref = t.get("ref")
        if isinstance(ref, dict):
            asks = list(ref.get("ask") or [])
        elif isinstance(ref, list):
            asks = [x if isinstance(x, str) else json.dumps(x, ensure_ascii=False) for x in ref]
        else:
            asks = []
        if not asks:
            continue
        prompt = t.get("prompt") or t.get("content") or ""
        for a in asks:
            checked += 1
            ok = CK._token_cover(prompt, [str(a)])
            if ok:
                continue
            toks = [w for w in str(a).lower().replace(",", " ").split() if len(w) >= 4]
            missing = [w for w in toks if w not in prompt.lower()]
            if not missing:
                continue
            flagged.append((t["id"], t["cat"], str(a)[:70], ", ".join(missing[:6])))
            print("| %s | %s | %s | NO | %s |" % (t["id"], t["cat"], str(a)[:70].replace("|", "/"),
                                                  ", ".join(missing[:6])))
    print()
    print("Checked %d gold ask items over %d tasks; %d items flagged as not token-covered by the prompt." % (
        checked, len(tasks), len(flagged)))
    if flagged:
        print()
        print("Next step for each flagged cell, in order of honesty: (1) show the derivation from the "
              "prompt — if it exists, the cell is fine and the flag is a false positive; (2) if no "
              "derivation exists, record it as a bank defect with the missing evidence, do not paper it "
              "over with a gate; (3) never edit a frozen bank to hide the flag — publish a new bank "
              "version with a new hash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
