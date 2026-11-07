# Daily Research Summary: 2026-11-07

## Selected Papers

### 1. ParetoSaddler: Pareto-Guided Optimization of Agent Harnesses for Quality and Cost (arXiv:2611.02079, 2026-11-01)
**Core claim + evidence:** Joint quality-cost harness optimization is possible by separating intermediate candidate promotion (Bayesian bootstrap Pareto support on either dimension) from final deployment selection. On ClawMark quality rose 70.86% → 81.35% while cost fell $1.17 → $1.01 per task; on GAIA2 quality 56.22% → 62.89% and cost $0.78 → $0.45. Pareto-aware search retained useful intermediates that pure quality or pure cost filters would discard. Empirical repeated executions + domain-disjoint splits.

**Concrete tasks for harness:**
- Add energy/latency/token cost as an explicit second objective in autonomy acceptance; promote candidates that credibly improve either quality or cost on paired runs.
- Use bootstrap-style confidence on paired deltas before accepting a version.
- Maintain a short parent pool of non-dominated harness variants for later search.

**Potential risks:** Intermediate promotion can temporarily accept higher-cost versions; bootstrap threshold may be too strict on small paired sets; added evaluation cost.

### 2. Harness Updating Is Not Harness Benefit: Disentangling Evolution Capabilities in Self-Evolving LLM Agents (arXiv:2605.30621, 2026-11-04)
**Core claim + evidence:** Harness-updating capability (producing useful persistent updates) is largely flat across model capability tiers; even a 9B evolver can match stronger models. Harness-benefit is non-monotonic: mid-tier models gain most, weak models often fail to activate or adhere to the updated harness, strong models are already near ceiling. Controlled cross-pairing of 7 models as agents vs evolvers on three agentic benchmarks.

**Concrete tasks for harness:**
- Measure activation rate (does the solver load the relevant gate/fixer/validator?) and adherence rate on recent hard-bank runs.
- Prefer allocating stronger local capacity to the solver role; keep the evolver/proposal role lightweight or on a separate frozen model.
- Add an explicit "harness invocation" check in the autonomy ledger.

**Potential risks:** Over-separating roles may lose the single-model simplicity of the current process; activation metrics need careful definition to avoid false negatives.

### 3. The Two-Ledger Model: Transaction-Grain Cost Accounting for Multi-Agent AI Systems (arXiv:2611.06989, 2026-11-04)
**Core claim + evidence:** Settlement-grain billing cannot answer per-transaction (or per-task) AI cost. Proposes an attribution ledger of invocation-grain telemetry joined to a FOCUS-conformant settlement ledger via a correlation spine (trace, metadata, business key, probabilistic match). Simulation shows >99% cost coverage, residual recovery of unmetered spend within 0.24 pp, and mid-flight gating reducing p99 cost up to 61%. Ties directly to resource accounting and economic evaluation.

**Concrete tasks for harness:**
- Extend existing telemetry join to produce per-attempt cost records that can be reconciled against any external billing later.
- Add a simple residual check: flag runs where measured energy/token usage diverges from expected by more than a threshold.
- Log cost at task-grain in the autonomy ledger so economic comparisons remain paired.

**Potential risks:** Over-engineering the accounting spine before basic energy logging is stable; false residual flags on noisy sensors.

### 4. Beneath the Surface: What We Overlook When We Talk About Agent Evolution (arXiv:2611.07624, 2026-11-05) — continued focus
**Core claim + evidence:** (Recap from prior day) All 16 evolved agents gained new tasks while losing previously covered ones; reliability gains often raised deployment cost; transfer is selective. Motivates preservation-aware evaluation and tested decision rules. EvoAudit-style diagnostics improved results.

**Concrete tasks for harness:**
- Quantify coverage gain vs coverage loss on every autonomy version using the existing hard bank + holdout.
- Require explicit applicability conditions (which task families the change targets) in proposal logs.

**Potential risks:** Protected-case sets can freeze useful evolution if not periodically refreshed.

## Proposed Tasks
1. Retroactively compute paired quality and cost deltas for the last three autonomy versions and mark any non-dominated candidates that were previously rejected solely on quality.
2. Add a lightweight activation/adherence probe to the next hard-bank smoke run (does the model load the intended fixer/validator?).
3. Extend the autonomy ledger schema with a cost field (energy or token) and a residual flag for the next evaluation cycle.

## Operator Question
Do you approve making cost (measured energy or token count) a first-class paired acceptance criterion alongside quality, with intermediate Pareto promotion allowed, before any further autonomous harness edits? This aligns with the Pareto and Two-Ledger findings but requires a clear cost budget definition.

All additions preserve English, practical style, and measurable harness changes. No production code or hard bank modified.
