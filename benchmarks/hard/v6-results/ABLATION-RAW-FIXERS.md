# Fair-controls ablation: is the contour win just format plumbing?

The independent audit (`audits/2026-11-06-four-arm-v61-preliminary-diagnostic-review.md`) raised the
right objection: the contour has deterministic validation, format repair and gates, the cloud arms get
one unassisted answer, so the win might be an artifact of plumbing rather than of what the contour
decides. This ablation gives the raw arms **exactly one contour component and nothing else**: the
deterministic post-normalizer from `harness/gate_run.post_normalize_answer` (zero model tokens, no
checker feedback, no retry, content preserved), re-scored by the frozen scorer.
Generator: `scripts/raw_plus_fixers_ablation.py`, output `ABLATION-RAW-FIXERS.json`.

| arm | strict raw | strict raw + repair | repaired cells | failures: content / format-only |
|---|---|---|---|---|
| basalt | 56/71 | 56/71 | 0 | 15 / 0 |
| codex | 50/71 | 50/71 | 0 | 21 / 0 |
| grok | 54/71 | 54/71 | 0 | 17 / 0 |
| contour 0.0.2.29 rep0 | 63/71 | — | — | 8 / 0 |

## What this shows

1. The contour's deterministic repairer changes **nothing** for any raw arm: 0 cells repaired, 0 flips,
   on all three arms. Its two rules (single-object list unwrap for B/D, decorated-item id
   normalization for J) simply never fire on the raw answers.
2. Every raw-arm failure on this bank is **content-side**: Grok 15 content / 0 format-only, ChatGPT
   21 / 0, bare basalt 17 / 0. The contour's own 8 failures are also content-side. Nobody in this
   experiment is losing points for formatting.
3. Therefore the contour's +7..+13 cells over the cloud arms cannot be a format-plumbing artifact: the
   raw answers are already format-valid where they are marked wrong. The win is in what the contour
   *decides to check and re-decide before answering* (contract gates, per-candidate verdicts,
   verification, retry budget) — components the raw arms do not have and cannot be given offline.

## Limits of this ablation (read before quoting)

- It isolates only the deterministic offline normalizer. A full factorial (each cloud model driven
  through the same loop/retry/gate machinery) requires the contour trajectory to run on those models;
  the current contour implementation calls the local serve, so a cloud-backed contour leg is a
  separate build, listed as work rather than claimed as done.
- "Format-only" means the scorer's `format_ok` passed while `content < 1.0`; a scorer that is too
  permissive on format would understate format problems. The scorer is frozen and separately tested
  (`harness/gate_v4x` contracts, issue #7 CI), and the answer-by-answer F/H/K audit is the check on
  that — see `REVIEW-INBOX.md` and issue #6.
