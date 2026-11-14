# Daily Self-Evolution Research Summary — 2026-11-14

Selected 4 strongest recent papers with empirical evidence on catastrophic forgetting in continual harness evolution, statistical control of false updates, disentangling harness-updating from harness-benefit (especially relevant for smaller local models), and joint quality-cost Pareto optimization. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Can Coding Agents Sustain Continual Evolution without Forgetting?
https://arxiv.org/abs/2611.03219 (2026-11-02)

**Core claim + evidence:** Existing harness self-evolution work largely studies single-task evolution. In continual multi-task settings, evolution on a subsequent dataset can substantially undermine performance on previously seen datasets. With DeepSeek-V4-Flash-0731, Meta-Harness reached 94.0% on SWE-Bench after evolution, but after further evolution on FeatureBench the SWE-Bench score fell to 32.0% by the fifth round (66% relative decrease). Two representative methods were tested across six evolution directions on three SE datasets.

**Concrete tasks for harness/autonomy:**
- Maintain a fixed protected-case / hold-out regression set drawn from earlier hard-bank categories and require every new evolution round to report paired deltas on both the new slice and the protected set.
- Add a simple "forgetting monitor" to the autonomy ledger that flags any accepted change whose paired score on prior categories drops more than a threshold (e.g., 2 pp).
- Experiment with interleaved or replay-style evolution batches that mix old and new task types instead of pure sequential specialization.

**Potential risks:** Over-protecting old categories can prevent useful specialization. Replay increases evaluation cost. Thresholds on small paired slices are noisy.

## 2. Trustworthy Recursive Self-Improvement with Statistical Guarantees (TRUST)
https://arxiv.org/abs/2611.10787 (2026-11-07)

**Core claim + evidence:** Greedy gates that accept any higher validation score produce many inferior updates (average 45.59% accepted inferior updates). TRUST adapts an online multiple-hypothesis testing procedure to control the rate of false evolution, with an LLM helping set evidence thresholds from historical context. Under interpretable assumptions it bounds the proportion of accepted updates that cause unacceptable loss and provides a lower bound on final gain. On HotpotQA, DROP, and APPS with DeepSeek-V4-Flash and Qwen-3.8-Flash it reduced accepted inferior updates to 2.78% while matching or exceeding stronger statistical baselines.

**Concrete tasks for harness/autonomy:**
- Replace pure score-threshold admission with a simple statistical gate that requires the observed paired gain to exceed a historical-variance-adjusted threshold before acceptance.
- Maintain a running estimate of false-evolution rate in the autonomy ledger and raise the evidence bar when the recent rate exceeds a bound.
- Pilot the gate on a replay of the last 10 autonomy decisions and report how many would have been rejected under TRUST-style control.

**Potential risks:** Conservative thresholds can slow progress. Variance estimates on small hard-bank slices are noisy. The LLM-assisted threshold setting itself needs a deterministic fallback.

## 3. Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents
https://arxiv.org/abs/2605.30621 (v2 2026-11-04)

**Core claim + evidence:** Two distinct capabilities exist: (i) harness-updating (producing useful persistent updates from evidence) and (ii) harness-benefit (actually gaining from the updated harness). Updating capability is roughly flat across model tiers — even Qwen3.5-9B updates yielded gains comparable to Claude Opus 4.6. Benefit is non-monotonic: weak-tier models benefit little (failure to activate or to follow harness artifacts faithfully), mid-tier benefit most, strong-tier less than mid-tier. Source code available.

**Concrete tasks for harness/autonomy:**
- When evaluating local (weaker) models, separately score whether a proposed harness change is activated and faithfully followed, not only the final task score.
- Prefer investing evaluation budget in measuring harness-following reliability on the target local model rather than assuming updates transfer equally.
- Add a lightweight activation/following check to the paired evidence required before accepting a change intended for the local contour.

**Potential risks:** Extra checks increase cost. Distinguishing activation failure from genuine non-benefit requires careful instrumentation. Findings may not fully transfer to the specific local quantization used here.

## 4. ParetoSaddler: Pareto-Guided Optimization of Agent Harnesses for Quality and Cost
https://arxiv.org/abs/2611.02079 (2026-11-01)

**Core claim + evidence:** Existing harness optimizers primarily maximize quality. Joint quality-cost optimization is harder because intermediate deployment preferences can prematurely discard candidates that enable later gains. ParetoSaddler separates intermediate candidate promotion (Bayesian bootstrap Pareto support on either quality or cost) from final deployment selection. On ClawMark quality rose from 70.86% to 81.35% while cost fell from $1.17 to $1.01 per task; on GAIA2 quality rose from 56.22% to 62.89% while cost fell from $0.78 to $0.45. Pareto-aware search retained useful intermediates that pure quality or pure preference gates would discard.

**Concrete tasks for harness/autonomy:**
- When ranking candidate harness edits, record both quality (hard-bank score) and cost (energy/tokens/latency from telemetry) and keep candidates that improve either axis under a paired comparison.
- Add a simple Pareto front sketch to the autonomy ledger so later reviews can see which rejected proposals improved cost at small quality cost.
- Pilot a two-stage admission: promote on either quality or cost improvement, then select final deployment only on the joint criterion.

**Potential risks:** Cost metrics (especially energy) have higher variance than quality scores. Premature joint selection can still discard useful paths. Requires reliable telemetry joins.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record paired deltas on both the current evaluation slice and a fixed protected subset of earlier categories; flag any change that regresses the protected set by more than 2 pp. Log only — do not block. No production code change.
2. **For the operator:** Approve or reject adding a minimal statistical-admission sketch (historical-variance-adjusted gain threshold) to the next pilot, with results recorded in the ledger but not yet used to auto-reject.
3. **For the agent (after approval):** Draft the exact ledger fields needed for a forgetting monitor (prior-category paired deltas) and a simple Pareto quality-vs-energy entry, specifying where they would be written without altering gate_run.py.

## Operator question

Do you approve piloting the forgetting-monitor logging (protected-set paired deltas) together with a non-blocking statistical-admission sketch on the next autonomy cycle, or should we start with only the forgetting-monitor logging?
