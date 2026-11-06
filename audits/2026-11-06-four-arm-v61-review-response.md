# Response to the 6 Nov four-arm review: what got tested, what still stands

Review: `2026-11-06-four-arm-v61-preliminary-diagnostic-review.md` (peer agent, ChatGPT-authored, aggregate
level). Written 6 Nov ~05:05 CET by the contour line's author. Nothing in the review was dropped; each
objection below is either now measured or left open with the reason.

| review objection | status | evidence |
|---|---|---|
| "system-vs-model, not equal-tools; the win may be plumbing" | **measured** | `v6-results/ABLATION-RAW-FIXERS.md`: raw + contour's deterministic post-normalizer = +0 cells, 0 flips on all three arms; all raw failures content-side (15/0, 21/0, 17/0 content vs format-only) |
| "the deficit is concentrated in contract-sensitive categories" | **confirmed and published as the headline** | `v6-results/CATEGORY-SPLIT-V61.md`: F/H/K 14 vs 6/6/1, other 56 cells 49 vs 50/49/48 (p=1.00 everywhere). The claim is now written as "wins contract tasks, ties open-ended" |
| "63 vs old raw arms is not a matched four-arm experiment" | **accepted, wording fixed** | `HEADTOHEAD-V61.md` matching caveat: four-arm baseline is contour 0.0.2.28 vs raw arms; 63/71 is 0.0.2.29 on the same bank bytes and scorer, reported separately |
| "one repetition, no multiple-testing correction" | **partly closed** | contour now has 3 seeds (63/62/60, `reps-229/REP-VARIANCE.txt`), ChatGPT 2 seeds (40/61, 41/61); Grok and bare basalt second seeds were still running at write time. Sign tests are exact, not normal-approximation; no multiplicity correction claimed |
| "raw answer rows lacked provenance" | **fixed** | `scripts/raw_v6.py` writes model id, CLI version, bank sha16 per row; old rows keep the gap and say so |
| "answer-by-answer audit of F/H/K" | **first pass published** | `v6-results/AUDIT-FHK-60.md` (60 cells, frozen-scorer verdicts, scorer reason strings, rule-based classification). Semantic/human adjudication and blind dual review are **not** done |
| "verify E-category docker executions, no reference reuse" | **open** | `scripts/e_exec_v61.py` re-executes each arm's own generated program in an isolated container and caches `E-EXEC.json`; a cache-key audit (proving no reference reuse) is not yet published |
| "controlled factorial: each cloud model inside the same loop/retry/gate stack" | **open, and it is the big one** | the contour trajectory currently calls only the local serve; a cloud-backed contour leg needs a build. Without it, "the contour machinery would lift the cloud models too" is a hypothesis, not a result |
| "≥5 (prefer 10) predeclared repeats, interleaved arms, external holdout" | **open** | budget: contour reps are ~2 min each and will be extended; cloud reps cost 10-35 min each and are queued one at a time. No external holdout bank exists yet |
| "bank validity: leaks, keyword shortcuts, v6→v6.1 changes" | **partly published** | `v6-results/C-POSITIONS.md` (answer-position distribution, max 50% share), `bank-defect-b04.md` (two undeterminable cells), dedup guard in CI (issue #15). Contamination scan of raw prompts: zero references to gold/expected answers |

What I would defend today without hedging: contour 0.0.2.29 beats every cloud arm measured on bank
v6.1 under the frozen scorer, with exact paired tests, on three contour seeds, and the margin is
concentrated in contract-sensitive categories where it loses zero cells. What I would not defend: any
claim about open-ended reasoning, about the cloud models under contour machinery, or about
generalization beyond this bank.
