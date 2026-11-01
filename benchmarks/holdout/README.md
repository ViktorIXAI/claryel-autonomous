# Held-out task bank

`bank-holdout.json` (206 tasks) was generated on 2026-11-01, **after**
contour v1.9 code was frozen — see commit chronology in `history/timeline.md`.
Generator: [`/harness/parb_bank_holdout.py`](../../harness/parb_bank_holdout.py),
seed 20261101 (the dev bank uses 20261031).

Composition:

* 200 unseen instances of the same A–K families (identical structure/levels,
  different deterministic draws);
* 6 hand-written new scenarios in existing conventions (depreciation,
  cross-currency, CSV join with duplicate keys, rule-conflict flag,
  two-forbidden-tools agent plan, new extraction text);
* ids remapped with `x`-markers (`A-xe-…`) — `scripts/sanity_data.py`
  asserts the holdout and dev id sets are **disjoint** in CI.

Run it with the frozen harness:

```bash
export PARB_BANK=$PWD/benchmarks/holdout/bank-holdout.json
export PARB_ROOT=/path/to/run
python3 harness/make_plan.py          # stages holdout bank + plan
PARB_BOX=<box> PARB_GATE_VERSION=v1.9 \
  PARB_RESULTS=results-holdout.jsonl PARB_LEDGER=gate-ledger-holdout.jsonl \
  python3 harness/gate_run.py
```

Interpretation discipline:

* a contour gain that survives on holdout instances is a harness property;
* a gain that shrinks or flips on holdout was partly dev-instance tuning;
* the independent scorer runs against this bank too
  (`PARB_BANK=… python3 analytics/second_opinion.py …`).

First mini-run (14 tasks, P2005SAH, contour v1.9): published in
`/logs/samples/holdout-p2005-mini/`. Status of full holdout series:
planned — the mini-run is the pilot, results will be interpreted without
re-touching v1.9 (a v2.0 candidate must beat both dev and holdout sets).
