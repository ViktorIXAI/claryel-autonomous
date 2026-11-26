# Daily Research Summary — 2026-11-26

Selected four recent papers with strong empirical grounding and direct applicability to frozen-model harnesses that use paired evidence and an autonomy ledger.

### Demystifying the Autoresearch Harness (arXiv:2611.28244)
Core claim: Context folding (individually accessible past-attempt records) outperforms rolling summaries; selective deletion of unused lessons outperforms consolidation. Combined system reaches 72.7% medal rate on MLE-Bench Lite and 94% fast₁ on KernelBench Level 3 under fixed budget.
Evidence: Isolation experiments across three models and two benchmarks vs recency-truncation baseline.
Concrete tasks: Add context-folding option for telemetry/run records in the autonomy ledger; implement unused-lesson deletion gate measured by paired hard-bank conversion.
Risks: Context bloat and latency; loss of rare high-value repairs.

### Evolve Where It Matters: Coverage-Guided Self-Evolution (arXiv:2611.25429)
Core claim: Instruction-level coverage (follow / not-follow / not-covered) enables targeted skill revision and yields +25.6–30.4 pp over initial skill and +8.7–14.0 pp over strongest baseline.
Evidence: Three benchmarks, three executors; ablation shows coverage removal drops recovered failures 20.8%.
Concrete tasks: Annotate gate_run.py traces with coverage labels; generate one coverage-targeted repair per major failure cluster with paired validation.
Risks: Labeling overhead; spurious revisions that pass local checks.

### Blind to What They Can Fix (arXiv:2611.29807)
Core claim: Self-improving agents write runtime checks that stay silent on ≥50% of environment-shift failures even when the agents can repair those failures once surfaced.
Evidence: Five domains, up to seven models; monitor built from normal runs catches most failures.
Concrete tasks: Add detection-rate metric to autonomy ledger; pilot normal-run monitor that flags deviations before repair proposals.
Risks: False positives and extra cost; possible weakening of primary gates.

### How Feedback-Free Self-Evolution Reshapes Agent Skills (arXiv:2611.25534)
Core claim: Feedback-free rewriting degrades every model on every benchmark (avg −15 points on SkillsBench after 30 rounds) by pulling skills toward the model prior.
Evidence: Systematic multi-model multi-benchmark study; SkillDiff recovers +4.8 points by marking external knowledge.
Concrete tasks: Forbid pure self-rewrite of autonomy rules without paired evidence; add prior-divergence check on proposed rules.
Risks: Over-strict checks can freeze useful adaptation.

**Proposed concrete tasks (2026-11-26):**
1. Measure detection rate (surfaced vs silent failures) on last 50 hard-bank failures and log in autonomy ledger.
2. Prototype context folding for last 10 autonomy proposals and compare proposal quality under paired seeds.
3. Add coverage-label step to one failure cluster and generate a single targeted repair proposal for operator review.

**Question for operator:** Approve a controlled, non-production experiment that (a) measures the detection gap on a frozen hard-bank subset and (b) tests context folding versus current ledger summarization, with all results recorded as paired evidence and no changes to production code or the hard bank? Yes / No / Modify.
