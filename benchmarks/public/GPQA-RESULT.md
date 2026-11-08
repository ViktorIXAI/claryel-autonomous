# GPQA-Diamond (198 tasks) — four-arm result, first unsaturated set on the line

Date: 2026-11-08. Pinned task file `benchmarks/public/gpqa-diamond.tasks.jsonl`, tasks sha16
`af73cc064d4d8529` (source: Hugging Face `fingertap/GPQA-Diamond`, a mirror of
`Idavidrein/gpqa` used because the upstream card is agreement-gated; see `MANIFEST.json`).
Checker contract in force: `pub-checkers-v2` (`scripts/pub_bench_score.py`, self-test green,
`letter` checker). GPQA Diamond is expert-level science MCQ; the ladder notes noise ±3 pp, and
the `gsm8k`/ARC docs on this line show saturated sets cannot separate these brains. **This set
can** — and it does.

## Arms (matched set = the whole 198-task file)

| arm | model / transport | tasks | strict | wall time | call parameters |
|---|---|---|---|---|---|
| brain-basalt | `qwen3.8-flash-next-iq3_s-basalt`, IQ3_S on a 24 GB-class GPU, no contour | 198/198 | **127/198 = 64.1 %** | 1785 s (9.0 s/task), one draw per task | temp 0.7, max_tokens 1200, single seed pass |
| codex | `gpt-6.1-sol`, codex-cli 0.166.0, reasoning xhigh, read-only sandbox, prompt via STDIN | 198/198 | **192/198 = 97.0 %** | 3553 s (17.9 s/task) | sampling parameters not exposed by the transport |
| contour-0.0.2.56 (item P0) | the FROZEN contour runtime `0.0.2.56` on the same endpoint model, category `P`, public checkers in the validator slot, token ladder 512→1200 | 198/198 | **91/198 = 46.0 %** | 2187 s leg wall, 1367.2 s measured engine time | streamed request, `request_seed` pinned (sp1), ladder 512→1200, `enable_thinking` off — NOT the bare arm's request shape; see the parity section |
| grok | `grok-4.7`, hermes one-shot, toolsets off | in flight (12/198 at publish time; ~2–3 min per task on this set) | pending — no percent for a partial arm | — | — |

198/198 answered in every completed arm, 0 empty, 0 transport failures; the join dropped no ids.

## Paired sign tests (matched 198)

Exact two-sided sign test over discordant pairs only (`scripts/pub_bench_compare.py`).

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs codex | 2W / 67L | −32.8 pp | < 1e-6 |
| basalt vs contour-0.0.2.56 | 51W / 15L | +18.2 pp | 1.0e-5 |
| contour vs codex | 2W / 103L | −51.0 pp | < 1e-6 |

The basalt-vs-codex gap (67 discordant ids) is **6× the noise floor** measured for this harness
(~5 % cell flips at n≈200 means ~10 discordant flips between identical configurations): the
local 24 GB quantized brain genuinely sits ≈33 pp below `gpt-6.1-sol` on expert science, and
every honest caveat below shrinks that claim — it does not remove it.

## Contour parity (item P0) on GPQA: the harness cost finally bites

Ledger census over 198 rows (frozen stamp `0.0.2.56`, behavior 2.56):

| measure | value |
|---|---|
| contour/repair events (family grammars, fixers, answer edits) | **0** — `gate:fields_ok` fired 7×, zero answer rewrites |
| token-ladder escalations 512→1200 | **188 of 198 rows (95 %)** — 386 endpoint requests for 198 tasks |
| rows still truncated at the 1200 ceiling | **122 (62 %)** — truncated chain-of-thought usually lost its `ANSWER:` line, so the letter checker scored it a loss |
| model calls / gate fixes / gate blocks | 198 / 0 / 0 |
| prompt + generated tokens (accepted calls) | 48,594 in + 203,882 out (the discarded 512-rung drafts add roughly another 100 k generated tokens) |
| engine time inside a 2187 s wall | 1367.2 s |
| GPU energy | **not sampled for this leg** (sampler unit pointed at a wrong unit name and wrote no csv — stated, not estimated); the bare leg's 64.21 Wh over 1785 s is the nearest measured window |

The −18.2 pp paired delta is a **harness-cost measurement, not a contour-quality one**: the
mechanism census is again null (no repairs, no blocks — public category `P` routing as proven on
the other sets), but the frozen runtime's *request shape* mismatches this endpoint's verbose
thinking model: nearly every task burns its 512-rung draft, escalates, and 62 % still run out of
room at 1200. The bare arm at the same 1200 cap fits (mean 802 generated tokens, max 1200, no
`length` finishes in its transport). Discordant ids confirm the mechanism: of the 51 ids
basalt-wins/contour-loses, the contour answers end mid-reasoning on the truncated rows; the 15
ids contour wins are listed in the run archive. A contour arm that wants to compete on GPQA
needs a ladder matched to the model's natural output length — recorded as the cost side of
parity, not patched tonight (the hard line is frozen at `0.0.2.56`; no new stamps).

## Verdict

* **GPQA-Diamond resolves the brain gap the saturated sets could not:** `gpt-6.1-sol` 97.0 % vs
  the local 24 GB quantized brain 64.1 % (−32.8 pp paired, p < 1e-6). On the four saturated
  sets every brain sat inside a 1.7 pp band; here the ordering is real.
* The frozen contour runtime costs **−18.2 pp** against the same brain through ladder/ceiling
  mismatch on long-thinking outputs, with **zero** repair activity — the harness never edits an
  answer on public sets, and on GPQA its token ladder is actively the wrong shape.
* The grok leg lands late tonight (2–3 min per task through the reasoning transport); its row
  joins this table when scored — no partial percent published.

## Honest caveats

1. **Contamination.** GPQA Diamond has been public since late 2023 and is in common crawl
   neighborhoods; 97.0 % for a frontier cloud brain cannot be separated from memorisation, and
   the ladder already retired it for frontier IQ claims after one more unsaturated set
   (SimpleBench) runs. The **local** number is the clean half of the comparison: a 24 GB
   quantized model at 64.1 % is far from this set's ceiling, so contamination (if any) cannot
   explain the whole gap.
2. `gpt-6.1-sol` answers through a reasoning CLI that cannot expose temperature; the local arm
   is single-draw at 0.7. The gap is far too large for that asymmetry alone, but the exact pp
   value absorbs it.
3. **The contour arm is a different request shape**, streamed + seeded + ladder-capped, on a
   serve that was restarted at 20:36 CET under a full-swap incident before both its ARC and GPQA
   legs; the bare leg ran before it. The mechanism census rules contour *edits* out, and the
   truncation arithmetic explains the delta mechanically.
4. Cloud answer files were grepped for `bank|answer_key|expected|/home/|/Users/` before
   publication: 0 matches.
5. No energy samples for the GPQA contour leg (sampler wiring bug, listed in the table rather
   than papered over); GPU energy numbers elsewhere in this repo use the method in
   `../hard/v6-results/ENERGY-METHOD.md`.
