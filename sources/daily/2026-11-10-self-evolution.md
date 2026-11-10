# Daily Self-Evolution Research Summary — 2026-11-10

Selected 4 strongest recent papers with empirical or theoretical relevance to frozen-model harness evolution, verification, repair, and cross-domain influences. Focus on statistical reliability of admission, adaptive overfitting on fixed evaluation sets, allocation of capability between solver and evolver, and cognitive/systems effects of memory on long-horizon search.

## 1. Trustworthy Recursive Self-Improvement with Statistical Guarantees
https://arxiv.org/abs/2611.10787 (2026-11-07)

**Core claim + evidence:** Greedy acceptance of harness updates based on higher validation scores produces high rates of inferior updates (mean 45.59% across settings). TRUST adapts online multiple hypothesis testing (FER control) with LLM-guided error-budget allocation, noninferiority tolerance, and overlap correction. On HotpotQA, DROP, and APPS with DeepSeek-V4-Flash and Qwen-3.8-Flash, it reduces the ratio of accepted inferior updates to 2.78% while achieving higher final gains than statistical baselines and the greedy gate. Includes theoretical FER control and a lower bound on deployment gain under stated assumptions.

**Concrete tasks for harness/autonomy:**
- Prototype a non-greedy admission rule that requires a statistical threshold (or simple paired significance) before logging an autonomy proposal as accepted; record the estimated false-evolution rate or equivalent metric in the ledger.
- Add an overlap-correction or fresh-sample requirement when reusing the same hard-bank subset for successive proposals.
- Log the loss-tolerance parameter and error-budget allocation decision alongside every acceptance/rejection.

**Potential risks:** Overly conservative thresholds can stall useful evolution. Requires reliable paired telemetry that may increase evaluation cost. Assumptions (e.g., valid e-values) may not hold exactly on our fixed task bank.

## 2. Which Self-Improvements Should We Trust? Reliable Self-Improvement When Agents Reuse Their Benchmarks
https://arxiv.org/abs/2609.33180 (2026-09-29)

**Core claim + evidence:** When a fixed evaluation set is reused for adaptive candidate generation, empirical gains can overfit the search trajectory and fail to reflect genuine population improvement. REUSE provides statistical guarantees (probability at least 1-α that every promoted modification is a true population improvement) by strictly limiting feedback returned to the proposer and accounting for promotion history in the error budget. In live experiments it reduced the proportion of false promotions from up to 20.7% to 0% while matching the best baselines on true population performance.

**Concrete tasks for harness/autonomy:**
- Restrict the information returned to the proposer in autonomy cycles to a minimal sufficient statistic (e.g., binary accept/reject + aggregate delta) rather than full per-task outcomes, and measure the effect on subsequent proposal quality.
- Add a promotion-history counter to the autonomy ledger so that successive proposals on the same hard-bank subset are discounted or subjected to a higher evidence bar.
- Define a small sealed hold-out subset of the hard bank that is never shown to the proposer and is used only for final confirmation of accepted changes.

**Potential risks:** Severely limiting feedback may reduce the quality of subsequent proposals. Implementing certified bounds adds complexity and may reject useful changes under our small evaluation budgets.

## 3. Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents
https://arxiv.org/abs/2605.30621 (revised 2026-11-04)

**Core claim + evidence:** Harness-updating capability (producing useful persistent updates from evidence) is largely flat across model capability tiers—even Qwen3.5-9B updates yield gains comparable to stronger models. Harness-benefit (actually improving task solving by using the updated harness) is non-monotonic: weak models benefit little, mid-tier models benefit most, strong models benefit less. Low weak-tier gains are traced to failure to activate or faithfully follow harness artifacts. Recommendation: allocate capability budget to the task-solving agent rather than the evolver.

**Concrete tasks for harness/autonomy:**
- Instrument the autonomy process to log whether a proposed harness change was activated and followed on subsequent runs (activation rate, instruction-following fidelity).
- Prefer using the strongest available local model for the solver role while keeping a lighter model for proposal generation, and measure the resulting hard-bank delta.
- Add an activation-check gate that rejects or flags proposals whose artifacts are not invoked in at least a minimum fraction of relevant traces.

**Potential risks:** Separating solver and evolver models increases operational complexity and cost. Activation metrics may be noisy if traces are incomplete. May undervalue evolver improvements that only appear after several cycles.

## 4. Scaling Discovery Requires Forgetting
https://arxiv.org/abs/2610.20563 (2026-10-14) — cognitive science / systems influence

**Core claim + evidence:** Long-running LLM agent search (sequential, parallel, or communicating) plateaus because agents become anchored to accumulated history, producing fewer and smaller edits. Periodically discarding every agent’s session and candidate history while restarting from the best candidate found so far unblocks search. On four tasks (heuristic programming, kernel optimization, model training) a team of four that forgets improves up to 15% over parallel agents and 39% over a single agent at matched budget.

**Concrete tasks for harness/autonomy:**
- Introduce a periodic context-reset step in long autonomy cycles: after N proposals, clear intermediate reasoning traces while retaining only the best-scoring harness version and its paired evidence, then continue.
- Log edit size and proposal diversity before/after reset points to quantify anchoring.
- Test a lightweight “forget” variant on a frozen hard-bank subset and compare coverage and cost against the continuous sequential process.

**Potential risks:** Discarding history loses useful intermediate insights and may require re-discovery. Reset frequency must be tuned; too frequent resets waste prior work. May interact poorly with forgetting metrics already tracked from continual-evolution studies.

## Proposed concrete tasks (1-3)

1. **For the agent:** Add a minimal statistical or paired-significance check (and a promotion-history counter) to the next autonomy cycle’s ledger entries only — no production code change. Report the fraction of recent proposals that would have been rejected under a simple non-greedy rule and the estimated overlap risk on the hard-bank subset used.
2. **For the operator:** Approve or reject defining a small sealed hold-out slice of the hard bank (never shown to the proposer) for final confirmation of accepted autonomy changes.
3. **For the agent (after approval):** Draft a short design note for a periodic context-reset experiment based on paper 4, specifying reset interval, retained artifacts, and the exact metrics (edit size, coverage delta, cost) that will be logged.

## Operator question

Do you approve defining a sealed hold-out subset of the hard bank (used only for confirmation, never returned to the proposer) and requiring it for future autonomy admissions, or should we first run a one-cycle pilot that only logs promotion history and simple paired significance without blocking any proposals?
