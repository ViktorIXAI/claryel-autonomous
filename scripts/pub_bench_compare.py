#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Paired comparison of public-benchmark arms on the task ids both arms actually answered.

Every percent on this line is published with the matched-set size and an exact two-sided sign
test, because an unpaired average over different id sets is how benchmark claims get inflated.
Arms are scored through the same checkers as pub_bench_score.py; ids missing in either arm are
dropped symmetrically and the drop count is printed.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pub_bench_score import check                                    # noqa: E402


def sign_test(w, l):
    n = w + l
    if n == 0:
        return 1.0
    k = min(w, l)
    return min(1.0, sum(math.comb(n, i) for i in range(0, k + 1)) * 2 / 2 ** n)


def load_answers(path):
    out = {}
    for line in open(path, encoding="utf-8"):
        d = json.loads(line)
        if d["id"] not in out:
            out[d["id"]] = d
    return out


def main():
    if len(sys.argv) < 4:
        print(__doc__ + "\nusage: pub_bench_compare.py <tasks.jsonl> arm=path.jsonl arm=path.jsonl "
                        "[--limit N] [--offset N]")
        return 2
    tasks_f = sys.argv[1]
    specs = [a for a in sys.argv[2:] if "=" in a]
    arms = [a.split("=", 1) for a in specs]
    limit, offset, rest = None, 0, [a for a in sys.argv[2:] if "=" not in a]
    for i, a in enumerate(rest):
        if a == "--limit":
            limit = int(rest[i + 1])
        elif a == "--offset":
            offset = int(rest[i + 1])
    all_tasks = [json.loads(l) for l in open(tasks_f, encoding="utf-8") if l.strip()]
    window = all_tasks[offset:offset + limit] if limit else all_tasks[offset:]
    ids = [t["id"] for t in window]
    by_id = {t["id"]: t for t in window}
    ans = {name: load_answers(path) for name, path in arms}

    common = [i for i in ids if all(i in a and (a[i].get("answer") or "").strip() for a in ans.values())]
    dropped = len(ids) - len(common)
    print("matched ids: %d of %d (dropped %d unanswered in some arm)" % (len(common), len(ids), dropped))
    if len(common) < 20:
        print("too few matched ids to publish a comparison")
        return 1
    score = {}
    for name in ans:
        score[name] = {i: bool(check(by_id[i]["checker"], by_id[i]["gold"], ans[name][i]["answer"]))
                       for i in common}
        ok = sum(score[name].values())
        print("%-10s %4d/%4d = %5.1f%%" % (name, ok, len(common), 100.0 * ok / len(common)))
    names = list(ans)
    for a in range(len(names)):
        for b in range(a + 1, len(names)):
            x, y = names[a], names[b]
            w = sum(1 for i in common if score[x][i] and not score[y][i])
            l = sum(1 for i in common if score[y][i] and not score[x][i])
            print("%s vs %s: %dW/%dL diff %+.1f pp p=%.6f"
                  % (x, y, w, l, 100.0 * (w - l) / len(common), sign_test(w, l)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
