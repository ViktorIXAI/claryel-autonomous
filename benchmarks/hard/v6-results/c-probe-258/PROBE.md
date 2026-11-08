# C-probe-258: C-ex6-01 contour candidate probed OFF-ENDPOINT and CLOSED (negative result)

Date: 2026-11-08. Follow-up to MAP-258, which queued `contour 2.58 candidate / pair-259 = C-ex6-01
B-inclusion gating`. Nothing was launched and no contour stamp was burned: the candidate family was
probed with single diagnostic calls on the idle endpoint (P2005 Basalt, GPU 0%, no foreign
`gate_run`) and refuted before reserving an arm slot.

## 1. The "injection" framing was refuted by bytes

MAP-258's promotion note says the coverage step "injects a letter the verdicts reject". It does not:

- map-258 ledger rows for C-ex6-01 (all three legs, bank v6.8 `7a9527bf2e4ebbff`, stamp `0.0.2.56`)
  carry `gate:coverage_ok` — never `coverage_gap`; `picked == self_declared` held on every leg.
- A byte-level replay of the exact `coverage_gate` request (same sp1 gseeds as reps 25/26/27, same
  call body: temperature 0.7, first ladder rung max_tokens 512, stream, thinking disabled) shows the
  MODEL ITSELF writing `B=ПОДХОД` then `ФИНАЛ: B, C, F` on the failing draws. The contour faithfully
  reproduces the model's own verdicts; the scaffold's effect is that forced per-option enumeration
  makes the model agree with the reversed safety-sounding option B more often than the free-form
  answer does (free-form with contour OFF: `C,F` unanimously — MAP-258 fairness probe).

## 2. Three prompt-layer repair families, probed on all 8 v6.8 C tasks x seeds 25/26/27

| family (all zero extra model calls, reference never read) | idea | outcome |
|---|---|---|
| COMMIT-FIRST | make the model write its own `ОТВЕТ:` line first, keep it when it disagrees with verdicts | catastrophic: 6/24; the same-context enumeration contaminates the pre-committed line, it over-includes (ABCF/ACF/ABC...) — the "unanimous C,F" property belongs to the RAW no-scaffold prompt, not to a commitment emitted alongside the verdict ask |
| V1 agreeableness guard | add one generic sentence: a restrictive-sounding formulation is not itself evidence of correctness | pass 1: 18/24 (target cell 2/3, but new losses); pass 2: 15/24, target 0/3 — at or below the baseline band, collateral on `C-ex6-02` (whose gold is all-correct: the guard removes correct letters) |
| V2 in-call recheck | second commitment `ФИНАЛ2` in the same call | 16/24 both passes, target 1/3 — no gain, `C-ex6-00` collateral |

Baseline for the same rows (old verdict protocol, verdict set == gold set): map-258 arms 22/24;
probe sessions 18/24 and 20/24. **All three candidates land at or below the baseline band.**

## 3. Measurement-resolution finding (feeds the evaluation-system backlog)

Same seeds, same body, same idle endpoint, different session: the C pool drifts at least two cells
per pass (baseline `C-ex6-02` 3/3 in arm legs, 0/3 in a probe session; V1 total 18/24 then 15/24).
A single-draw C-cell probe cannot resolve a +/-1-cell mechanism effect; C-class probes need >=3
draws per cell before any wording family is promoted to a pair. Seeds 25/26/27 are burned for
C-ask-wording hypotheses (used to generate these designs); any future C pair must use fresh seeds.

## 4. Decision

- `contour 2.58 / pair-259` C-ex6-01 candidate: **CLOSED UNBUILT** at the prompt-layer family —
  refuted at probe stage, exactly what pre-arm probing is for. No stamp registered, no pair
  launched, no percent row (no arm ran).
- The remaining selection-family route (best-of-N over verdicts) is rejected by construction: any
  aggregation bias (e.g. prefer the smaller set, or intersect) is wrong on the all-correct-gold task
  `C-ex6-02` — visible in the same tables.
- With the loop pool 6/6, zero stable-fail cells and the only repeat-fail cell closed as above, the
  adopted line 0.0.2.56 is at the BANK CEILING on v6.8: seven seed-unstable cells remain, all at
  the <=2/3 draw-lottery level (MAP-258 map). Next scheduled measurement work is the four-arm
  cadence when it comes due (5 contour stamps after cadence-255), not a new contour hypothesis.

## Provenance

- Endpoint: P2005 Basalt (model alias `qwen3.8-flash-next-iq3_s-basalt`), idle at launch; ws bank
  copy `361f7bdb24d6ac71` = published v6.8 `7a9527bf2e4ebbff`; scorer identity only used to compare
  letter sets against `ref.letters` (no re-scoring of published arms).
- Seeds: sp1 (`gseed = sha256(task|rep)[:8] % 999983`), reps 25/26/27; every stored row carries its
  gseed, prompt sha16, raw text, parsed verdict set / final set / committed set.
- Row files: `rows-commitfirst-258.jsonl` (24 rows, COMMIT-FIRST family, byte-captured pass),
  `rows-askword-v1v2-258.jsonl` (48 rows, V1/V2, byte-captured pass). Earlier flag-only passes are
  superseded by these byte-captured runs; per-pass totals quoted above name their pass.
- Probe scripts (untracked local, not published: they resolve the endpoint from the box's own
  profile file): sha256 `4a5f465c8e7ebdb6ad386be6b3cb47d49fedb35d4d6a81ffa7a11b248533b2f9`
  (commit-first) and `26ee73863b301ec6ad340c9baf605165ecb74a29dd55f2b2b6578f98903b166f` (V1/V2).
