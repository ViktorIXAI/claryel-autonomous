# Daily Self-Evolution Research Summary — 2026-11-17

Selected 4 strongest recent papers with empirical or formal evidence on evolution side-effects, statistical governance of adoption, controlled false-evolution rates, and explicit harness invariants. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not automatically produce reliable, efficient, or transferable improvement. Across four methods, two harnesses and general/coding tasks, all sixteen evolved agents gained previously uncovered tasks while losing previously covered ones. Reliability can rise (e.g., +5.2 points) while covering fewer tasks; most reliability gains also increase deployment cost. Specific edits usually outperform generic reminders, but composition changes benefits. Stricter admission can discard useful alternatives; transfer selectively preserves gains. EvoAudit revises select/analyze/mutate/gate and obtains the best performance.

**Concrete tasks for harness/autonomy:**
- On every autonomy acceptance, record both newly covered and newly lost hard-bank tasks (coverage delta) alongside the reliability/score delta.
- Add a cost/energy column to the paired comparison so reliability gains that increase resource use are visible in the ledger.
- Pilot an EvoAudit-style review of the last N proposals that rewrites the select/analyze/mutate/gate steps and measures the effect on coverage preservation.

**Potential risks:** Over-weighting coverage preservation can block useful specialization. Cost accounting adds measurement overhead. Diagnostic replays increase evaluation budget.

## 2. Evidence-Governed Adoption of Self-Generated Updates in Autonomous AI Agents
https://arxiv.org/abs/2611.16378 (2026-11-12)

**Core claim + evidence:** A plausible self-generated modification is not automatically suitable for persistent adoption. EGE separates generation from confirmatory adoption, evaluates frozen candidates on fresh paired audits, requires meaningful improvement on a prespecified primary objective, protects declared capabilities via reference-relative non-inferiority tests, and applies governance constraints before bounded canary deployment. Provides evaluator-calibrated simultaneous lower bounds (Hoeffding + independent calibration), bridge tests for reference replacement, a cumulative degradation bound, and an audit-planning condition relating effect size, sample size and acceptance probability. Monte Carlo illustrates calibration under evaluator optimism (stylised, not a live agent).

**Concrete tasks for harness/autonomy:**
- Declare a primary objective and a protected-capability set for each autonomy cycle; require non-inferiority on the protected set before any admission.
- Evaluate frozen candidate harnesses on a fresh paired audit slice that was not used for proposal generation.
- Log the audit-planning parameters (margin, n, acceptance probability) in the ledger so later cycles can reuse or tighten them.

**Potential risks:** Fresh paired audits raise evaluation cost. Non-inferiority thresholds on small slices are noisy. Calibration assumes a valid reference evaluator; imperfect reference weakens the bound.

## 3. Trustworthy Recursive Self-Improvement with Statistical Guarantees
https://arxiv.org/abs/2611.10787 (2026-11-07)

**Core claim + evidence:** Greedy acceptance of higher validation scores can accept inferior updates (average 45.59 % on the tested settings) and lead to degeneration; overly conservative gates reject beneficial updates. TRUST adapts online multiple-hypothesis testing to control the rate of false evolution, letting an LLM use historical context to decide how much evidence is required. Under stated assumptions it limits the proportion of accepted updates that cause unacceptable loss and supplies a lower bound on final performance gain. On HotpotQA, DROP and APPS (DeepSeek-V4-Flash, Qwen-3.8-Flash) it reduces accepted inferior updates to 2.78 % while obtaining higher final scores than prior statistical gates.

**Concrete tasks for harness/autonomy:**
- Replace or augment the current acceptance rule with a simple false-evolution control that tracks the running proportion of accepted updates later shown to be inferior on a protected slice.
- Let the proposer state a required evidence level (sample size or confidence) based on recent ledger history before a candidate is admitted.
- Record for each admission whether it later proved inferior; feed the rate back into the next cycle’s evidence requirement.

**Potential risks:** Online multiple-testing procedures can become overly conservative on small paired sets. Historical-context LLM decisions add another failure surface. Assumptions (bounded scores, valid testing) must hold for the guarantees.

## 4. Anatomy of an Agent Harness: Decisions, Invariants and Corner Cases
https://arxiv.org/abs/2611.19960 (2026-11-15)

**Core claim + evidence:** Most harness decisions are made in code and rarely written down, so the same corner cases recur. The paper supplies a system model with trust boundaries, 30 decision cards (six groups) each containing options, costs, an invariant, breaking corner cases, a test and an evidence tag, six failure cause classes, a test method using scripted providers and planted changes, and a checklist. Of 83 invariant clauses, 56 are tagged Tested. Applied to the author’s own harness the checklist shows 11 hold / 14 do not / 5 untested. No ranking or quality claims are made.

**Concrete tasks for harness/autonomy:**
- Map the current gate_run.py decision points onto the paper’s six groups and flag any missing invariants that affect our hard-bank or telemetry guarantees.
- Add one explicit invariant + test (e.g., “fresh paired audit is independent of proposal data”) to the autonomy ledger acceptance checklist.
- Use the planted-change test method on a synthetic failure to verify that our current fixer/validator detects the planted regression.

**Potential risks:** The catalogue is derived from one desktop harness plus open-source references and is not independent. Checklist application by a single builder can be biased. Implementing many new tests increases maintenance cost.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record both coverage delta (newly solved / newly lost hard-bank tasks) and resource-cost delta alongside the primary score, and log the result only (no production code change).
2. **For the operator:** Approve or reject adding a protected-capability non-inferiority check and a fresh-paired-audit requirement to the autonomy acceptance rule for the next candidate.
3. **For the agent (after approval):** Draft a minimal false-evolution tracker that records whether each accepted update later fails a protected slice, and propose an evidence-level adjustment for the following cycle.

## Operator question

Do you approve piloting the coverage-and-cost delta logging plus a protected-capability non-inferiority check on the next autonomy cycle, or should we start with only the coverage-and-cost logging?
