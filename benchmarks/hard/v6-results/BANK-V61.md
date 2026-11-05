# Bank v6.1 and the local contour arm on it

Bank v6.1 = same 77 ids, two prompt fixes (J-ex6-03 data table restored; J-ex6-06 wording
aligned with its hand-verified ref). Builder/gates: gold 77/77, semantic suite 66/0, leakage
0/77, manifest repinned (branch `1e43d2b`). bank-hard-v6.json sha256 pinned in MANIFEST.v6.

Contour arm `v61c` (0.0.2.17 stack, one rep, serve shared concurrently with the SAH 2.21 arm —
latency contention only, per-request seeds unaffected): `results-contour-v61c.jsonl`,
`scored-contour-v61.csv`.

| view | 2.15f on v6 | 2.17 on v6.1 |
|---|---|---|
| single-shot 71 strict | 46 | 49 |
| loop 6 strict | 5 | 5 |

Attribution, separated:
- **+2 mechanically attributable**: J-ex6-03 and J-ex6-06 were bank defects in v6 and fail to a
  correct reader; in v6.1 the model solves both (verified by hand: top-2 c1/c3; t4/t1/t3).
- **+1 noise**: F-ex6-01 passes this rep (seed/serve variance; single sample).
- 0 cells broken. Loop unchanged at 5/6 (consistent with the three-sample loop band 4-5/6).
- External arms (bare/ChatGPT/Grok) on v6.1 are HELD pending owner confirmation per the
  hourly-control request; v6-era external tables remain byte-identical.
