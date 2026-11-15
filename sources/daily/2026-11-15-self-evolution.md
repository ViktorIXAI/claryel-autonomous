# Daily Self-Evolution Research Summary — 2026-11-15

Selected 4 strongest recent papers with empirical evidence on reliability-vs-coverage trade-offs in harness evolution, separation of powers for autonomous program evolution, executable finite-state control for long-horizon procedure fidelity, and catastrophic forgetting under continual multi-task evolution. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not automatically yield reliable, efficient, or transferable improvement. Across four methods (AHE, HyperAgents, A-Evolve, GEPA) on MiniSWE and Codex harnesses, all 16 evolved agents gained previously uncovered tasks while losing previously covered ones. In one general-task case reliability rose 5.2 points while losing ten previously covered tasks. Most reliability gains increased deployment cost. Specific changes usually outperformed generic reminders, but benefits changed when combined. The highest-scoring agent did not yield the largest mean improvement; stricter admission discarded useful alternatives. Transfer was selective. EvoAudit/AGE revisions of select/analyze/mutate/gate improved outcomes. Code: https://github.com/simple-agent-lab/RSIHub

**Concrete tasks for harness/autonomy:**
- In every autonomy ledger entry, report both reliability (Avg@k on paired runs) and coverage (Pass@k / tasks solved at least once), plus explicit regressions (previously solved tasks now failed).
- Record energy/token/latency cost deltas alongside quality deltas; reject or flag changes whose cost increase exceeds a paired threshold even if quality rises.
- Maintain a small archive of rejected-but-promising candidates so later cycles can re-evaluate them under different admission rules.

**Potential risks:** Over-emphasizing coverage preservation can block useful specialization. Cost telemetry variance is higher than quality scores. Re-evaluating rejected candidates increases evaluation budget.

## 2. Where Autonomy Belongs: A Separation of Powers for Agentic Program Evolution (EvoTrias)
https://arxiv.org/abs/2611.15309 (2026-11-11)

**Core claim + evidence:** LLM-driven program evolution rests on three decisions—govern (direct search from accumulated evidence), propose (construct next candidate), and judge (settle validity and fitness). Misallocating autonomy across them produces failures. EvoTrias assigns one owner each: Structured Governance for cross-round decisions, Open Proposal for intra-task construction, Protected Judgment behind a private evaluator. Owners exchange only typed contracts; runtime hooks enforce boundaries. Separating Governance from Proposal cut token cost 64%; Protected Judgment kept scores faithful to transfer. New SOTA on mathematical, systems, and algorithm-design benchmarks. Can run as a plugin on existing coding agents.

**Concrete tasks for harness/autonomy:**
- Explicitly label each autonomy ledger decision as Govern, Propose, or Judge and record which component owns it.
- Pilot a protected-judgment path that evaluates candidate harness edits with a context-isolated critic or deterministic checker before admission.
- Measure token cost of the proposal step versus the governance step on the next cycle to quantify the benefit of separation.

**Potential risks:** Strict separation can increase latency or coordination overhead. Protected judgment requires a reliable independent evaluator; shared-context critics may leak information. Plugin integration may not map cleanly to the current gate_run.py structure.

## 3. Keeping LLM Agents on Procedure: Executable Finite-State Control for Long-Horizon Instruction Fidelity
https://arxiv.org/abs/2611.10884 (2026-11-07)

**Core claim + evidence:** Agents drift from stated procedures over long unattended runs; restating instructions or resuming only moves the drift. An executable finite-state machine (FSM) keeps workflow state outside the model context and enforces it at tool calls, state transitions, and end of turn. On 200-account SOP-Bench batches, Claude Haiku 4.5 + FSM decided 139 accounts correctly and by procedure vs 48 for the strongest baseline (95% CI [46, 130]) and maintained the rate to the end. Across three models the gain tracked baseline drift. Small models with FSM outperformed larger models without it at lower cost. Analyses on SWE-bench Verified, τ^{2}-bench, and staged workflows support stronger execution control over stronger models alone.

**Concrete tasks for harness/autonomy:**
- Identify the longest multi-step procedures in the current hard bank or autonomy loop and sketch a minimal external FSM that enforces their critical transitions.
- Add a post-hoc check in the ledger that flags runs whose observed tool-call sequence violated a declared procedure state machine.
- Pilot an external state tracker for one category of tasks (e.g., multi-turn repair sequences) and measure procedure adherence rate versus baseline.

**Potential risks:** Rigid FSM can reject valid alternative paths. Specifying the full procedure state machine requires operator input or careful mining from traces. Enforcement overhead may increase latency on short tasks.

## 4. Can Coding Agents Sustain Continual Evolution without Forgetting?
https://arxiv.org/abs/2611.03219 (2026-11-02)

**Core claim + evidence:** Continual harness self-evolution across multiple task types produces catastrophic forgetting. With DeepSeek-V4-Flash-0731, Meta-Harness reached 94.0% on SWE-Bench after evolution, but after further evolution on FeatureBench the SWE-Bench score fell to 32.0% by the fifth round (66% relative decrease). Two methods were tested across six evolution directions on three SE datasets. Insights point to the need for retention mechanisms.

**Concrete tasks for harness/autonomy:**
- Require every new evolution round to report paired deltas on both the new task slice and a fixed protected subset drawn from earlier hard-bank categories.
- Flag (without blocking) any accepted change whose paired score on prior categories drops more than a pre-set threshold (e.g., 2 pp).
- Experiment with mixed batches that interleave old and new task types rather than pure sequential specialization.

**Potential risks:** Over-protection prevents useful specialization. Mixed-batch evaluation increases cost. Thresholds on small paired slices are noisy.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record both reliability (Avg@k) and coverage (tasks solved at least once) plus explicit regressions of previously solved tasks, together with cost deltas from telemetry. Log only; no production code change.
2. **For the operator:** Approve or reject adding explicit Govern / Propose / Judge labels to the next autonomy ledger entries and piloting a simple protected-judgment (context-isolated) check on one candidate harness edit.
3. **For the agent (after approval):** Draft the minimal external state-machine sketch for one multi-step procedure currently handled inside gate_run.py and list the ledger fields needed to track procedure-adherence violations.

## Operator question

Do you approve piloting the dual reliability/coverage + regression logging (plus cost deltas) on the next autonomy cycle, and simultaneously labeling decisions as Govern/Propose/Judge with a non-blocking protected-judgment check, or should we start with only the reliability/coverage logging?
