# Daily Self-Evolution Research Summary — 2026-11-20

Selected 5 strongest recent papers with empirical evidence on modular gated self-improvement, requirement-centered harness evolution, failure-type diagnosis for intervention choice, preservation-aware evaluation of evolved agents, and systemic validity gaps from multi-agent scaling. All applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Harnesses That Improve Themselves: A Unifying Framework for Self-Improving Agent Harnesses
https://arxiv.org/abs/2611.22299 (2026-11-17)

**Core claim + evidence:** Self-improving harnesses inspect traces, separate runtime bugs from model limits, and rewrite code. Framework pairs four editable components (context/state, agent control, action interfaces, verification/recovery) with diagnose-propose-validate-deploy loop. Modular gated updates generalize better and cost less than full rewrites or prompt reflection. Defenses against prompt bloat, benchmark gaming, and evaluator tampering. SWE-bench Lite shows gated modular evolution outperforms baselines across models and repositories at lower token cost.

**Concrete tasks for harness/autonomy:**
- Map gate_run.py surfaces and validators onto the four components; annotate editable vs frozen under current autonomy rules.
- Require every proposal to name target component and pass component-local validation plus protected-slice non-regression before ledger entry.
- Add a simple pre-admission filter for token bloat or protected-slice regression.

**Potential risks:** Over-strict modular gates may block useful cross-component fixes. Small validation slices can miss rare regressions. Defense heuristics may reject beneficial edits.

## 2. Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses (AHE-Beta)
https://arxiv.org/abs/2611.24924 (2026-11-18)

**Core claim + evidence:** Existing methods produce narrow patches by ignoring implicit requirements. AHE-Beta loop: simulated users raise requirements over multi-turn use, team implements generalizable changes, selection merges only on verified requirement resolution + review. Held-out pass@1 rises 21.9% to 33.3% with 40.8% fewer tokens; outperforms Claude Code, Meta-Harness, prior AHE. Human A/B prefers it in 31/48 pairs; gains transfer to GLM-5.3 and DeepSeek-V4.1-Flash.

**Concrete tasks for harness/autonomy:**
- Convert recent ledger entries and failure clusters into explicit requirement statements and score candidates against them.
- Require accepted edits to cite the requirement resolved and pass a short multi-turn review on a protected slice.
- Log requirement coverage remaining after each admission.

**Potential risks:** Simulated-user requirements may diverge from real operator needs. Team-style modification increases cost if not budgeted. Vague requirements enable gaming.

## 3. Harness Evolution Hits a Ceiling: When Weight Training Should Begin
https://arxiv.org/abs/2610.11655 (2026-10-08)

**Core claim + evidence:** Label failed trajectories by first firing signal to separate process failures (blocked calls, loops, exhausted budgets) from content failures (delivered but poor plan). Harness evolution repairs process failures; content failures need weight training. On DeepPlanning, self-evolving harness lifts Qwen3.5-4B held-out from 0.16 to 0.30 (delivery 55% to 90%). LoRA on evolved trajectories internalizes gains; adapters alone can match evolution on larger models. Diagnose-then-intervene rule: choose lever by failure composition, then decide which gains to train in.

**Concrete tasks for harness/autonomy:**
- Classify recent hard-bank failures as process vs content using first-signal or failure.md tags; prioritize harness edits only for process failures.
- Log the process/content split in the autonomy ledger for each cycle so future decisions remain visible.
- When process failures drop below a threshold, flag content-dominated failures for operator review rather than further harness search.

**Potential risks:** Misclassification of the first signal can send the wrong lever. On a frozen model the content ceiling is hard; over-focus on process may ignore solvable content issues via better verification. Transfer of the diagnostic may vary by task bank.

## 4. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher scores do not reliably imply better agents. Across four methods and sixteen evolved agents, every agent gained previously uncovered tasks while losing previously covered ones. Reliability can rise while coverage falls; most reliability gains also raise deployment cost. Motivates preservation-aware evaluation and EvoAudit revisions of select/analyze/mutate/gate stages.

**Concrete tasks for harness/autonomy:**
- For every accepted edit report newly solved and newly failed tasks on the protected hard-bank slice (coverage delta) in addition to aggregate score.
- Track deployment cost (tokens or latency) alongside accuracy in the ledger.
- Add a preservation check that rejects edits whose coverage loss exceeds a predefined threshold even if aggregate score rises.

**Potential risks:** Strict coverage preservation can block useful redistribution of capability. Cost tracking adds logging overhead. Small protected slices make coverage counts noisy.

## 5. From the Fluency Fallacy to the Micro-to-Macro Validity Gap: Opportunities and Pitfalls of LLMs in Social Simulation
https://arxiv.org/abs/2507.19364 (v4 2026-10-09; Frontiers 2026)

**Core claim + evidence:** Micro-level LLM limitations (hallucinations, stochastic inconsistency, biases, alignment effects) propagate, amplify, or contract into agent-level distortions (persona convergence) and macro-level risks (artificial consensus, behavioral homogenization). Evaluators face Fluency Fallacy and automation bias. Framework distinguishes exploratory/serious-game uses from confirmatory research. Hybrid theory-driven ABM architectures improve epistemic control but remain vulnerable to physics-washing.

**Concrete tasks for harness/autonomy:**
- Audit autonomy ledger and failure clusters for signs of fluent-but-unfaithful acceptance (high surface score, low deterministic gate agreement).
- Prefer deterministic evidence over model-as-judge for all admission decisions; log disagreement rate.
- When proposing multi-component or multi-turn changes, require an explicit check that the change does not amplify stochastic inconsistency on a protected slice.

**Potential risks:** Over-application of the validity-gap critique can freeze useful exploratory edits. Deterministic-only preference may miss tasks where model judgment is the only practical signal. Small slices under-power detection of homogenization.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, classify candidate failures as process vs content, declare the target component and the requirement addressed, then log coverage delta + cost delta before any admission decision (log only, no code change).
2. **For the operator:** Approve or reject adding a lightweight process/content tag and coverage-delta field to the autonomy ledger template.
3. **For the agent (after approval):** Draft a minimal modular validation checklist (component-local + protected non-regression + coverage preservation) as a standing autonomy rule proposal.

## Operator question

Do you approve piloting the process/content classification + modular component + coverage-delta logging on the next autonomy cycle (log only), and/or adding those fields to the ledger template?
