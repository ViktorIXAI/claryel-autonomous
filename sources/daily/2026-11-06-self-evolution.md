# Daily Research Summary: 2026-11-06

## Selected Papers

### 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution (arXiv:2611.07624, 2026-11-05)
**Core claim + evidence:** Higher benchmark scores from harness evolution do not guarantee reliable, efficient, or transferable improvement. Across 16 evolved agents, all gained new tasks but lost previously covered ones. Reliability can rise while coverage drops; most gains increase deployment cost. Specific component changes outperform generic reminders, but combinations can interfere. Strict admission can discard useful variants. EvoAudit/AGE revisions of select/analyze/mutate/gate improved outcomes. Empirical: repeated evaluations, component interventions, admission replays on general (τ³-Banking) and coding (Terminal-Bench 2) tasks with MiniSWE and Codex harnesses.

**Concrete tasks for harness:**
- Add preservation-aware metrics to autonomy ledger: track newly covered vs. lost tasks on hard bank paired runs.
- Log deployment cost (tokens, energy, latency) alongside scores for every version.
- Implement an admission gate that rejects proposals improving one subset while regressing protected cases, with explicit applicability conditions.
- Audit recent proposals for generic reminders vs. specific changes and measure interference.

**Potential risks:** Over-strict admission may discard useful intermediate variants; cost tracking adds overhead; protected sets may become stale.

### 2. Can Coding Agents Sustain Continual Evolution without Forgetting? (arXiv:2611.03219, 2026-11-02)
**Core claim + evidence:** Continual harness self-evolution across task types causes severe catastrophic forgetting. Meta-Harness raised SWE-Bench to 94% then dropped to 32% after FeatureBench evolution (66% relative drop). Conflicts identified in verification, workflow, and budget strategies. Code: https://github.com/THU-Agent/continual-harness-evolution.

**Concrete tasks for harness:**
- Measure forgetting on successive hard-bank category batches: evolve on one category, then evaluate retention on previous categories with paired seeds.
- Classify recent harness edits by conflict type (verification/workflow/budget) and test ablation of conflicting modules.
- Add a retention gate requiring non-regression on a fixed previous-task subset before accepting new evolution.

**Potential risks:** Retention checks increase evaluation budget; over-conservative gates slow adaptation; category batches may not match real task diversity.

### 3. How Do Coding-Agent Harnesses Self-Evolve? An Empirical Study of Retrospective Adaptation (arXiv:2610.34938, 2026-10-26)
**Core claim + evidence:** Retrospective skill (“review completed session and propose harness changes”) produces many proposals, but few reduce the targeted problem on later tasks. Of 12 implemented changes, only a minority eliminated or reduced the issue; some added unrelated work. Most proposals referenced session events, but some were generic.

**Concrete tasks for harness:**
- Implement a retrospective review step after each hard-bank batch that proposes scoped edits, then validate only on the specific failure pattern with hold-out tasks.
- Track whether accepted retrospective changes reduce recurrence of the same failure mode in subsequent runs.
- Reject proposals that do not demonstrably reduce the targeted action on fresh sessions.

**Potential risks:** Retrospective proposals may introduce unmeasured regressions; validation on narrow patterns may miss broader effects.

### 4. The Harness Is the Model: Agent Scaffolding Changes a Fixed LLM's Compliance with Banking Conduct Rules, Unevenly Across Models (arXiv:2611.06116, 2026-11-04)
**Core claim + evidence:** With model fixed, harness choice changes compliance rates substantially within a model (up to 11.5 pp spread). Same-model reviewer reduced violations without increasing over-refusals. Deterministic scoring from tool traces. Some rules (date arithmetic) failed in all harnesses.

**Concrete tasks for harness:**
- Add a same-model independent critic path for high-stakes validation steps and measure violation/over-refusal rates on a compliance-style subset.
- Prefer deterministic tool-trace assertions over model judges for autonomy decisions.
- Document harness × model interaction effects in the ledger when comparing versions.

**Potential risks:** Independent critic increases latency/cost; model-specific harness effects may not transfer to our local frozen models.

## Proposed Tasks
1. Design a minimal preservation-aware admission checklist (new coverage, lost tasks, cost delta, protected-case non-regression) and apply it retrospectively to the last three autonomy versions.
2. Run a small continual-evolution experiment: evolve harness on one hard-bank category for 2–3 cycles, then measure paired retention on two prior categories.
3. Add cost (energy/token) logging as a first-class field in the autonomy ledger for the next evaluation cycle.

## Operator Question
Do you approve creating a protected-case subset (e.g., historically stable hard-bank tasks) and requiring non-regression on it as a hard admission rule before any further autonomous harness edits? This would slow adaptation but address the forgetting and coverage-loss patterns observed.

All additions preserve English, practical style, and measurable harness changes. No production code or hard bank modified.
