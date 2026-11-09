# Daily Self-Evolution Research Summary — 2026-11-09

Selected 4 strongest recent papers with empirical or theoretical relevance to frozen-model harness evolution, verification, repair, and cross-domain influences. Focus on reliability, coverage trade-offs, forgetting, long-horizon adaptation, and safety of agent-directed change.

## 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not reliably indicate practical improvement. Across 16 evolved agents (4 methods × harnesses/tasks), every agent gained previously uncovered tasks while losing previously covered ones. Example: reliability +5.2 points while losing 10 covered tasks. Most gains increase deployment cost. Highest-scoring agent is not the best further improver; stricter admission can discard useful variants. EvoAudit/AGE revises select/analyze/mutate/gate and outperforms baselines. Code: RSIHub.

**Concrete tasks for harness/autonomy:**
- Add paired coverage tracking to autonomy ledger: for every accepted change, log tasks gained vs tasks lost on hard-bank subset, not just aggregate score.
- Introduce a preservation-aware gate that rejects proposals if any protected cases regress, even if mean score rises.
- Measure and log deployment cost (tokens/energy) delta for each candidate before admission.
- Pilot EvoAudit-style diagnostics on recent ledger entries: replay admission decisions and flag discarded alternatives that later proved useful.

**Potential risks:** Over-strict preservation can stall useful evolution. Cost accounting may favor cheap but brittle changes. Requires reliable task-level telemetry that is currently incomplete.

## 2. Can Coding Agents Sustain Continual Evolution without Forgetting?
https://arxiv.org/abs/2611.03219 (2026-11-02)

**Core claim + evidence:** Continual harness evolution across sequential task datasets produces catastrophic forgetting. With DeepSeek-V4-Flash and Meta-Harness, SWE-Bench rose to 94% then fell to 32% after further evolution on FeatureBench (66% relative drop). Patterns observed across six evolution directions and two methods.

**Concrete tasks for harness/autonomy:**
- Maintain a fixed regression suite of prior hard-bank tasks that must be re-evaluated after every evolution step on a new task family.
- Add a forgetting metric to the autonomy ledger (performance delta on previous task clusters).
- Experiment with rehearsal or modular isolation (task-specific harness overlays) before accepting cross-task mutations.

**Potential risks:** Full regression suites increase evaluation cost. Modular isolation may reduce beneficial transfer. False positives if task distributions shift naturally.

## 3. BOXBOX: Recursive Harness Self-Improvement for Long-Running Performance Optimization
https://arxiv.org/abs/2611.09218 (2026-11-06)

**Core claim + evidence:** Offline harness optimization is insufficient for open-ended long-running tasks. BOXBOX allows agent-triggered harness revision with kernel-managed hot reloading while preserving execution context. On PerfRace benchmark under matched budgets, Speedup@4h = 1.70× vs 1.54× for strongest baseline (Frozen / offline evolution / scaling).

**Concrete tasks for harness/autonomy:**
- Prototype a hot-reloadable module interface for non-critical harness components (e.g., retry policy, telemetry filters) that can be swapped mid-run without full restart.
- Log mid-run revision proposals and their measured effect on remaining task progress in the autonomy ledger.
- Define safe boundaries: only allow hot-reload on components whose interfaces are frozen and whose failure modes are already covered by existing gates.

**Potential risks:** Hot reload can introduce state inconsistency or security issues if not strictly sandboxed. Long-running evaluation is expensive. Context preservation bugs may silently corrupt later evidence.

## 4. Adapting the Process of Adaptation: Darwinian, Lamarckian, and Agent-Directed Evolution in AI
https://arxiv.org/abs/2611.07048 (2026-11-04) — macroeconomics / systems influence (Andrew Lo)

**Core claim + evidence:** Theoretical comparison of Darwinian, Lamarckian, and agent-directed evolution. When learning is effective, agent-directed search adapts faster, but misspecified evaluation targets cause accelerated convergence to the wrong behavior. Errors can persist across recursive generations. Independent oversight must keep pace.

**Concrete tasks for harness/autonomy:**
- Explicitly document the evaluation target (hard-bank metrics, cost, preservation) in every autonomy proposal and require a misspecification check.
- Add an independent critic gate (separate from the proposing agent) that re-evaluates accepted changes against the stated objective before final commit.
- Track whether search effort is increasing while protected metrics degrade — treat as possible misspecification signal.

**Potential risks:** Extra critic layer adds latency and cost. Over-reliance on theoretical framing without empirical calibration. May slow useful evolution if applied too rigidly.

## Proposed concrete tasks (1-3)

1. **For the agent:** Implement a minimal paired coverage + cost logger in the next autonomy cycle (no code change to production gates yet — only telemetry and ledger entries). Report gained/lost tasks and token delta for the last 5 proposals.
2. **For the operator:** Approve or reject adding a fixed prior-task regression suite (subset of hard bank) that must be re-run after any cross-task evolution experiment.
3. **For the agent (after approval):** Draft a short design note for a preservation-aware admission gate based on paper 1, including the exact metrics and protected-case definition that would be used.

## Operator question

Do you approve creating a protected regression suite (selected hard-bank tasks that must never regress) and requiring it for future autonomy admissions, or should we first run a one-cycle pilot that only logs coverage changes without blocking proposals?
