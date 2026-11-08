# Public-line arm artifacts (re-scorable bytes behind every PUB digest row)

Written by `scripts/publish_pub_arms.py`. One prefix per contour arm; the infrastructure fields
(hostname, LAN address, absolute local path, key material) are masked per the repo privacy rules,
and the answer text is **never** edited — re-scoring a published `*-answers.jsonl` with
`scripts/pub_bench_score.py` (contract `pub-checkers-v2`) reproduces the digest percent exactly,
which is asserted for each file below.

| arm | file | lines | sha16 |
|---|---|---|---|
| arc-challenge-contour-escalation-answers.jsonl | 300 | `90bf60cc70007866` |
| arc-challenge-contour-escalation-bank-version.json | 6 | `845cdf76a755ec50` |
| arc-challenge-contour-escalation-ledger.jsonl | 300 | `0e4eae97bdb7ebf5` |
| arc-challenge-contour-escalation-plan.json | 1 | `2025e06b43582822` |
| arc-challenge-contour-escalation-results.jsonl | 300 | `1b205f13fbb9d213` |
| arc-challenge-contour-escalation-run-record.json | 40 | `cde6c60ea9b13b4c` |
| arc-challenge-contour-escalation-stats.json | 24 | `86cf050bdbc3052c` |
| arc-challenge-contour-escalation-ws-identity.json | 36 | `7ec628b3206b6468` |
| arc-challenge-contour-matched-answers.jsonl | 300 | `9be65d62b734a93c` |
| arc-challenge-contour-matched-bank-version.json | 6 | `8fdd7e82405d3475` |
| arc-challenge-contour-matched-ledger.jsonl | 300 | `14bff207380e4735` |
| arc-challenge-contour-matched-plan.json | 1 | `2025e06b43582822` |
| arc-challenge-contour-matched-results.jsonl | 300 | `e8a19fe4c79a8420` |
| arc-challenge-contour-matched-run-record.json | 45 | `49a67ae9735a35f7` |
| arc-challenge-contour-matched-stats.json | 28 | `39fca8a2b2762039` |
| arc-challenge-contour-matched-ws-identity.json | 41 | `bcd8a97b65c83447` |
| gpqa-diamond-contour-escalation-answers.jsonl | 198 | `b28ab5ac6f562ee8` |
| gpqa-diamond-contour-escalation-bank-version.json | 6 | `330a74aeec4a8240` |
| gpqa-diamond-contour-escalation-ledger.jsonl | 198 | `f8b46c25e51ff0a7` |
| gpqa-diamond-contour-escalation-plan.json | 1 | `3d91a5f23ee84222` |
| gpqa-diamond-contour-escalation-results.jsonl | 198 | `d92f4e27dd452a5f` |
| gpqa-diamond-contour-escalation-run-record.json | 40 | `d8d71a0c7740f895` |
| gpqa-diamond-contour-escalation-stats.json | 25 | `d8ed89a24812f8c2` |
| gpqa-diamond-contour-escalation-ws-identity.json | 36 | `1c5913d87ad68258` |
| gpqa-diamond-contour-matched-answers.jsonl | 198 | `07132245ccef4880` |
| gpqa-diamond-contour-matched-bank-version.json | 6 | `7e98b4233a3c32cc` |
| gpqa-diamond-contour-matched-ledger.jsonl | 198 | `dfeac925340b8cdf` |
| gpqa-diamond-contour-matched-plan.json | 1 | `3d91a5f23ee84222` |
| gpqa-diamond-contour-matched-results.jsonl | 198 | `8e48383694510f79` |
| gpqa-diamond-contour-matched-run-record.json | 45 | `9c928083666372b3` |
| gpqa-diamond-contour-matched-stats.json | 30 | `833b21dcb4e1fdaa` |
| gpqa-diamond-contour-matched-ws-identity.json | 41 | `4a9b5fc0d4126116` |

Pins these arms share:

* GPQA-Diamond: tasks sha16 `af73cc064d4d8529` (198 ids), ws bank sha16 `1b30f3cc51204d03`,
  contour stamp `0.0.2.56` (behavior 2.56), checker contract `pub-checkers-v2`.
* ARC-Challenge: tasks sha16 `523af08216f14256` (first 300 ids in file order), ws bank sha16
  `e56146d09263ca89`, same stamp and contract.

The `-escalation` legs are the original item-P0 arms (first rung 512, sp1 request seed,
`enable_thinking:false`); the `-matched` legs are their parity re-runs at the bare arm's request
shape (`PARB_SHAPE=bare PARB_LADDER=1200`, harness git `06def0b`). The escalation rows are
superseded as parity measurements and kept because their bytes are immutable published data —
see `GPQA-RESULT.md` and `ARC-CHALLENGE-RESULT.md`.

Reproduce one row:

```
python3 scripts/pub_bench_score.py benchmarks/public/gpqa-diamond.tasks.jsonl \
       benchmarks/public/arms/gpqa-diamond-contour-matched-answers.jsonl
```
