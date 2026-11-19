# Daily Self-Evolution Research Summary — 2026-11-19

Selected 5 strongest recent papers with empirical evidence on requirement-centered harness evolution, modular gated self-improvement, practical self-evolving memory, statistical control of false updates, and documented reliability/cost trade-offs. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses (AHE-Beta)
https://arxiv.org/abs/2611.24924 (2026-11-18)

**Core claim + evidence:** Existing evolution often produces narrow benchmark-specific patches by ignoring implicit user requirements. AHE-Beta uses a requirement-centered loop: simulated users raise issues over multi-turn interaction, a team implements generalizable changes, and selection merges only when a verified requirement is resolved and review passes. On held-out tasks, pass@1 rises from 21.9% to 33.3% with 40.8% fewer tokens than Base Harness, outperforming Claude Code, Meta-Harness, and prior AHE. Blind human A/B tests show preference in 31/48 pairs and higher ratings on all five dimensions; gains transfer to GLM-5.3 and DeepSeek-V4.1-Flash without further evolution.

**Concrete tasks for harness/autonomy:**
- Extract recent autonomy ledger entries and failure.md clusters into explicit requirement statements (explicit + inferred interaction needs) and score candidate patches against them rather than raw score only.
- Require every accepted harness edit to cite the requirement it resolves and to pass a short multi-turn interaction review on a protected slice before ledger admission.
- Log requirement coverage (how many open requirements remain after the edit) alongside the paired hard-bank delta.

**Potential risks:** Simulated-user requirements may diverge from real operator needs. Team-based modification increases token cost if not carefully budgeted. Requirement statements can become vague and allow gaming.

## 2. Harnesses That Improve Themselves: A Unifying Framework for Self-Improving Agent Harnesses
https://arxiv.org/abs/2611.22299 (2026-11-17)

**Core claim + evidence:** Pairs four editable runtime components (context/state, agent control, action interfaces, verification/recovery) with a diagnose-propose-validate-deploy loop. Modular gated updates generalize better and cost less than full rewrites or pure prompt reflection. Defenses against prompt bloat, benchmark gaming, and evaluator tampering. SWE-bench Lite experiments show gated modular evolution outperforms baselines across models and repositories at lower token cost.

**Concrete tasks for harness/autonomy:**
- Map current surfaces in gate_run.py and related modules onto the four components; annotate which are currently editable under autonomy rules.
- Force every proposal to name its target component and to pass a component-local validation plus a small cross-component protected regression check.
- Add a lightweight bloat/gaming detector (token growth or protected-slice regression) as a pre-admission filter.

**Potential risks:** Over-strict modular gates may miss beneficial cross-component changes. Defense heuristics can reject useful edits. Validation slices that are too small miss rare regressions.

## 3. ARISE: Practical Self-Evolving Memory for Accurate and Cost-Efficient Enterprise Agents
https://arxiv.org/abs/2611.23588 (2026-11-17)

**Core claim + evidence:** Memory evolves from the agent's own failures without changing weights, tools, or workflow logic. Failures are attributed (self or teacher), corrections stored as micro-memory, consolidated into macro rules, and a rule is accepted only if held-out accuracy rises. Across 14 domains on SOP-Bench and τ²-bench with 5 models, ARISE-Teacher gains 10.9 pp and 5.8 pp respectively while using fewer model calls and tokens; ARISE-Self still gains 10.0 pp on SOP-Bench.

**Concrete tasks for harness/autonomy:**
- Convert recent recurring failure clusters into candidate micro-corrections and test consolidation into a macro rule only if a held-out hard-bank slice improves.
- Maintain a small retrievable micro-memory store that is consulted before retry; log hit rate and accuracy delta.
- Prefer self-attribution first, with optional teacher fallback, and record which path produced the accepted rule.

**Potential risks:** Held-out slices that are too small can admit rules that later regress. Consolidation can over-generalize and introduce bloat. Teacher attribution adds cost and external dependency.

## 4. Trustworthy Recursive Self-Improvement with Statistical Guarantees (TRUST)
https://arxiv.org/abs/2611.10787 (2026-11-07)

**Core claim + evidence:** Greedy acceptance of higher validation scores admits many inferior updates (45.59% on average). TRUST adapts online multiple-hypothesis testing, using an LLM on historical context to set evidence thresholds, to control the rate of false evolution. Under stated assumptions it bounds the proportion of accepted updates that cause unacceptable loss and provides a lower bound on final gain. On HotpotQA, DROP, and APPS it reduces inferior accepted updates to 2.78% while matching or exceeding stronger statistical baselines.

**Concrete tasks for harness/autonomy:**
- Replace or augment the current score-delta admission rule with a simple statistical threshold that requires the observed gain to exceed a historically estimated noise floor before ledger acceptance.
- Log the estimated false-evolution rate and the evidence threshold used for each decision.
- Pilot on a fixed subset of hard-bank slices and compare number of admitted regressions versus the existing paired-evidence rule.

**Potential risks:** Overly conservative thresholds can stall useful improvement. Historical context used by the LLM can itself be gamed or drift. Assumptions may not hold on small or non-stationary hard-bank slices.

## 5. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not reliably imply better agents. Across four methods and sixteen evolved agents, every agent gained previously uncovered tasks while losing previously covered ones. Reliability can rise while coverage falls; most reliability gains also increase deployment cost. The work motivates preservation-aware evaluation and EvoAudit-style revisions of the select/analyze/mutate/gate stages.

**Concrete tasks for harness/autonomy:**
- For every accepted edit, report both newly solved and newly failed tasks on the protected hard-bank slice (coverage delta) in addition to aggregate score.
- Track deployment cost (tokens or latency) alongside accuracy so cost increases are visible in the ledger.
- Add a simple preservation check that rejects edits whose coverage loss exceeds a predefined threshold even if aggregate score rises.

**Potential risks:** Strict coverage preservation can block useful redistribution of capability. Cost tracking adds logging overhead. Small protected slices make coverage counts noisy.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, require every candidate to declare the requirement it addresses and the component it targets, then apply a modular validation + protected-slice non-regression + coverage-delta log before any admission decision (log only).
2. **For the operator:** Approve or reject a small pilot that converts the top three recurring failure clusters into ARISE-style micro-memory candidates and tests consolidation only on held-out slices.
3. **For the agent (after approval):** Draft a minimal statistical admission filter (gain must exceed estimated run-to-run noise) and a coverage-preservation rule, both as checklist items in the autonomy ledger template.

## Operator question

Do you approve piloting the requirement-declaration + modular component gate + coverage-delta logging on the next autonomy cycle, and/or a small ARISE-style micro-memory consolidation experiment on recent failure clusters?
