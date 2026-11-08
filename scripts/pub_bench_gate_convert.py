#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Item P0 (contour parity): turn a frozen-runtime gate arm into public-benchmark inputs.

The contour row of a public set is produced by `harness/gate_run.py` at the frozen stamp
(see `scripts/pub_bench_contour_ws.py`, which stages the workspace). Its artifacts are the
hard-bank artifact shapes — a results JSONL with the answer bytes and a ledger JSONL with the
cost accounting. This script converts them into the shapes the public scorer expects, and
publishes the harness accounting beside the percent, because a harness that never fires is a
cost and that has to be visible.

Usage:
  pub_bench_gate_convert.py <RESULTS.jsonl> <LEDGER.jsonl> <out-answers.jsonl>
                            [--stats stats.json] [--stamp 0.0.2.56] [--bench gsm8k]
                            [--endpoint-model qwen3.8-flash-next-iq3_s-basalt]

The model column becomes `<endpoint model>+contour-<stamp>` so a digest row can never be read
as the bare arm. `transport_note` is what the digest call column prints for this arm: the
frozen runtime streams, pins a request seed and starts at the first ladder rung, so its call
parameters are NOT identical to the bare arm's and the difference is stated, not hidden.
"""
import argparse
import collections
import json
import sys


def load_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def event_census(ledger):
    """Every contour/fix/ladder/engine event name with its count, plus rows that had none."""
    names = collections.Counter()
    fired_rows = 0
    for r in ledger:
        evs = r.get("events") or []
        if evs:
            fired_rows += 1
        for e in evs:
            names[str(e)] += 1
    return names, fired_rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("ledger")
    ap.add_argument("out")
    ap.add_argument("--stats")
    ap.add_argument("--stamp", default="")
    ap.add_argument("--bench", default="")
    ap.add_argument("--endpoint-model", default="")
    a = ap.parse_args()

    res = load_jsonl(a.results)
    led = load_jsonl(a.ledger)
    if not res:
        sys.exit("no result rows in %s" % a.results)
    # A gate arm that reports a different contour stamp per row is two runs in one file;
    # refuse rather than average them into one published row.
    stamps = sorted({r.get("contour_version", "") for r in res})
    behaviours = sorted({r.get("contour_behavior", "") for r in res})
    if len(stamps) > 1:
        sys.exit("results mix contour stamps %s — split the arm before converting" % stamps)
    stamp = a.stamp or stamps[0]
    if a.stamp and stamps[0] != a.stamp:
        sys.exit("rows are stamped %s, asked for %s" % (stamps[0], a.stamp))
    model = a.endpoint_model or next((r.get("model") for r in res if r.get("model")), "")
    if not model:
        sys.exit("no endpoint model in rows and none passed — the row would be unattributable")

    ladder = {(r["task"], r.get("rep")): r for r in led}
    n_ans = n_empty = n_trunc = 0
    with open(a.out, "w", encoding="utf-8") as fh:
        for r in res:
            ans = r.get("answer") or ""
            if ans.strip():
                n_ans += 1
            else:
                n_empty += 1
            if r.get("truncated"):
                n_trunc += 1
            gen = r.get("gen") or {}
            rungs = ",".join(str(x) for x in gen.get("ladder", []))
            if gen.get("request_shape"):
                # 2026-11-08 parity rule: the row names its own request shape, so a matched-shape
                # leg never wears the old escalation-start label.
                note = ("frozen contour runtime %s (behavior %s): %s, ladder rungs %s, first rung %s"
                        % (stamp, behaviours[0] if behaviours else "?", gen["request_shape"],
                           rungs, gen.get("max_tokens")))
            else:
                note = ("frozen contour runtime %s (behavior %s): streamed request, "
                        "request_seed pinned (sp1), ladder rungs %s, enable_thinking off"
                        % (stamp, behaviours[0] if behaviours else "?", rungs))
            fh.write(json.dumps({
                "id": r["task"], "bench": a.bench or (r.get("cat") or ""), "arm": "contour",
                "model": "%s+contour-%s" % (model, stamp), "temp": 0.7,
                "transport": "gate_run %s" % stamp,
                "transport_note": note,
                "answer": ans,
                "seconds": (ladder.get((r["task"], r.get("rep"))) or {}).get("seconds"),
            }, ensure_ascii=False) + "\n")

    stats = {}
    if a.stats:
        names, fired = event_census(led)
        contour_names = {k: v for k, v in names.items() if k.startswith("contour:") or k.startswith("fix:")}
        stats = {
            "contour_stamp": stamp,
            "contour_behavior": behaviours[0] if behaviours else "",
            "rows": len(res),
            "answers_present": n_ans,
            "answers_empty": n_empty,
            "truncations": n_trunc,
            "rows_with_any_event": fired,
            "rows_with_contour_or_fix_event": sum(
                1 for r in led if any(str(e).startswith(("contour:", "fix:")) for e in (r.get("events") or []))),
            "gate_fire_events": dict(contour_names),
            "all_events": dict(names),
            "model_calls_total": sum(r.get("model_calls", 0) for r in led),
            "gate_fixes_total": sum(r.get("gate_fixes", 0) for r in led),
            "gate_blocks_total": sum(r.get("gate_blocks", 0) for r in led),
            "ladder_steps_total": sum(r.get("ladder_steps", 0) for r in led),
            "ptok_total": sum(r.get("ptok", 0) or 0 for r in led),
            "ctok_total": sum(r.get("ctok", 0) or 0 for r in led),
            "useful_tokens_total": sum(r.get("useful_tokens", 0) or 0 for r in led),
            "overhead_tokens_total": sum(r.get("overhead_tokens", 0) or 0 for r in led),
            "engine_seconds_total": round(sum(r.get("seconds", 0) or 0 for r in led), 1),
            "engine_stalled_rows": sum(1 for r in res if r.get("engine_stalled")),
            # the arm's own request shape, read out of the rows (never from the launcher)
            "request_shapes": sorted({str((r.get("gen") or {}).get("request_shape"))
                                      for r in res if (r.get("gen") or {}).get("request_shape")}),
            "first_rungs": sorted({int((r.get("gen") or {}).get("max_tokens"))
                                   for r in res if (r.get("gen") or {}).get("max_tokens")}),
        }
        json.dump(stats, open(a.stats, "w", encoding="utf-8"), indent=2)

    names, _fired = event_census(led)
    fired_ct = {k: v for k, v in sorted(names.items()) if k.startswith(("contour:", "fix:"))}
    print("answers %d (empty %d, truncated %d) -> %s" % (n_ans, n_empty, n_trunc, a.out))
    print("contour/fix events: %s" % json.dumps(fired_ct, ensure_ascii=False))
    if a.stats:
        print("stats -> %s" % a.stats)
    return 0


if __name__ == "__main__":
    sys.exit(main())
