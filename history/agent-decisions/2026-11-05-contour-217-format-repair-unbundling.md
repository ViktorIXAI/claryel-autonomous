# Decision record — contour 0.0.2.17: keyword-free format repair unbundled from CHECKER_INJECT

Date: 2026-11-05 20:49-21:10 CET. Owner directive for this shift: "Бей куда хочешь но бей,
коммить, фиксируй работай" + "С вчерашними результатами пока не сравнивай, бей по сегодняшним
проблемам, публикуй все шаги и результаты и логи". Branch `hard-v6-loopd-hermes`,
fast-forwarded into `hard-v6-p0-fix-hermes`. Worktree `~/sah-loopd`, measurement workspace
`~/parb-loopd-216`.

## What was diagnosed

On the published 0.0.2.16 full arm (`full-216/`): J was 0/7 and B 2/7 while the raw chat arms
sit at J 5-6/7 and B 6-7/7. Six cells had content 1.00 and `format_ok=False`
(`items_not_bare_ids`, `object_wrapped_in_list`). The deterministic repairs that were written
for exactly these cases in 0.0.2.15 never executed: the only three call sites of
`post_normalize_answer` were gated by `POST_NORMALIZE = CHECKER_INJECT and contour_at_least(2,0)`,
and issue #15 switched `CHECKER_INJECT` off for the official score. The 0.0.2.15 contract test
passed because it called the function directly and bypassed the pipeline gate. Ledger evidence:
zero `contour:v20_*` events in the whole 2.16 arm.

## Decision

Open the gate for the **keyword-free** repair only (`FORMAT_REPAIR = contour_at_least(2,17)`,
call sites use `post_normalize_allowed() = POST_NORMALIZE or FORMAT_REPAIR`). The G
contradiction-marker and K tax-negation normalizers stay behind `CHECKER_INJECT`: they insert
the very words the scorer looks for, which is what issue #15 forbids. Whether the H 600-char
trim (no keyword, pure length cut) should also be unbundled is an **owner decision**, logged in
`benchmarks/hard/REVIEW-INBOX.md`, not taken here.

## Measurement (paired, identical seeds, one rep, back-to-back arms)

plain strict 39/71 -> 41/71; B 2 -> 5, J 0 -> 3; repair fired 11 times
(6 `v20_j_id_norm`, 5 `v20_obj_unwrap`); all 6 targeted format-only cells recovered, none
broken; the 4 opposite-direction strict losses carry no repair event (serve resample).
Aggregate sign test 6W/4L p=0.754 — not significant on one rep; the claim published is
mechanism-level (6/6 targeted cells, zero model tokens), not a contour-beats-raw verdict.

## Guards

`harness/gate_v38_repair_pipeline_test.py` (9 checks): gate closed at 2.16/inject-off (the
bug), open at 2.17/inject-off, J and B repairs produce scorer-valid shapes, G/K injectors
stay off at 2.17, inject-ON path preserved, repair idempotent.
Standing gates re-run after the change: `gold_selftest_v6` 77/77, `leakage_scan_v6` 0 leaks,
`verify_manifest --v6` PASS, `semantic_suite_v6` 66 controls / 0 violations, `docs_policy --push`
PASS, current-diff gitleaks clean (history scan: 9 old hits, current tree clean).

## Caveat recorded for the suite

`semantic_suite_v6` failed once ("orphan containers left: e-sbx-…") while a gate arm was
running at the same time: its orphan-container control counts the arm's own E-battery
sandbox. Re-run on an idle host: 66 controls, 0 violations, 0 containers left. The suite must
run with the runner idle.

## Next target

J content: 3/7 vs 5-6/7 for raw arms; all remaining J losses are `id_set_mismatch` /
`order_partial` (B: 2 x `fields_mismatch`), i.e. rule selection, not format.
