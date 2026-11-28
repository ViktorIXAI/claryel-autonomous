# Self-Evolution and Broader Scientific Influence Reading List

This file collects key papers on agent harness self-evolution and related scientific domains. It is maintained for practical use by the autonomous agent: each entry includes what can be turned into concrete tasks.

## Core Agent Harness Self-Evolution

### Self-evolving Agent Harness
https://arxiv.org/abs/2610.18813

Formalizes harness self-evolution: revising prompts, memory, workflows, and executable components while keeping model weights fixed. Distinguishes interpreted state from code and control logic changes.

**Practical agent tasks:**
- Map current autonomy ledger decisions to the paper's update-target categories.
- Propose a classification of our existing gates, fixers, and validators according to the paper's taxonomy.
- Generate a checklist of surfaces we are allowed to revise versus those that must stay frozen.

### Self-Evolving Harness on Multiple Tasks with the Agent as Its Own Optimizer
https://arxiv.org/abs/2609.38372

The same frozen model acts as both solver and proposer: it solves tasks, then reads full run records and directly edits the harness that ran it. Started from a 49-line seed and produced gains on both in-distribution and out-of-distribution benchmarks.

**Practical agent tasks:**
- Design a minimal seed harness (under 100 lines) that still passes our hard bank and use it as a baseline for self-editing experiments.
- Implement a "solver then proposer" loop that reads complete telemetry and proposes bounded harness edits.
- Measure hold-out degradation when the same harness is evolved across successive task batches.

### Self-Harness: Harnesses That Improve Themselves
https://arxiv.org/abs/2606.09498

Iterative loop: weakness mining from traces → minimal harness proposals → regression-tested acceptance. Demonstrated relative gains up to 50-60% on held-out sets across multiple models and benchmarks.

**Practical agent tasks:**
- Cluster recent failures.md entries into recurring weakness patterns and generate one minimal patch proposal per cluster.
- Add a non-regression acceptance rule that requires paired evidence before promoting any harness change.
- Run a controlled self-harness cycle on a frozen subset of the hard bank and publish the accepted/rejected proposals.

### Hierarchical Self-Improvement: A Framework for Task-Specific Evolvable Agent Harnesses
https://arxiv.org/abs/2608.08466

Single frozen model operates at three scopes: task harness, evolver that rewrites the harness, and meta-evolver that rewrites the evolver's strategy. Shows large gains on moderate-difficulty tasks with clear limits on harder ones.

**Practical agent tasks:**
- Separate current autonomy rules into a task-level harness and a meta-level strategy document.
- Propose a meta-evolver prompt that reviews the last N autonomy ledger entries and suggests rule changes.
- Test whether a meta-level review improves the quality of subsequent harness proposals.

### From Failed Trajectories to Reliable LLM Agents: Diagnosing and Repairing Harness Flaws (HarnessFix)
https://arxiv.org/abs/2606.06324

Builds a Harness-aware Trace Intermediate Representation from raw traces, attributes failures to specific harness layers, and generates scoped repair operators that are validated against regressions.

**Practical agent tasks:**
- Define a lightweight intermediate representation for our gate_run.py traces and failure logs.
- Attribute the last 20 failures to specific layers (gate, fixer, validator, retry policy, telemetry).
- Generate and validate one scoped repair patch per attributed failure layer.

### Self-Healing Harness for Runtime Oversight of Agent Self-Modification
https://arxiv.org/abs/2609.24130

Admission control for self-modification: agent proposes changes, external runtime gate decides persistence. Many proposals improved the triggering case but regressed protected cases.

**Practical agent tasks:**
- Implement a protected-case set that must never regress when accepting a harness change.
- Add an admission gate that rejects proposals which improve one failure while degrading any protected case.
- Log every rejected self-modification with the collateral regression that caused rejection.

### HarnessFlow: MCTS-Guided Harness Optimization for LLM Agents
https://arxiv.org/abs/2611.06254

Uses Monte Carlo Tree Search over a refinement tree of complete executable harnesses under a limited evaluation budget. Outperformed initial harnesses and Meta-Harness while reducing cost.

**Practical agent tasks:**
- Represent our recent harness versions as a refinement tree and score them by paired hard-bank results.
- Propose a small MCTS-style search that explores 5-10 candidate harness edits under a fixed token budget.
- Compare search cost versus quality gain against our current sequential autonomy process.

### MESH-Harness: Self-Improving Agent Harnesses via Bandit-Guided Compositional Evolution
https://arxiv.org/abs/2610.05300

Organizes harnesses into functional modules with explicit interfaces and uses LinUCB to search combinations under limited evaluation budgets.

**Practical agent tasks:**
- Decompose gate_run.py into explicit modules (gate, fixer, validator, telemetry, retry) with stable interfaces.
- Maintain a small library of alternative module implementations and test compositional combinations.
- Track which module combinations improve hard-bank scores without increasing energy or latency.

## Verification, Repair, and Evaluation Foundations

### Rethinking Verification in Agent Harnesses
https://arxiv.org/abs/2610.34577

Studies when and how to apply verification: instructions, reminders, completion gates, and independent critics. Shows that verification placement strongly affects reliability.

**Practical agent tasks:**
- Audit every current verification point in gate_run.py and classify it (instruction, reminder, completion gate, independent critic).
- Propose moving or adding one verification step based on the paper's findings and measure the effect.
- Add an independent critic path that does not share context with the primary solver.

### Verification-Gated Redraw and Repair for Local Small Language Models
https://arxiv.org/abs/2611.00707

Paired comparison of raw generation, redraw, and diagnosis-driven repair on local small models. Emphasizes controlled evidence.

**Practical agent tasks:**
- Add a paired redraw-versus-repair experiment on a subset of hard-bank failures using only local models.
- Require diagnosis evidence before any repair is applied.
- Publish the paired results in the autonomy ledger.

### LLM-as-a-Judge Is Not an Oracle
https://arxiv.org/abs/2609.02246

Deterministic checks should be stronger than model-as-judge evaluations. Model judges introduce additional failure modes.

**Practical agent tasks:**
- Replace or augment any model-as-judge steps with deterministic assertions where possible.
- Measure disagreement rate between model judge and deterministic gates on recent runs.
- Prefer deterministic evidence in all autonomy acceptance decisions.

## Broader Scientific Domains (for Cross-Influence)

The daily research routine must also scan for work that can affect agent design through other fields:

- **Macroeconomics / resource allocation**: papers on cost-aware decision making, energy accounting, and long-horizon resource trade-offs.
- **Sociology / organizational behavior**: studies of trust, transparency, accountability, and multi-agent coordination.
- **Psychology / cognitive science**: work on verification, reflection, metacognition, and failure attribution.
- **Systems engineering / reliability**: formal methods, admission control, regression testing, and continuous evolution under constraints.
- **Other domains**: any empirical finding that can be turned into a measurable constraint, gate, or task for the harness.

## Daily Research Routine Rules

The agent must run the following process once per day:

1. Search arXiv, Semantic Scholar, and related sources for new papers on:
   - Agent harness self-evolution, self-improvement, verification, and repair
   - Influences from macroeconomics, sociology, psychology, cognitive science, systems engineering, and other scientific domains that could affect agent design
2. Select the strongest 3-5 papers based on empirical evidence, reproducibility, and practical applicability.
3. For each selected paper, extract:
   - Core claim and evidence
   - Concrete tasks that can be injected into the current harness or autonomy process
   - Potential risks or regressions if applied
4. Append a short summary to this file or to a dated companion file under `sources/daily/`.
5. Propose 1-3 concrete tasks for itself (or for the operator) based on the findings.
6. Ask the operator a clear question if human judgment or approval is required before proceeding.
7. Do not modify production code or the hard bank without explicit approval and paired evidence.

All additions must preserve the existing style: English, practical, and tied to measurable harness changes.

## Daily Summary 2026-11-25

Selected four recent papers with strong empirical grounding and direct applicability to frozen-model harnesses that use paired evidence and an autonomy ledger.

### Which Failure Does an Intervention Repair? (arXiv:2611.29290)
Core claim: Interventions (skills, harnesses, budget) interact rather than add; a harness can absorb, rescue, or preserve a skill's effect. Matched factorial study (~0.9M trajectories) shows self-evolved skills rarely beat short human skills, can learn shortcuts, and fail to transfer. Feedback recovers mainly failures with visible error signals.
Evidence: 1,872 instances × 4 models × 4 skills × 4 harness levels × 3 budgets, three repeats each; code and data released.
Concrete tasks: Classify recent hard-bank failures by presence/absence of visible error signal; measure whether current repair paths preferentially convert signal-bearing failures. Add a protected-case check that rejects any proposed skill/harness edit which collapses score on a held-out model or harness level.
Risks: Over-fitting to the paper's harness ladder; applying a skill that was optimal for one local model to another without re-validation.

### Harnesses That Improve Themselves: A Unifying Framework (arXiv:2611.22299)
Core claim: Four editable runtime components + four-stage diagnose-propose-validate-deploy loop with modular gated evolution outperforms full-harness rewrites and pure prompt reflection on SWE-bench Lite at lower token cost. Defenses against prompt bloat, benchmark gaming, and evaluator tampering are required.
Evidence: Experiments across models and repositories showing modular updates generalize better.
Concrete tasks: Map current gate/fixer/validator/telemetry surfaces onto the four components; propose one modular patch that targets only the verification-and-recovery component and require a non-regression gate on a fixed protected subset before acceptance.
Risks: Full-rewrite style proposals that overfit the current bank and regress on OOD tasks.

### GUARD: Stabilizing Recursive Self-Improvement with Regret Guidance (arXiv:2611.23476)
Core claim: Directional regret over pre-execution self-checks plus a Soft-HURT gate that promotes an edit only when gains outweigh regressions prevents catastrophic forgetting and memory bloat while improving performance and cutting deployment tokens.
Evidence: Consistent gains across memory, skill-evolution, continual-stream, and domain-reasoning benchmarks with zero measured post-block forgetting.
Concrete tasks: Define a small set of pre-execution self-checks derived from existing validators; log directional regret for each autonomy proposal and reject any edit whose Soft-HURT score is non-positive on the protected-case buffer.
Risks: Incorrect self-check decomposition can pin the wrong rules and freeze useful exploration.

### The Resolution Hypothesis (arXiv:2611.23068)
Core claim: Agent evolution is bottlenecked by noisy evaluation that cannot reliably identify true improvements (selection ≈ random; method margins smaller than run-to-run variance). Over 10M calls across 7 methods and 6 models.
Evidence: Repeated evaluations show helpful candidates exist but selectors fail to find them; published rankings often rest on luck.
Concrete tasks: Require at least two independent paired seeds (or a bootstrap CI that excludes zero) before any autonomy acceptance decision. Log the resolution width of every score used for promotion.
Risks: Stricter gates slow progress if the current bank already has low variance; may reject real but small gains.

**Proposed concrete tasks (2026-11-25):**
1. Attribute the last 30 hard-bank failures to presence/absence of a visible error signal and measure current repair conversion rates on each subset (paired).
2. Add a Soft-HURT-style non-regression gate over a frozen protected-case buffer to the autonomy acceptance rule and re-evaluate the last three rejected proposals under it.
3. Require resolution evidence (multi-seed CI or bootstrap) in the next autonomy ledger entry before any harness change is marked Autonomously-adopted.

**Question for operator:** Approve running a controlled, non-production experiment that implements the Soft-HURT-style gate and the visible-error-signal attribution on a frozen subset of the hard bank (no production code or bank changes)? Yes / No / Modify.

## Daily Summary 2026-11-26

See full write-up in `sources/daily/2026-11-26-self-evolution.md`.

Selected four papers focused on context/skill management, coverage-guided revision, detection gaps in self-improvement, and feedback-free skill erosion.

Key practical takeaways for the harness:
- Prefer individually accessible raw records (context folding) over pure summarization in the autonomy ledger.
- Use instruction-level coverage labels to target repairs at actual instruction faults rather than whole-run outcomes.
- Measure and log the detection rate of existing gates (surfaced vs silent failures); silent failures stay unrepaired.
- Block pure feedback-free self-rewrites of rules; require paired evidence and a prior-divergence check.

**Proposed concrete tasks (2026-11-26):**
1. Measure detection rate on last 50 hard-bank failures.
2. Prototype context folding on last 10 autonomy proposals (paired).
3. Generate one coverage-targeted repair proposal for operator review.

**Question for operator:** Approve a controlled, non-production experiment that measures the detection gap and tests context folding versus current ledger summarization (paired evidence only, no production code or hard-bank changes)? Yes / No / Modify.

## Daily Summary 2026-11-27

See full write-up in `sources/daily/2026-11-27-self-evolution.md`.

Selected four papers emphasizing transferable interventions, auditable certificates, and shared failure modes.

Key practical takeaways for the harness:
- Evolve intervention policies from same-task success/failure contrasts and filter with protected-subset replay to reduce overfitting.
- Require claim-obligation certificates (not just scores) before accepting repairs in the autonomy ledger.
- Generate probe tasks that isolate recurring failure modes and add them to the protected-case buffer.
- Annotate every proposal with the explicit + implicit requirement it satisfies.

**Proposed concrete tasks (2026-11-27):**
1. Author two TransHarness-style intervention policies from recent same-task pairs and evaluate only on a frozen protected subset (paired).
2. Prototype a minimal claim-obligation certificate for three recent failures.
3. Generate one ProbeAgent-style probe for the highest-frequency failure mode and add it to the protected-case buffer.

**Question for operator:** Approve a controlled, non-production experiment that implements the TransHarness-style same-task contrast + protected-subset replay and the claim-obligation certificate check on a frozen subset of the hard bank (no production code changes, no hard-bank modifications)? Yes / No / Modify.

## Daily Summary 2026-11-28

See full write-up in `sources/daily/2026-11-28-self-evolution.md`.

Selected four papers on evidence-producing verification, context/skill management for long-horizon evolution, held-out gated memory evolution, and requirement-centered harness engineering.

Key practical takeaways for the harness:
- Require claim-obligation certificates (not scalar scores alone) before accepting any repair or edit in the autonomy ledger.
- Prefer context folding (individually accessible digests + on-demand full records) over pure summarization; selectively delete unused skills.
- Accept macro rules or ledger patterns only when held-out paired accuracy rises.
- Annotate proposals with the explicit (and inferred implicit) requirement they satisfy and verify resolution on a protected subset.

**Proposed concrete tasks (2026-11-28):**
1. Prototype a minimal claim-obligation certificate on the last five hard-bank failures and log detection of silent or contract-violating cases (paired with current gates).
2. Implement context folding for the last 10 autonomy proposals and measure token cost + hard-bank score versus current summarization (paired, non-production).
3. Add a held-out accuracy gate for macro-rule / pattern proposals and re-score the last three ledger entries under it.

**Question for operator:** Approve a controlled, non-production experiment that implements the claim-obligation certificate check and context-folding prototype on a frozen subset of the hard bank (no production code changes, no hard-bank modifications)? Yes / No / Modify.
