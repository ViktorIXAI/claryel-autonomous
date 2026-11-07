# Gold-derivability census chain (versioned scanners)

Every census number in this repo is now attributable to a scanner version, a bank
file, and the scorer contract whose matching rules it mirrors. Before this, census
counts were quoted from a "sha-less" tool and could not be compared across
releases — exactly the failure mode the measurement-stack doctrine forbids.

## Scanners

| scanner | file | bytes sha16 | categories | status |
|---|---|---|---|---|
| audit-v1 | `scripts/bank_derivability_audit.py` | `0e5e4df63718ee1d` | A, B, K | FROZEN — the only scanner of the published chain; byte-unchanged forever |
| audit-v2 | `scripts/bank_derivability_audit_v2.py` | `ac4516f263e3e8f2` | A, B, K + H (opt-in `PARB_AUDIT_CATS=ABKH`) | current |

audit-v2 changes exactly two things (contract-pinned by
`harness/audit_v2_scanner_test.py`, 27 checks, enrolled in CI):
1. identity — every run prints `SCAN-ID scanner=… self-sha16=… bank-sha16=…
   contract=… contract-sha16=…`, so a census line names its full stack;
2. H ask-atom coverage — for every `ref.unknown` and every `ref.ask` item it applies
   the frozen contract's OWN matcher (`_token_cover`: some token `[а-яa-z0-9]{4,}`
   whose `_stem_tok` appears as a substring). An atom is reportable when no token
   stem is copyable from the prompt: `h_absent` (the gold demands naming atoms the
   prompt never shows — the published H-ex6-01 class) or `h_script` (reachable only
   by crossing Latin/Cyrillic scripts). With `cats=ABK` audit-v2 reproduces
   audit-v1's hit set EXACTLY on every published bank (guarded in the test).

All census runs below scored against scorer contract v6.2 (`c8c0c7dd114dfc32`,
modules `parb_check_v6.py 89437d8cfe1fc6c8` / `parb_loop.py f5f5b78ab46a0f0c` /
`e_sandbox.py 424c04126e9b6c1e`). Census = CANDIDATES, not verdicts: a candidate
becomes a published defect only after answer-byte evidence from arms.

## The chain

Counts = candidate atoms (tasks). audit-v1 ABK recomputed 2026-11-07 reproduces
the published chain exactly — rescore integrity of the audit tooling itself.

| bank (sha16) | audit-v1 ABK | audit-v2 ABK | audit-v2 H | total v2 |
|---|---|---|---|---|
| v6.1 `9ec86dfca4a6f85f` | 40 (17 tasks) * | 40 (identical set) | 1 | 41 (18 tasks) |
| v6.2 `3c866ea7daae611c` | 39 (17) — published chain value | 39 (identical set) | 1 | 40 (18) |
| v6.3 `73f7a04d57473545` | 38 (17) — published chain value | 38 (identical set) | 1 | 39 (18) |
| v6.4 `85a0cd0dd6fa1fab` | 37 (16) — published chain value | 37 (identical set) | 1 | 38 (17) |
| v6.5 `cd29d6ac94dc3267` | 37 (16) | 37 (identical set) | **0** | 37 (16) |
| v6.6 `5c86252b2ef2f422` (WORKING) | 37 (16) | 37 (identical set) | **0** | 37 (16) |

\* v6.1 was never in the published chain; recorded now for completeness.
Never quote a total across scanner versions — the ABK column is the comparable one.

## What the H coverage shows

The single H candidate on v6.1–v6.4 is identical in all four banks:

```
H-ex6-01   ask[0]   h_absent   аудит-лог operations :: no token-stem copyable (аудит,operations)
```

That is the H-ex6-01 defect class from bank-probe-65 made mechanical: the gold ask
demands an answer component containing a stem of `аудит` or `operations`; before the
v6.5 naming fix the prompt showed neither, so `_token_cover` zeroed every faithful
Russian paraphrase. The v6.5 scenario sentence ("есть только аудит-лог operations")
makes the stem literally copyable — v6.5 and v6.6 census H=0. audit-v2 would have
caught this defect at bank-build time, with no arms spent.

Consequence for the queued H-family coverage extension (the inviting claims
fragment still present in H-ex6-00/02/03/04): the atom census finds NO unnameable
ask atoms there — the extension's defect class (claims-field spec vs `claims:[]`
contract) is a spec-vs-contract contradiction, not a derivability gap, so audit
census alone cannot license a v6.7 bank change. The extension stays queued behind
answer-byte evidence from arms (the pair-243/fairness-probe rule), unchanged.

## Artifacts

Verbatim audit-v2 census outputs (one file per bank, identity headers included):
`v6-results/audit-census-v2/*.out`. Reproduce:
`PARB_AUDIT_CATS=ABKH python3 scripts/bank_derivability_audit_v2.py benchmarks/hard/<bank>.json`.
