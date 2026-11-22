# Daily Self-Evolution Research Summary — 2026-11-22

Selected 4 strongest recent papers with empirical evidence on modular self-improving harnesses, regret-guided non-regression, requirement-centered evolution, and the distinction between producing harness updates and benefiting from them. All applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Harnesses That Improve Themselves: A Unifying Framework for Self-Improving Agent Harnesses
https://arxiv.org/abs/2611.22299 (2026-11-17)

**Core claim + evidence:** Self-improving harnesses inspect execution traces, separate runtime bugs from model limits, and rewrite their own code. The framework pairs four editable runtime components (context and state, agent control, action interfaces, verification and recovery) with a four-stage loop (diagnose, propose patches, validate, deploy). Modular updates with validation gates outperform full-harness rewrites and prompt reflection; they generalize across models while bounding token cost. Practical defenses address prompt bloat, benchmark gaming, and evaluator tampering. Experiments on SWE-bench Lite show gated modular evolution wins across models and repositories at a fraction of the token cost.

**Concrete tasks for harness/autonomy:**
- Map current gates, fixers, validators, and telemetry to the four components (context/state, control, action interfaces, verification/recovery).
- Require any proposed patch to declare which component it edits and which validation gate must pass before ledger admission.
- Add a standing check that rejects proposals which expand prompts without a measured token or latency bound.

**Potential risks:** Over-modularization can create interface debt. Validation gates that are too weak still allow gaming. Full rewrites remain tempting on complex failures.

## 2. GUARD: Stabilizing Recursive Self-Improvement with Regret Guidance
https://arxiv.org/abs/2611.23476 (2026-11-17)

**Core claim + evidence:** Self-editing without external graders often backfires because reflection and scalar scores conflate newly broken behaviors with unsolved ones, causing local regressions, skill forgetting, and memory bloat. GUARD decomposes tasks into pre-execution self-checks and guides updates via directional regret. It pins mastered rules, prioritizes newly broken behaviors, and selects among parallel candidates by critic-free group-relative fitness. A Soft-HURT gate promotes an edit only when gains outweigh regressions, scopes specialized fixes, and guarantees non-regression on its gated buffer. Across memory, skill evolution, continual task streams, and domain reasoning benchmarks, GUARD improves performance with zero measured post-block forgetting and no stream-mean drops while cutting deployment token usage. Final held-out mean 73.22% vs 69.92% for the no-evolve agent.

**Concrete tasks for harness/autonomy:**
- Introduce a lightweight directional-regret note on the next autonomy cycle: list newly broken protected cases versus still-unsolved ones before any proposal is accepted.
- Require the Soft-HURT-style condition (gains outweigh regressions on a fixed buffer) as an explicit acceptance criterion in the ledger.
- Log every rejected edit with the collateral regression that triggered rejection.

**Potential risks:** Pre-execution self-checks can miss dynamic failures. Over-scoping of fixes reduces transfer. Group-relative fitness may still prefer locally high-scoring but narrow edits.

## 3. Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses
https://arxiv.org/abs/2611.24924 (2026-11-18)

**Core claim + evidence:** Existing methods overlook implicit requirements and interaction needs and often produce narrow, benchmark-specific patches. AHE-Beta uses a requirement-centered loop: (1) simulated users raise requirements as issues over multi-turn interaction, (2) team-based modification implements generalizable changes, (3) requirement-driven selection merges only when a verified requirement is resolved and review passes. On held-out tasks, pass@1 rises from 21.9% to 33.3% with 40.8% fewer tokens than Base Harness, exceeding Claude Code, Meta-Harness, and prior AHE. Blind human A/B test: real users prefer AHE-Beta in 31 of 48 valid pairs and rate it higher on all five dimensions, matching the simulator. Gains transfer to GLM-5.3 (+15.8% pass@1) and DeepSeek-V4.1-Flash (+5.3%) without further evolution.

**Concrete tasks for harness/autonomy:**
- Capture operator or simulated-user requirements as explicit issues in the autonomy ledger before generating patches.
- Prefer proposals that claim to satisfy a named requirement over pure score-maximizing patches; require the requirement to be re-verified after the edit.
- Run a small human or operator preference check on any non-trivial harness change before promotion.

**Potential risks:** Simulated-user requirements may diverge from real operator needs. Requirement verification can become another model-as-judge path. Transfer of preference gains is not automatic.

## 4. Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents
https://arxiv.org/abs/2605.30621 (revised 2026-11-04)

**Core claim + evidence:** Two distinct capabilities exist: harness-updating (produce useful persistent updates from evidence) and harness-benefit (actually benefit from those updates during task solving). Harness-updating is flat across capability tiers—even Qwen3.5-9B updates yield gains comparable to Claude Opus 4.6. Harness-benefit is non-monotonic: weak models benefit little (activation or adherence failures), mid-tier benefit most, strong models benefit less (ceiling effects). Design guidance: allocate capability budget to the task-solving agent rather than the evolver; focus training on harness invocation and long-horizon instruction following.

**Concrete tasks for harness/autonomy:**
- When scoring proposals, separately log whether the edit was produced by a strong evolver and whether the frozen task-solver actually activates and follows it on a protected slice.
- Prefer measuring activation/adherence (coverage-style or invocation counts) over raw score when deciding admission.
- Keep the evolver lightweight; invest evaluation budget in confirming the task-solver can use the new artifact.

**Potential risks:** Flat updating does not imply every weak evolver is safe. Activation failures can look like zero benefit even when the update is good. Ceiling effects may hide useful specialized edits for strong models.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, tag each proposal with the component it edits (context/control/action/verification) and a directional-regret note (newly broken vs still unsolved). Log only.
2. **For the operator:** Approve or reject adding an explicit Soft-HURT-style non-regression condition (gains must outweigh regressions on a fixed protected buffer) as a required ledger field before any future acceptance.
3. **For the agent (after approval):** Draft a short standing rule that every admission must name both the requirement (or failure cluster) being addressed and the resolution signal that confirmed non-regression.

## Operator question

Do you approve piloting the component-tag + directional-regret note (log only) on the next autonomy cycle, and/or adding the Soft-HURT-style non-regression condition as a required field in the autonomy ledger?
