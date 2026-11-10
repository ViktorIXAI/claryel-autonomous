#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired sign tests between public-benchmark arms from their VERDICT files.

`pub_bench_compare.py` scores answer files through `pub_bench_score.check`, which returns None
for execution/AST checkers (`pytest-*`, `bfcl-ast-v1`, `pub-ifeval-v1`), so an AST-scored or
execution-scored set has no paired table unless the verdict rows are joined instead. A verdict
row is `{id, ok, why}` as written by `pub_bench_bfcl.py --verdicts`,
`pub_bench_exec.py` or `pub_bench_ifeval.py`; joining those is the only comparison that cannot
re-interpret a verdict, and it is byte-cheap.

Arms are cut to the same pre-registered slice (`--limit/--offset` over the pinned task file, the
same convention as the scorers), ids missing in any arm are dropped symmetrically, and every pair
gets an exact two-sided sign test over its discordant cells with the ids printed - never a total
alone. The sign test is imported from `pub_bench_compare.py` so the line has one source for it.

usage: pub_bench_verdict_sign.py <tasks.jsonl> LABEL=VERDICTS.jsonl [...] [--limit N] [--offset N]
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_compare import sign_test                          # noqa: E402  (one sign test)


def load_verdicts(path):
    """Keep the FIRST row per id - the same rule the public scorers use, so a quarantined
    duplicate row cannot flip a paired cell differently than the published percent did.
    Key aliases on this line: a checker verdict row carries `ok`; a repair/redraw arm verdict row
    carries the keep-best flag as `strict` (plus `first_ok`, `retry_verifier_ok`, `kept`)."""
    out = {}
    for line in open(path, encoding="utf-8"):
        if not line.strip():
            continue
        r = json.loads(line)
        ok = r["ok"] if "ok" in r else r.get("strict")
        if ok is None:
            continue
        if r["id"] not in out:
            out[r["id"]] = bool(ok)
    return out


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 2
    tasks = [json.loads(l) for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    specs = [a for a in sys.argv[2:] if "=" in a]
    rest = [a for a in sys.argv[2:] if "=" not in a]
    limit, offset = None, 0
    for i, a in enumerate(rest):
        if a == "--limit":
            limit = int(rest[i + 1])
        elif a == "--offset":
            offset = int(rest[i + 1])
    ids = [t["id"] for t in tasks[offset:(offset + limit) if limit is not None else None]]
    cat = {t["id"]: t.get("category", "?") for t in tasks}
    arms = [(lbl, load_verdicts(path)) for lbl, path in (s.split("=", 1) for s in specs)]

    print("slice: offset %d limit %s -> %d ids of the pinned task file" % (offset, limit, len(ids)))
    common, drops = [], []
    for i in ids:
        if all(i in v for _, v in arms):
            common.append(i)
        else:
            drops.append(i)
    print("arms: %s" % ", ".join("%s (%d verdicts)" % (lbl, len(v)) for lbl, v in arms))
    print("common ids: %d of %d (dropped symmetrically: %d%s)"
          % (len(common), len(ids), len(drops),
             (" e.g. %s" % drops[:5]) if drops else ""))
    for lbl, v in arms:
        ok = sum(1 for i in common if v[i])
        print("  %-28s %d/%d = %.1f %%" % (lbl, ok, len(common), 100.0 * ok / max(len(common), 1)))
    for a in range(len(arms)):
        for b in range(a + 1, len(arms)):
            la, va = arms[a]
            lb, vb = arms[b]
            w = [i for i in common if va[i] and not vb[i]]
            l = [i for i in common if vb[i] and not va[i]]
            p = sign_test(len(w), len(l))
            print("pair %-24s vs %-24s  W%d/L%d p=%.3f  (delta %+.1f pp)"
                  % (la, lb, len(w), len(l), p,
                     100.0 * (len(w) - len(l)) / max(len(common), 1)))
            for i in w:
                print("    %s wins: %s [%s]" % (la, i, cat.get(i, "?")))
            for i in l:
                print("    %s wins: %s [%s]" % (lb, i, cat.get(i, "?")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
