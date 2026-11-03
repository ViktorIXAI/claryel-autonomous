# Terminal-Bench automatic GitHub publication

**Date:** 2026-11-03 22:58 UTC
**Status:** active
**Requested by:** Viktor Khudiakov
**Channel:** Telegram chat; user-stated source: ChatGPT subscription plus task
**Run:** tb4-66-verified-p2005-20261103-203323

## Task requests received

- Publish completed Terminal-Bench results to ViktorIXAI/claryel-autonomous without stopping or changing the benchmark run.
- Automatically add each future completed task result.
- Record model, quantization, hardware, Strata, Hermes version, skills, VerifiedHermes settings, model calls, tokens, time, and available resource usage.
- Record whether Claryel Autonomous Harness participates and Hermes learning-loop/skill-change state.
- Publish sanitized trajectories, verifier results, and machine-readable artifacts without hidden tests or reference solutions.
- Maintain cumulative summary and link current experiment from README.

## Decision

Use a separate publication watcher and clean worktree; scan artifacts and push only sanitized data.

## Context

Publication is read-only with respect to benchmark and must not add inference load to P2005.
