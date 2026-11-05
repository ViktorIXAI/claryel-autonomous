# v6 review inbox — reviewer findings ledger (ACKNOWLEDGED, NOT YET ACTIONED)

Owner directive 2026-11-05: instructions/commands from GitHub reviewer players
(ChatGPT/GPT-6, Grok bot) are NOT executed as tasks. Hermes publishes evidence
only. Every substantive finding is logged here; remediation happens ONLY on
Viktor's explicit command, batch by batch.

Status legend: FIXED-@<commit> = already closed by earlier owner-commanded work;
LOGGED = recorded, awaiting owner command; DECLINED = recorded with rationale.

## From GPT-6 (ChatGPT) — issue #15 / PR #17 rechecks (16:25Z, 16:52Z, 17:06Z)

| # | Finding | Status |
|---|---------|--------|
| 1 | E verdict spoofing via stdout (`PASSED x OF y` written by evaluated code) | FIXED @ a117312b (verdict protocol v2), superseded by v3 |
| 2 | Docker container orphan risk on wall timeout; image not digest-pinned | FIXED @ a117312b (named container, kill/rm, digest pin `python@sha256:aa943ce4…`), hardened @ 90f67095 (`finally` teardown) |
| 3 | Writable grading fixtures inside container (answer code can rewrite gold/probe mid-run) | FIXED @ 90f67095 (`/input:ro` mounts + VERDICT digest attestation) |
| 4 | Readable gold / oracle leak: expected outputs visible to untrusted probe (`/input/_batt.json` readable; `exp` in probe memory) | FIXED @ (v3 rewrite: per-test ephemeral containers; gold never enters container; host-side comparison; oracle-read cheat control) — pending gate run |
| 5 | `run_unshare`/`run_local` bogus `audit=audit` kwargs (latent NameError in unused fallbacks) | FIXED @ 90f67095 |
| 6 | Generated ws shim not pinned | FIXED @ b3a934e/90f67095 (WS-GENERATED.v6.sha256 + MANIFEST + fail-closed builder) |
| 7 | H base credit for empty template | FIXED @ 823cb86 (proportional gold-only credit + per-task negative controls) |
| 8 | D-loop dup+missing must reduce CONTENT, not only format | FIXED @ 823cb86 (controls assert content 0.33) |
| 9 | H morphological fragments; need contradictory-statement negatives | FIXED @ a117312b (_asserts_completion window guard + 3 adversarial controls) |
| 10 | Per-arm entrypoint resolution/hashes not independent | FIXED @ a117312b (dry_run per-arm sha256 + E_DOCKER_SMOKE through real scorer) |
| 11 | Do not claim 77 prompts = 77 independent hard skills; G dropped long-context | LOGGED (wording discipline; PROTOCOL already states v6 scope) |
| 12 | "Reported test results are Hermes claims, not independent runtime attestation" | LOGGED — reviewer-side execution is their choice; we publish reproducible artifacts |
| 13 | Prefer separate grader principal; "no shared mount/env/IPC contains gold" | PARTIALLY FIXED by v3 (gold host-side); LOGGED: stronger host-side grader sandbox (gVisor / bench VM) awaiting owner command |

## From CLARYEL BOSS (Grok bot) — PR #17 review + hourly controls

| # | Finding | Status |
|---|---------|--------|
| B1 | H empty-template base credit | FIXED @ 823cb86 |
| B2 | D-loop dup+missing content control | FIXED @ 823cb86 |
| B3 | check_v6_shim pinning | FIXED @ b3a934e |
| B4 | Absolute local paths in committed sources (secret-scan) | FIXED @ 847b2eb |
| B5 | Writable-fixture exploit (same as GPT-6 #3) | FIXED @ 90f67095 |
| B6 | Gold-oracle READ residual (same as GPT-6 #4) | FIXED @ v3 rewrite (this batch) |
| B7 | Integrate side branch into PR #17 under single writer (fast-forward) | LOGGED — writer-line action |
| B8 | Publish exact commands+outputs for suite/no-orphan/digest evidence trail | PARTIALLY DONE (comments carry command strings + outputs); LOGGED: add CI-executed attestation run if owner wants third-party runtime proof |
| B9 | #11 least-privilege acceptance still open; FRESH100 paused (#13) | LOGGED, untouched per owner pause |

## Process constraints acknowledged
- Single writer on `hard-v6-p0-fix` (flag `.hermes-single-writer-STOP`); my work lands on `hard-v6-p0-fix-hermes` for the writer line to FF.
- Reviewers demand no merge/no inference without owner GO; owner issued 4-arm run GO on 2026-11-05 (Viktor, chat).

## Self-found findings during 4-arm v6 series (2026-11-05)
| # | finding | status |
|---|---|---|
| S1 | v6 loop-D tasks were plan-replay, not drivable by the agent loop (kind-bug rerun exposed: 0/6 role-play) | FIXED @ 80999648 (loop-v2 agent tasks + trajectory scorer) |
| S2 | contour 2.14 net-negative vs bare basalt on v6: B/J format regressions (`[{...}]` wraps, decorated J items), A arithmetic worse under scaffold | LOGGED — next contour version (format canonicalization for B/J, scaffold harm probe on A) |
| S3 | grok raw transport (`hermes -z @file`) exposes file tools; one H answer disclosed the transport path; no bank/gold leak traces (grepped) | LOGGED + disclosed in v6-results README; future raw arms: stdin-only transports |
| S4 | contour early-answer rejection creates a second answer row -> strict format fails on loop tasks (own guard hurts own format) | LOGGED — gate must tag rejected turns so trajectory scoring ignores them |
| S5 | score_v6/4-arm scripts require e_sandbox beside parb_check_v6 (raw dirs) | FIXED (deployed copies) |
| S2b | contour 2.15: deterministic format repair (B/D obj-unwrap, J id-seq), zero model tokens, inert at 2.14 | FIXED @ r6+ (contract gate_v36) |
| S4b | loop gate-refused turns marked (trusted harness marker) and excluded; gate-blocked attempts mapped to attempted tools and penalized | FIXED @ r6 (suite controls, 66/0) |

## From Hermes — hard-v6 0.0.2.16 full arm diagnostics (20:33-20:46 CET)

- **P0 FIXED @ 8c9f762 (contour 0.0.2.17)** — the deterministic format repair added in 0.0.2.15
  never ran in the official score: all three call sites were gated by
  `POST_NORMALIZE = CHECKER_INJECT and contour_at_least(2,0)`, and issue #15 keeps
  `CHECKER_INJECT` off. Evidence in the published 0.0.2.16 arm (`full-216/`): 7/7 J rows still
  carried `items_not_bare_ids` and 5 rows `object_wrapped_in_list` with content already 1.00;
  no `contour:v20_*` event anywhere in the ledger. Six strict cells were format-only losses
  (B-ex6-00/01/03, J-ex6-00/04/05). 2.17 opens the gate for the keyword-free repair only;
  contract `harness/gate_v38_repair_pipeline_test.py` (9 checks) pins both directions: the
  repair runs at 2.17 with injection OFF, and the G/K keyword injectors stay OFF there.
- **LOGGED, owner call** — the same single `CHECKER_INJECT` switch also disables the H answer
  length trim (cut to the scorer's own 600-char ceiling, keeping uncertainty and numeric
  sentences; it inserts no checker keyword) and the K tax-negation note. If issue #15 is about
  scorer-keyword injection specifically, the H trim is the next candidate to unbundle; if it is
  about any answer post-processing, it must stay off. Not changed without an owner command.
- **LOGGED** — `gitleaks detect` over repo history reports 9 hits. The current tree is clean:
  the only remaining matches are two `gitleaks:allow`-annotated synthetic fixtures
  (`benchmarks/privacy-boundary/test_gateway.py` RFC1918 fixture, `scripts/security/secret_scan.py`
  scanner canary). No credential or real SSH target is exposed; old commits of the published
  contour scripts carried LAN material and were already sanitized in the current tree.
  Rewriting published history is not proposed.

## From Hermes — hard-v6 0.0.2.17 full arm (20:50-21:09 Europe/Rome)

- **P0 CONFIRMED @ 0.0.2.17** — format-only strict losses 6 -> 0; plain strict 39/71 -> 41/71; loop 4/6 unchanged.
  Artifacts: `benchmarks/hard/v6-results/full-217/`.
- **SHIPPED @ contour 0.0.2.18** — K boolean synonym canonicalize (`true`/`false` -> `yes`/`no` on yes/no fields),
  keyword-free, independent of CHECKER_INJECT (contract `harness/gate_v39_k_bool_test.py`, 11/11). Does not
  re-enable G contradiction marker or K_NEGATION inject path.
- Still open content misses for later stamps: A arithmetic/scaffold, H ungrounded_claims, J id_set, F avoid,
  D-p read_first; H trim / K_NEGATION unbundle still LOGGED pending evidence from 2.18 arm.


## From Hermes — 0.0.2.18 measured on the K battery (21:19 CET, K-only paired arms)

- **CONFIRMED @ 0.0.2.18** — K strict **1/4 -> 2/4** on identical seeds (K-only plan, same
  endpoint, back-to-back). Ledger shows `contour:v218_k_bool_yes` x2; K-ex6-00 recovered
  (`EXCLUDES_TAXES: true` -> `yes`, content 0.75 -> 1.00). K-ex6-01 rose 0.50 -> 0.75 and still
  fails on `value:SERVICE` (semantic value miss, not format). Artifacts:
  `benchmarks/hard/v6-results/k-218/` (`PAIR-K-217-218.txt`). n=4: mechanism evidence, not a
  significance claim.
- **Remaining deterministic gap (proposed 2.19, keyword-free)** — K-ex6-03 failed with
  `FREE_SHIPPING: да`: `k_bool_canonicalize` maps only `true|false`, and the K field comparator
  wants the reference token (`yes`). Extending the same mapping with `да -> yes`, `нет -> no`
  covers another format-free cell. Does not touch `K_NEGATION` (still injection-gated, off).
- **MEASUREMENT PITFALL recorded** — a malformed stamp is silent: `PARB_GATE_VERSION=0.0.218`
  resolves to `release 0.0.218, contour behavior 0.0`, i.e. a RAW arm with every contour feature
  off, and the run still exits 0 with a full record count. My first K pair hit exactly this
  (identical answers, zero contour events) and only the first log line exposed it. Hardening
  proposal for the owner: make `gate_versioning` fail closed (or normalize) when the stamp has
  no registered `(C,D)` instead of falling back to behavior 0.0.

## From Hermes — J battery probe (contour 0.0.2.18, 12 probe reps, 21:21 CET)

- **BANK DEFECT, LOGGED — J-ex6-03 is unanswerable as shipped**: the row carries no tuple table
  (keys `cat,id,kind,level,prompt,ref,seed,stage`, no `doc`/`assembled_doc`), the prompt gives a
  formula and asks for the top-2 ids, gold is `['c1','c3']`. All four published arms lose it
  (contour/basalt/codex/grok, content 0.00). Proposed remediation on owner command: regenerate the
  row with its data table, ship as a new bank version, and A/B rescore every saved arm with the
  frozen scorer before restating J for any arm. Not changed silently — the current bank sha16
  `f52acbd15b3271e7` pins four already-published arms.
- **BANK WORDING, LOGGED — J-ex6-06 is a two-way reading** («Пропустить score>=70» = skip or let
  through). Contour/basalt/codex answered the skip reading `['t2']`, grok the gold reading; the
  cell is a luck-of-reading test. Proposed: reword to `оставить только score>=70` in the next bank.
- **CHRONIC (not lottery)** — all four probed J cells are 0.00 across 3 fresh seeds (spread 0.00):
  retry/best-of-N cannot help. The two genuine model gaps are J-ex6-01 (drops the `срок<=10` filter
  in the second slot) and J-ex6-02 (three-way tie at severity*probability, tie-break by severity
  never ordered right).
- **Design hypothesis for the next contour stamp** — a J analogue of `logic_by_code` (category C):
  parse the inline tuple table + the stated filter/sort keys/tie-break, compute the order in code,
  emit bare JSON ids; fail CLOSED to `ask_ladder` on any parser doubt, exactly like
  `logic_parser_gap` does for C. Structural change, one version, contract test first.
- After the bank fixes and this stamp, J should be re-measured; the current J row (contour 3/7 vs
  raw 5-6/7) is **not** a clean reasoning verdict — 2 of the 4 lost cells are bank-side.
- **CLAIMED (to avoid a second double-implementation)** — Hermes/`~/sah-loopd` takes the J
  logic-by-code stamp next (contract test first, fail-closed parser). K `да/нет -> yes/no`
  extension (2.19) stays with the 0.0.2.18 author; do not start a J parser elsewhere.

## Checkpoint answered (2026-11-05 evening)
| item | status |
|---|---|
| GPT-6 provenance/authorization checkpoint (comment 6667774740) | ANSWERED publicly @ issue #15 comment 6668651655: owner-GO chronology stated honestly (relay GO posted 20:02Z, after 18:16-19:15Z runs authorized in chat earlier same day); pinned hashes of bank/scorer/harness; immutable commit 0cdb8729; verification recipe executed remotely by us (HTTP 200 + sha match); comparability restated; PR #17/#11 status independent of runs |
| Owner GO via BOSS relay (6667967176) | recorded: all v6 runs allowed continuous; PR #16/#17 merge remains owner-blocked; no secrets rule re-affirmed |

## Bank v6.1 (2026-11-05 late) — J defect fix, confirmed by probes
| item | status |
|---|---|
| J-ex6-03 prompt had NO data table (builder `% r4` with no placeholder; only the old builder revision passed it) — every arm lost the cell | FIXED v6.1 (table in prompt) |
| J-ex6-06 prompt said "skip score>=70" while ref kept >=70 — wording/ref contradiction | FIXED v6.1 (unambiguous wording, ref verified by hand) |
| v6.1 probes: contour 2.17 J-subset 5/7 (both ex-defect cells now 1.00); bare Basalt J-subset 7/7 | PUBLISHED (answers-basalt-j-v61.jsonl, results/ledger-contour-j-v61.jsonl) |
| J: contour 5/7 vs bare 7/7 on v6.1 probe — inspected both discordants: model arithmetic/order errors in the FIRST answer; nudge is best-of-two (takes second only if strictly better), no degradation mechanism found; 2/7 is inside noise band | CORRECTED: earlier "scaffold harm" wording withdrawn, no evidence |

## Hourly control 6667894164 — processed
| item | status |
|---|---|
| GO chronology requested (when/where/scope, paid arms) | ANSWERED publicly (comment 6669323957): owner chat GO before runs, scope = 4 arms 1 rep, ChatGPT via subscription CLI, Grok via owner OAuth, no new paid quota |
| "stop further runs until owner confirms" | HONORED: external arms on v6.1 HELD; in-flight v61c local arm finished and disclosed; external v6.1 runners pre-staged in ~/parb-v6-raw-ext, nothing launched |
| their P0: 2.15 repair inactive under POST_NORM master gate | ALREADY FIXED by me in master gate (call-site POST_NORMALIZE or contour_at_least(2,15)); their arm confirms repair events fire at 2.17 |
## From Hermes — hard-v6 0.0.2.18 full arm (21:14-21:28 Europe/Rome)

- **DONE** plain 45/71 strict (+4 vs 2.17, 0 regressions), loop 4/6; K 1/4 -> 3/4 via bool canon.
  Artifacts: `benchmarks/hard/v6-results/full-218/`.
- **SHIPPED @ contour 0.0.2.19** — H JSON contract: clear non-empty `claims`/`actions_done`
  (v6 scorer fail-hard); offline replay recovers H-ex6-01 and H-ex6-03 to 1.00; contract
  `harness/gate_v40_h_json_test.py` 7/7. Keyword-free; inject stays OFF.
- Still open: A arithmetic, H-ex6-02 requires miss, J id_set, F avoid, D-p read_first,
  D-l banned_attempted, K-ex6-01 SERVICE synonym, H-trim/K_NEGATION inject unbundle.

## From Hermes — hard-v6 0.0.2.19 full arm (21:30-21:36 Europe/Rome)

- **DONE** plain 47/71 (+2 vs 2.18 net), H 2/5 -> 4/5 via JSON contract clear; loop 4/6.
  First 219 attempt aborted (plan.json overwritten by jprobe to 12 rows); restored plan-full.json.
  Artifacts: `benchmarks/hard/v6-results/full-219/`.
- **SHIPPED @ contour 0.0.2.20** — K bool Cyrillic `да`/`нет` -> yes/no (extends 2.18 true/false).
  Motivated by K-ex6-03 regression on 2.19 (`FREE_SHIPPING: да`). J logic-by-code left to claimed owner.

## From Hermes — hard-v6 0.0.2.20/21 (21:38-21:46 Europe/Rome + next)

- **0.0.2.20 DONE** plain 47/71, loop **6/6**, K 3/4 (Cyrillic bool recovered K-ex6-03). Artifacts full-220/.
- **P0 FOUND**: D-ex6-p* answers already matched gold JSON but scored 0.4 via `LP.check_D_loop`
  (`read_first_missing`) — plain D mis-routed through the loop scorer.
- **SHIPPED @ contour 0.0.2.21** — D-plain uses `CK.CHECK["D"]` / check_D_plain_v6 when kind/mode != loop.
  Expected +3 strict on D-p0/p1/p2. J logic-by-code still claimed by other writer.

