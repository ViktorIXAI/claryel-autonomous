# Public-line contour arm artifacts (the re-scorable bytes behind the PUB digest rows)

Written by `scripts/publish_pub_arms.py`. One file-name prefix per contour arm. Infrastructure
fields (hostname, LAN address, absolute local path, key material) are masked per the repo privacy
rules; **answer text is never edited**. Re-scoring a published `*-answers.jsonl` with
`scripts/pub_bench_score.py` (contract `pub-checkers-v2`) reproduces the published percent
exactly — asserted for every arm below.

| arm file | lines | sha16 |
|---|---|---|
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
| arc-easy-contour-escalation-answers.jsonl | 300 | `e2407d5cb745a05a` |
| arc-easy-contour-escalation-bank-version.json | 6 | `055b650afd938842` |
| arc-easy-contour-escalation-ledger.jsonl | 300 | `6f4eace44fc97190` |
| arc-easy-contour-escalation-plan.json | 1 | `e1638a6a84d969f7` |
| arc-easy-contour-escalation-results.jsonl | 300 | `7c916c24b4cb3564` |
| arc-easy-contour-escalation-run-record.json | 40 | `9b30f05be12c9d29` |
| arc-easy-contour-escalation-stats.json | 22 | `fc788d183fd5cc58` |
| arc-easy-contour-escalation-ws-identity.json | 36 | `1491da4724a0ecf7` |
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
| gsm8k-contour-escalation-answers.jsonl | 300 | `3f294f62a4ee0c0a` |
| gsm8k-contour-escalation-bank-version.json | 6 | `d0f6180e96b14c44` |
| gsm8k-contour-escalation-ledger.jsonl | 300 | `b86aee72840a9cb0` |
| gsm8k-contour-escalation-plan.json | 1 | `8d98d11112bb738b` |
| gsm8k-contour-escalation-results.jsonl | 300 | `a4f9cc49b6f90b87` |
| gsm8k-contour-escalation-run-record.json | 40 | `c04c6872de8ee3d2` |
| gsm8k-contour-escalation-stats.json | 24 | `1bbfa5f23461a217` |
| gsm8k-contour-escalation-ws-identity.json | 36 | `678a8d65b6d7040c` |

Task-file pins (from `benchmarks/public/<bench>.tasks.jsonl`):

* `gpqa-diamond` 198 ids `af73cc064d4d8529`, ws bank sha16 `1b30f3cc51204d03`
* `arc-challenge` first 300 of 1172 ids `523af08216f14256`, ws bank sha16 `e56146d09263ca89`
* `arc-easy` first 300 of 2376 ids `cac604a076e8b00a`, ws bank sha16 `055b650afd938842`
* `gsm8k` first 300 of 1319 ids `7dd0080ff23b8bc3`, ws bank sha16 `d0f6180e96b14c44`

All arms: contour stamp `0.0.2.56` (behavior 2.56), checker contract `pub-checkers-v2`, endpoint
`<LAN_IP>:8080`.

`-escalation` = the original item-P0 arms (first rung 512, pinned sp1 request seed,
`enable_thinking:false`). `-matched` = the parity re-runs at the bare arm's request shape
(`PARB_SHAPE=bare PARB_LADDER=1200`, harness `06def0b` or later; a call-parameter switch that
registers no contour feature — the hard line stays frozen at `0.0.2.56`). The escalation rows are
superseded as parity measurements and kept because published bytes are immutable; the result docs
carry the dated pointers.

Verified re-score of the published copies:

```
gpqa-diamond     matched 139/198 = 70.2 %   escalation 91/198 = 46.0 %
arc-challenge    matched 291/300 = 97.0 %   escalation 283/300 = 94.3 %
arc-easy         (matched leg in flight)    escalation 290/300 = 96.7 %
gsm8k            (matched leg in flight)    escalation 290/300 = 96.7 %
```

Reproduce one row:

```
python3 scripts/pub_bench_score.py benchmarks/public/gpqa-diamond.tasks.jsonl \
       benchmarks/public/arms/gpqa-diamond-contour-matched-answers.jsonl
```
