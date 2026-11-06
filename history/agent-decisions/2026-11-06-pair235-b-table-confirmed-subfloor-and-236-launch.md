# Decision: pair-235 — the B table repair is confirmed on its cell; the stamp still misses the noise floor (2026-11-06)

## Context

pair-235 (arms `h29r*` vs `h35r*`, P2005/Basalt, bank v6.1 `f4553aab304f60d7`, three matched seeds,
77/77 rows per arm) measured contour `0.0.2.35` — recomputing a markdown-table `*_total` from the
prompt's own table, footnote included — against the adopted `0.0.2.29`. It was pre-registered (in
`PAIR-234-V61.md`, before any `h*` row) as a cell-level claim only: exactly one cell (`B-ex6-06`) flips
in all three candidate seeds carrying `contour:v235_b_table_total`, expected mean +1.0, below the
~2-cell floor by construction; off-target movement refutes the clean pattern and freezes the stamp.

## Evidence

- Mechanism: exactly 3 fires, all on `B-ex6-06`, one per candidate seed; `B-ex6-06` 0/3 -> 3/3 strict;
  identical `model_calls=2` / `ptok=260` on that cell in both arms (zero-token repair as designed).
- Headline: 61.3 -> 63.3 (+2.0) — exactly at the measured ~2-cell resolution floor; pooled sign test
  9W/3L p=0.146; four off-target cells (A-ex6-00, A-ex6-08, F-ex6-00, J-ex6-06) flipped with no 2.35
  event: +1.0 event-attributed, +1.0 resampling.
- Rescore: 30 cell-arm joins against sibling answer bytes, 0 mismatches — the flip table is real.
- Energy: control seed-0/1 windows inflated by endpoint warm-up (816/605 s at the same call count);
  the matched-length seed-2 pair is 7.13 vs 8.77 Wh. No resource limit tight.

## Decision

**Not adopted.** `B_TABLE_AGGREGATE` is frozen to `CONTOUR_REVISION == (2, 35)` (same freeze mechanism
as 2.30–2.34), registered in `UNADOPTED_FEATURES` and pinned in the `gate_v49_feature_adoption_test.py`
flag matrix, so stamp 2.36 and later inherit none of it. The adopted line stays `0.0.2.29`.

The freeze is a LINE decision, not a mechanism verdict, and the report says both plainly: this is the
first stamp in the series whose mechanism evidence is complete (fires only on target, event on every
converted row, converts a 9-seed chronic cell deterministically). Re-adoption is a one-flag owner call.

## Next: 0.0.2.36 — group-4 lottery selection, pre-registered before launch

The newest live class in `UNSTABLE-CELLS-V61.md` is group 4 (component omission: `unknown_missing` /
`requires_missing:<field>` on H, `avoid` on F), reconfirmed by pair-235's `F-ex6-00` failure seeds
(note `avoid` in both arms). The class is a seed lottery, so the fix is the proven SELECTION recipe,
not a new nudge: extend 2.9 best-of-2 to the H notes (prefix-matching the parameterized note) and give
F one strict-best re-sample (seed+5501). Contract: `harness/gate_v53_g4_lottery_test.py` (38 checks)
including run_one call-site proof at 2.36 AND no-op proof at 2.29. Enrolled in the CI contract list in
the same commit. Launch: smoke `smk36*` then `run_pair236.sh` as `parb-pair236.service` (arms `i29r*`
vs `i36r*`). Pre-registered decision rule: attribution claim only; zero fires or any event-less flip
attributed to the mechanism freezes 2.36 like 2.33/2.34.
