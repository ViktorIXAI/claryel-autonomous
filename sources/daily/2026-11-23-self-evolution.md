# Daily Self-Evolution Research Summary — 2026-11-23

Selected 4 strongest recent papers with empirical or theoretical evidence on coverage-guided evolution, evaluation bottlenecks, non-regression gates, and reliable adoption conditions. All applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Evolve Where It Matters: Coverage-Guided Self-Evolution of Agent Skills
https://arxiv.org/abs/2611.25429 (2026-11-19)

**Core claim + evidence:** Existing self-evolution judges runs as a whole and cannot separate wrong instructions from instructions the agent did not follow. Instruction-level coverage labels each instruction of a skill as follow / not-follow / not covered. SkillPlumber uses a persistent root-cause-analysis agent to turn these labels into revision questions, checks each revision against the next run, and distills findings into a shared strategy library. Across three benchmarks and three executors, SkillPlumber solves 64.7–70.5% of tasks (25.6–30.4 pp above the initial skill, 8.7–14.0 pp above the strongest baseline). Removing coverage reduces recovered failures by 20.8% on SkillsBench with GPT-5.5. Token cost is higher in total but comparable per recovered task.

**Concrete tasks for harness/autonomy:**
- Add a lightweight coverage note to failure logs: for each gate/fixer/validator instruction or rule, record whether it was followed, not followed, or not reached in the last N runs.
- Require proposals that edit a specific rule to cite the coverage evidence that the rule is the source of the failure.
- Pilot a small RCA-style question generator that turns uncovered or not-followed rules into one concrete patch candidate.

**Potential risks:** Coverage instrumentation adds overhead and can itself become a source of noise. Over-focusing on not-followed rules may ignore higher-level control-flow problems. Strategy library can accumulate low-value entries.

## 2. The Resolution Hypothesis: Agent Evolution's Key Is Identifying Improvements
https://arxiv.org/abs/2611.23068 (2026-11-17)

**Core claim + evidence:** Agent evolution stalls because noisy evaluations cannot reliably identify better artifacts, not because proposers fail to generate them. Across seven evolution methods and six models (>10M LLM calls), candidate selection is no better than random at distinguishing helpful from harmful artifacts, so errors accumulate. At the method level, typical margins of a few percentage points are smaller than the variance between independent runs of the same method. Large published gains often collapse once graders are repaired. The bottleneck is making true improvements detectable and accumulable.

**Concrete tasks for harness/autonomy:**
- Require every acceptance decision to include a paired, seed-matched comparison on a fixed protected slice rather than a single-run score delta.
- Log the variance of the current scorer on the last 20 runs so that proposed gains can be compared against measurement noise.
- Add a standing note that any claimed improvement smaller than observed run-to-run variance must be marked "unresolved" in the ledger.

**Potential risks:** Over-conservative thresholds can freeze useful small gains. Variance estimates themselves can be noisy on small samples. Deterministic gates help but do not eliminate all evaluation noise.

## 3. GUARD: Stabilizing Recursive Self-Improvement with Regret Guidance
https://arxiv.org/abs/2611.23476 (2026-11-17)

**Core claim + evidence:** Self-editing without external graders often conflates newly broken behaviors with unsolved ones, causing regressions, skill forgetting, and memory bloat. GUARD decomposes tasks into pre-execution self-checks and guides updates via directional regret. A Soft-HURT gate promotes an edit only when gains outweigh regressions on a gated buffer and scopes specialized fixes. Across multiple benchmarks, GUARD improves held-out performance (e.g., 73.22% vs 69.92%) with zero measured post-block forgetting and no stream-mean drops while reducing token usage.

**Concrete tasks for harness/autonomy:**
- Introduce a directional-regret field in the next autonomy cycle: list newly broken protected cases versus still-unsolved ones before admission.
- Make the Soft-HURT condition (gains outweigh regressions on a fixed buffer) an explicit, logged acceptance criterion.
- Reject and archive any edit that improves one cluster while degrading any protected case.

**Potential risks:** Pre-execution checks miss dynamic failures. Over-scoping reduces transfer. Group-relative selection can still favor narrow edits.

## 4. A Theory of Reliable Self-Evolution for Agent Harnesses
https://arxiv.org/abs/2609.08175 (2026-09-29, updated)

**Core claim + evidence:** Gains on failed tasks do not automatically preserve performance on previously successful tasks. The paper provides a theoretically grounded condition under which a self-evolved harness can be reliably adopted, plus a validation rule that guarantees the condition. Progressive improvement is possible, but the performance ceiling is determined by the costs of verification and evaluation. Experimental evidence on performance shifts can identify sources of stagnation.

**Concrete tasks for harness/autonomy:**
- Formalize the current protected-case set and the admission rule as an explicit reliable-adoption condition that must be checked before any ledger entry is marked accepted.
- Track verification and evaluation cost (tokens, wall time, energy) alongside quality so that the ceiling can be measured rather than assumed.
- When evolution stalls, diagnose whether the stall is due to insufficient verification budget or to genuine capability limits.

**Potential risks:** Theoretical guarantees rest on assumptions (independent validation data, cost models) that may not hold in practice. Over-strict validation can prevent any progress. Cost tracking itself consumes resources.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, add a coverage-style note (followed / not-followed / not-reached) for the three most frequent failure rules and a directional-regret note. Log only; no code change.
2. **For the operator:** Approve or reject requiring that every future acceptance include a seed-matched paired comparison whose margin exceeds the observed run-to-run variance of the scorer (Resolution Hypothesis discipline).
3. **For the agent (after approval):** Draft the exact ledger fields for coverage note + Soft-HURT condition so they can be added as standing rules without touching production code.

## Operator question

Do you approve piloting the coverage-style failure note and directional-regret field (log only) on the next autonomy cycle, and/or requiring seed-matched paired evidence that exceeds measured scorer variance before any future acceptance?
