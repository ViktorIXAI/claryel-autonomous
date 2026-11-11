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
| contour-0.0.2.56 (item P0) | the FROZEN contour runtime `0.0.2.56` on the same endpoint model, category `P`, public checkers in the validator slot, token ladder 512→1200 | 198/198 | **91/198 = 46.0 %** *(superseded as a parity row by the matched-shape arm below, 139/198 = 70.2 % — a request-shape cost, not a contour effect; the number itself stays exactly as first published. Dated pointer 2026-11-10)* | 2187 s leg wall, 1367.2 s measured engine time | streamed request, `request_seed` pinned (sp1), ladder 512→1200, `enable_thinking` off — NOT the bare arm's request shape; see the parity section |
| contour-0.0.2.56, matched shape (item P0 re-run, 2026-11-08 23:06 CET; row added to this table 2026-11-10 so the in-force parity percent is quotable here) | the same frozen runtime and workspace recipe `pub-gpqa-diamond-contour-matched`, identical bank bytes, request shape equal to the bare arm's (`PARB_SHAPE=bare PARB_LADDER=1200`), checker `pub-checkers-v2`, same 198 ids | 198/198 | **139/198 = 70.2 %** | 1594 s leg wall, 1585.9 s measured engine time (8.0 s/task); no GPU energy samples for this leg (sampler wiring bug, stated in the caveats rather than papered over) | temp 0.7, first rung 1200 (single rung, 198 requests, 0 ladder steps), serve-default thinking, no request seed — the bare arm's call shape; 0 contour edits (`gate:fields_ok` 7 fired, adopted 0), 11/198 truncated at the ceiling |
| grok | `grok-4.7`, hermes one-shot CLI, toolsets off (cloud; **completed 2026-11-12 00:39 CET**, row added the same day — while the arm was partial it published no percent, so this is a new row, never an edit of an old one) | 198/198 | **174/198 = 87.9 %** | resumed leg 00:01:42→00:39:02 CET = 2240 s for the 59 missing ids (median 18.6 s, mean 38.0 s per call); the 139 ids stored on 2026-11-09 logged median 73.7 s / mean 239.9 s per call — a different transport build, wall times are not comparable across legs; no GPU energy for a cloud arm | sampling parameters not exposed by the transport; arm assembled from two legs resumed by id (198 unique ids, 198 `finish=ok`): 139 rows `v0.23.0+860.gf17db36.dirty`, 59 rows `v0.23.1+2.gb3746e3.dirty` — see "Grok arm completed 2026-11-12" at the end of this document |

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
  *(Corrected 2026-11-10: it did not land. The leg was stopped by the owner quota suspension at
  07:57 CET 2026-11-09 with 139/198 rows stored; see "Grok status on this set" at the end of this
  document.)*

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
published and no percent exists for it. *(corrected 2026-11-12: the grok arm completed at 00:39 CET
on 2026-11-12, its bytes are now shipped as `arms/gpqa-diamond-grok-answers.jsonl` and the percent is
published below — this paragraph stays as the record of what was true at 2026-11-10 02:40 CET.)*

## Grok status on this set (2026-11-10, supersedes the "lands late tonight" bullet above)

Owner quota decision 2026-11-09: no grok arm launches before **2026-11-12**. The GPQA grok leg that
was running was stopped at 07:57 CET with **139 of 198** rows stored (last id `gpqa-138`, 59 ids to
go, 139 unique ids and 139 `finish=ok` verified again at the 2026-11-10 tick); the file stays intact
and resumable by id, and **no percent is published while the arm is partial**. The grok cell in any
table on this set reads "suspended by owner quota, resumes 2026-11-12" — never a blank, never a zero,
never a transport failure. This set is first in the 12 Nov resumption queue (gpqa-diamond 59 ids,
then humaneval 44 ids, then the deferred mmlu-pro 500 and ifeval 541).
*(corrected 2026-11-12 00:39 CET: the queue ran and this set is **complete**; its table row now
carries the percent 174/198 = 87.9 %, which discharges the "suspended by owner quota" cell. The
sentence above stays as the rule that governed the window.)*

**Launch and scoring of the resumed leg, pre-registered 2026-11-11 (tick 45).** The 12 Nov queue is
started once, as a systemd user unit with an absolute launcher path
(`systemd-run --user --collect --unit=parb-pub-grok-queue bash <LOCAL_PATH>/pub-bench/go_grok_queue_20261112.sh`),
so the chain survives session end and the nightly gateway restart; liveness is read from row counts,
not unit state. This set is leg 1 (**59** ids, measured-band ETA 3.1-5.3 h). When it completes it is
scored by `pub-checkers-v2` (`letter`) over the **198** pinned ids, and the row names the transport
boundary: the 139 stored rows carry `v0.23.0+860.gf17db36.dirty`, the resumed rows carry whatever the
CLI reports at resume time (`v0.23.1+2.gb3746e3.dirty` as measured 2026-11-11 11:45 CET, after the
12 Nov 03:00 self-update). If the leg is still incomplete at the end of 2026-11-12 it stays unscored
and continues the next day by id — that is the expected shape of a 1 144-call chain, not a failure.

## Grok arm completed 2026-11-12 (00:39 CET): the fourth arm lands and the local-vs-cloud gap is bracketed

The 12 Nov owner-quota window opened at 00:00 CET. The Grok queue was started **once** as a systemd
user unit (`parb-pub-grok-queue`, absolute launcher path, `flock -n` double-spend lock,
`PUB_CLOUD_TIMEOUT=2400`) in the pinned order gpqa-diamond → humaneval → mmlu-pro → ifeval. Before
the first call the launcher ran the blank purge (every arm file printed `nothing parked`) and then
the deciding gate `scripts/pub_grok_resume_check.py` (22 checks, **RESUME GATE: READY**, resume set
`gpqa-139..gpqa-197` = 59 ids).

**Leg 1 (this set): 00:01:42 → 00:39:02 CET, wall 2240 s, 59 calls, `bad=0`** — no parked blank, no
transport failure. The two pre-existing zero-credit quarantines
(`pub-grok.jsonl.bad-timeout.bak` 46 rows / 38 ok, `pub-grok.jsonl.suspended-window-20261111.bak`
4 rows) were not touched and keep zero credit.

### Arm identity after the resume (mechanical, not hand-read)

`scripts/pub_grok_resume_check.py` in OPEN-window mode (inside the window the pin is a floor, not a
snapshot): **198 rows / 198 unique ids / 198 `finish=ok` / 0 empty answers**, SHA-256/16
`c479109822f388a5`, first id `gpqa-000`, last id `gpqa-197`. This is the first complete grok arm on a
set this line calls unsaturated.

### Percent and shipped bytes

Checker `pub-checkers-v2` (`letter`), self-test 22/22 green before the row was written, all 198 pinned
ids, 0 ids dropped: **174/198 = 87.9 %** — one digest row (`grok-4.7`, tasks `198 /
af73cc064d4d8529`). Answer bytes shipped: `arms/gpqa-diamond-grok-answers.jsonl`, 198 lines,
SHA-256/16 `c479109822f388a5`, `bytes_identical_to_runner_output=True` (the scrub masked nothing);
the privacy grep (`bank|answer_key|expected_|/home/|/Users/|<LAN prefix>|api_key|ssh -i|Authorization`)
over the answer fields returns **0 hits**. Re-scoring the **shipped** copy under the same contract
with zero model calls reproduces 174/198 exactly, so the row is re-checkable off this machine.

### Four arms on this set, in force (matched 198; every arm answered every id)

| arm | strict |
|---|---|
| basalt, local, no contour | 127/198 = 64.1 % |
| contour 0.0.2.56, matched shape | 139/198 = 70.2 % |
| grok-4.7, cloud | 174/198 = 87.9 % |
| codex `gpt-6.1-sol`, cloud | 192/198 = 97.0 % |

New exact sign tests (`scripts/pub_bench_compare.py`, two-sided over discordant pairs only):

| pair | W/L | diff | p |
|---|---|---|---|
| basalt vs grok | 6W / 53L | −23.7 pp | 1.75e-10 |
| contour-matched vs grok | 8W / 43L | −17.7 pp | 6.9e-7 |
| codex vs grok | 20W / 2L | +9.1 pp | 1.21e-4 |

Discordant ids, the rarer direction listed in full:

* basalt-only over grok (6): `gpqa-009, gpqa-087, gpqa-090, gpqa-099, gpqa-106, gpqa-170`;
* contour-only over grok (8): `gpqa-009, gpqa-011, gpqa-018, gpqa-060, gpqa-090, gpqa-099, gpqa-135, gpqa-170`;
* grok-only over codex (2): `gpqa-027, gpqa-072` — the **same two ids** on which the local arms alone
  beat codex everywhere on this set (they are basalt's only 2 wins against codex, and 2 of contour's 3).
  Two cells, so it is an observation, not a claim: three arms agree there and codex does not, which is
  a reason to read codex's 97.0 % as one draw like every other arm rather than as a ceiling.

Ladder verdict for this set: codex (97.0) > grok (87.9) > local contour (70.2) > local bare (64.1).
The frozen contour's +6.1 pp over bare stays inside the ~6 pp resolution floor of a 198-task MCQ at
temperature 0.7 (16W/28L, p=0.096) and is **not** claimed; the cloud-vs-local gaps (17.7–32.8 pp,
43–67 discordant cells) clear that floor by a wide margin.

### Cost / transport boundary (pre-registered at tick 45, reported now)

Per-row `seconds`, split by the CLI build each row stores:

| build (rows) | median | mean | max | sum |
|---|---|---|---|---|
| `v0.23.0+860.gf17db36.dirty` — 139 rows, 2026-11-09 leg | 73.7 s | 239.9 s | 2375.9 s | 33 340 s |
| `v0.23.1+2.gb3746e3.dirty` — 59 rows, 2026-11-12 leg | 18.6 s | 38.0 s | 535.7 s | 2 240 s |

The same model id answers ~4× faster per call at the median on 12 Nov than on 9 Nov, so wall time
here is a transport/endpoint property and the two legs' timings are not comparable. The score is
per-id, so the split does not bias the percent; what it buys is the honest statement that this arm
was produced by two CLI builds.

### Caveats on the grok row

1. Single draw per id; sampling parameters are not exposed by the transport (no readable seed or
   temperature), so this arm is not seed-reproducible — like the codex arm, unlike the two local ones.
2. The arm is assembled from two legs resumed by id (139 + 59 = 198: no duplicate id, no gap). The
   resume gate is what guarantees that; the two zero-credit quarantine files above are not part of it.
3. Four-option MCQ → 25 % guessing floor; on 198 tasks the same-configuration flip rate measured on
   this line (~5–6 % of cells, 44 discordant between the two local arms here) makes any delta under
   ~12 cells unresolvable. The codex-vs-grok 9.1 pp clears that but rests on 22 discordant cells.
4. Contamination is not excludable: GPQA-Diamond is public and static and is retired for frontier
   comparison in 2026 aggregators (`PUB-PLAN.md` rule 5).
5. Transport disclosure: the grok arm is a one-shot chat CLI with toolsets off (`-t ""`), so it has no
   file access — a bank/gold read is mechanically impossible for this arm, and its answers were
   grepped for bank/gold/path references (0 hits).
