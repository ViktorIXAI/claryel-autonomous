# Daily Research Summary: 2026-11-08

## Selected Papers

### 1. Can Coding Agents Sustain Continual Evolution without Forgetting? (arXiv:2611.03219, 2026-11-02)
**Core claim + evidence:** Continual harness self-evolution across sequential task distributions produces severe catastrophic forgetting. Meta-Harness raised SWE-Bench to 94.0% then dropped to 32.0% after further evolution on FeatureBench (66% relative decrease). Organized three SE datasets into six evolution directions; two representative methods showed consistent undermining of prior performance. Code released.

**Concrete tasks for harness:**
- Introduce a protected prior-task set (subset of hard bank + holdout from previous batches) that must not regress beyond a fixed margin on every autonomy acceptance.
- Log coverage loss explicitly in the autonomy ledger alongside any quality gain.
- Experiment with localized/modular updates (instead of global prompt/workspace edits) and measure forgetting rate.

**Potential risks:** Overly large protected sets freeze evolution; sparse coverage of protected cases misses collateral regressions; evaluation cost rises.

### 2. Beneath the Surface: What We Overlook When We Talk About Agent Evolution (arXiv:2611.07624, 2026-11-05)
**Core claim + evidence:** All 16 evolved agents gained previously uncovered tasks while losing previously covered ones. Reliability can rise (e.g., +5.2 points) while losing 10 covered tasks; most reliability gains increased deployment cost. Specific changes outperform generic reminders but interact; highest-scoring agent was not the best mean improver; stricter admission can discard useful variants. EvoAudit diagnostics on select/analyze/mutate/gate improved outcomes. Repeated evaluations, component interventions, admission replays.

**Concrete tasks for harness:**
- Require paired coverage-gain vs coverage-loss reporting on hard-bank + holdout for every candidate.
- Add applicability conditions and cost delta as mandatory fields in proposal records.
- Prototype a lightweight EvoAudit-style review step before acceptance (select, analyze, mutate, gate).

**Potential risks:** Preservation-aware rules may reject net-positive changes if loss is overweighted; cost accounting still immature.

### 3. A Theory of Reliable Self-Evolution for Agent Harnesses (arXiv:2609.08175, v2 2026-09-28)
**Core claim + evidence:** Provides a theoretically grounded condition for reliable adoption of a self-evolved harness (improvement in expected reward over the full user-task distribution with controlled retained-task degradation). Proposes a validation rule with guarantees. Performance ceiling is governed by verification and evaluation costs. Experimental performance shifts can diagnose stagnation sources (generation vs validation). Theory + constructive validation procedures.

**Concrete tasks for harness:**
- Formalize the current autonomy acceptance as an approximate reliable-adoption check: require positive expected gain on a representative sample plus non-regression bound on protected cases.
- Track verification/evaluation budget consumed per accepted change; flag when further gains approach the predicted ceiling.
- Use performance-shift diagnostics to decide whether to invest in better proposal generation or better validation.

**Potential risks:** Theoretical assumptions (i.i.d., known distributions) do not hold exactly; overly strict validation stalls progress; cost of independent validation data.

### 4. LLMs Know When They Know, but Do Not Act on It: A Metacognitive Harness for Test-time Scaling (arXiv:2605.14186, 2026-05-13)
**Core claim + evidence:** Inspired by Nelson-Narens metacognition theory, a harness that elicits pre-solve FOK and post-solve JOL signals and uses them for control (trust/retry/stop/aggregate) improves a fixed Claude Sonnet-4.6 from 48.3 to 56.9 pooled accuracy, exceeding strong leaderboard entries on HLE-Verified, LiveCodeBench v6, and R-Bench-V. Gains are non-uniform and largest on low-confidence problems. Ablations confirm both signals and the learned controller matter. Cross-domain (cognitive science) influence with strong empirical results on frozen model.

**Concrete tasks for harness:**
- Add optional FOK (pre-gate) and JOL (post-attempt) probes on a subset of hard-bank failures; use them to decide retry vs escalate to fixer.
- Log metacognitive scores in the autonomy ledger and correlate with actual success/failure for calibration.
- Test a simple controller that triggers redraw or repair only when JOL is low relative to FOK.

**Potential risks:** Signals may be poorly calibrated on our local models or long-horizon agent tasks; extra calls increase cost; controller overfitting to anchor set.

## Proposed Tasks
1. Define and freeze a small protected-case set (10-15 hard-bank items from prior successful runs) and require non-regression within 5% on it for the next three autonomy proposals.
2. Add coverage-loss and cost-delta fields to the autonomy ledger template and backfill the last accepted version.
3. Run a one-day pilot of FOK/JOL probes on 5 recent failures and report calibration against ground-truth outcome.

## Operator Question
Do you approve defining and freezing a minimal protected-case set (derived from recent successful hard-bank items) that must show non-regression before any further autonomous harness acceptance? This directly addresses the forgetting and coverage-loss findings but requires operator confirmation of which cases are non-negotiable.

All additions preserve English, practical style, and measurable harness changes. No production code or hard bank modified.
