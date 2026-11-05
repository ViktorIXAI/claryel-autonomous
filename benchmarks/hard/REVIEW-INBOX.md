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
