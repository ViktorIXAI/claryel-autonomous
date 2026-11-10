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

**Superseded 2026-11-08 23:20 CET:** the `contour-0.0.2.56 (item P0)` row above is a
**request-shape** measurement, not a parity one — the frozen arm started at a 512-token rung,
pinned a request seed and set `enable_thinking:false`, none of which the bare arm does. A
matched-shape re-run (`PARB_SHAPE=bare PARB_LADDER=1200`) landed later the same evening:
**139/198 = 70.2 %** (see *Matched-shape contour parity* at the end of this document). The old
row, its ledger and its answer bytes stay published unchanged; the matched row supersedes it.

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

## Matched-shape contour parity (item P0 re-run, 2026-11-08 23:06 CET) — supersedes the escalation-shape row

**Why this row exists.** The parity rule on this line is that a contour row is admissible only
when its *request shape* equals the bare arm's: first token rung = 1200, the serve's default
thinking state, temperature 0.7, same seed policy. The superseded row started at a 512-token rung,
pinned an sp1 request seed and set `enable_thinking:false` — three differences the bare row never
had. Measured on this endpoint with one identical prompt: with the thinking kwargs omitted the
chain of thought streams in `delta.reasoning_content` (144 chars of visible content, 126 completion
tokens), while `enable_thinking:false` moves the whole chain into `delta.content` (1108 chars, 372
tokens). That is the mechanism behind the truncation census above, and it is a call-parameter
effect, not a contour effect. The re-run used the frozen stamp `0.0.2.56` with the switch
`PARB_SHAPE=bare PARB_LADDER=1200` (pinned by `harness/gate_shape_parity_test.py`; it registers no
contour feature — the hard line stays frozen at `0.0.2.56`), workspace
`pub-gpqa-diamond-contour-matched`, bank sha16 `1b30f3cc51204d03` (identical to the superseded
leg), harness git `06def0b`, checker contract `pub-checkers-v2`, same 198 ids in file order.

| measure | escalation shape (superseded) | **matched shape (this row)** | bare arm |
|---|---|---|---|
| strict | 91/198 = 46.0 % | **139/198 = 70.2 %** | 127/198 = 64.1 % |
| first rung / ladder | 512→1200 | 1200, single rung | 1200 |
| request seed | sp1 pinned | none (bare policy) | none |
| thinking | `enable_thinking:false`, `reasoning_effort:none` | serve default | serve default |
| endpoint requests | 386 (198 + 188 escalations) | **198 (0 ladder steps)** | 198 |
| truncated at the ceiling | 122 (62 %), 98 of them scored as losses | **11 (5.6 %), 10 scored as losses** | engine finish not recorded; 16 rows sit at `ctok=1200` |
| contour/repair events, answer edits | 0 edits (`gate:fields_ok` 7) | **0 edits (`gate:fields_ok` 7)** | n/a |
| mean visible answer chars | 3198 | **407** | 464 |
| mean completion tokens (accepted calls) | 1030 | **789** | 802 |
| prompt / completion tokens | 48,594 / 203,882 (+ ~100 k discarded drafts) | **56,514 / 156,136** | — |
| engine time / leg wall | 1367.2 s / 2187 s | **1585.9 s / 1594 s** | 1785 s |
| GPU energy | not sampled (sampler wiring bug) | **56.85 Wh** (629 samples, mean 128.4 W, busy fraction 0.89) | 64.21 Wh |

### Paired sign tests (matched 198)

| pair | W/L | diff | p |
|---|---|---|---|
| bare vs contour (matched shape) | 16W / 28L | +6.1 pp for the contour leg | 0.096 |
| contour (matched) vs contour (escalation shape) | 63W / 15L | **+24.2 pp** | < 1e-6 |
| bare vs contour (escalation shape), published earlier | 51W / 15L | −18.2 pp | 1.0e-5 |

Discordant ids, bare-vs-matched (44 of 198, i.e. 22 % of cells flip between two independent
temperature-0.7 draws on this set): bare wins
`gpqa-003, 025, 031, 041, 052, 084, 087, 106, 115, 124, 128, 134, 141, 145, 154, 172`; matched
contour wins `gpqa-011, 015, 018, 021, 033, 040, 049, 058, 060, 069, 083, 089, 096, 102, 104, 110,
122, 125, 130, 135, 136, 139, 140, 163, 174, 184, 188, 189`.

### Verdict on this row

* With the shape matched, the frozen contour runtime is **statistically indistinguishable from the
  bare brain** on expert MCQ: 70.2 % vs 64.1 %, 44 discordant cells of 198, p = 0.096. Do not
  quote the +6.1 pp as a contour gain — 22 % cell discordance at temperature 0.7 is the
  resolution of this instrument on this set, and the contour edit census is again zero.
* The published −18.2 pp was a **request-shape artifact**: same stamp, same bank bytes, same ids,
  24.2 pp apart. The escalation ladder, not the contour, did the damage.
* The remaining harness-visible cost on this set is the **1200-token ceiling**, not the harness:
  11 rows still ran out of room and 10 of them scored as losses.
* Cost side, matched shape: one request per task (0 ladder steps), 56.85 Wh for 198 tasks
  (0.287 Wh/task) against the bare arm's 64.21 Wh (0.324 Wh/task) — the harness is no more
  expensive than bare once the token budget is right, because it stops re-drafting.

### Caveats on this row

1. Matched shape drops the pinned request seed (the bare arm sends none), so the leg is
   shape-reproducible, not bit-reproducible; the plan still carries the sp1 `gseed` per cell for
   identity, and every row stores `gen.request_shape`.
2. Single draw per arm. The 6.1 pp sits inside the ±6 pp resolution of a 198-task MCQ set at
   temperature 0.7; only the 24.2 pp shape effect clears that floor.
3. Both matched legs ran back-to-back on the endpoint after the 20:36 CET restart, at comparable
   load (the grok cloud leg does not touch the endpoint), so the two matched rows are at least
   mutually comparable.

## Answer bytes for the GPQA bare and codex arms are now published (2026-11-10 02:40 CET)

The GPQA rows in `PUB-DIGEST.md` carried answer bytes for both contour legs but not for the bare
(127/198 = 64.1 %) or codex (192/198 = 97.0 %) arms. Shipped now:
`arms/gpqa-diamond-basalt-answers.jsonl` (198 rows, `4126971be625719b`) and
`arms/gpqa-diamond-codex-answers.jsonl` (198, `2b8f5ca4b7ffd8de`). Re-score from the shipped copies
under `pub-checkers-v2` (self-test 22/22, zero model calls): 127/198 and 192/198, exactly the
published numbers. Scrub masked nothing; zero path/IP/key hits. The grok leg on this set is a
**partial** (139/198, owner quota window until 2026-11-12), so its bytes are deliberately not
published and no percent exists for it.
