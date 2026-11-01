# Related work

Verified 2026-11-01. This lab is small; we cite the published literature that
defines the evaluation standards we are measured against, and state honestly
which of their demands we now meet and which we do not.

| work | what it establishes | our status against it |
|---|---|---|
| Harness-Bench: Evaluating Agent Harnesses across Models and Realistic Workflows — [arXiv:2605.27922](https://arxiv.org/abs/2605.27922) | harness effects must be reported at the model–harness configuration level; realistic oracle-checked tasks, full traces | we report per (box, contour, engine) tuples and ship raw traces; our tasks are synthetic, not realistic-workflow — named gap |
| Rethinking the Evaluation of Harness Evolution for Agents — [arXiv:2607.12227](https://arxiv.org/abs/2607.12227) | harness-evolution gains must be tested on held-out tasks and against budget-matched simple baselines (test-time scaling, self-consistency) | holdout bank exists and is post-freeze (0.819 pilot, G-gap published); budget-matched simple baselines **not yet run** — top roadmap item |
| Holistic Agent Leaderboard (HAL), ICLR 2026 — [arXiv:2510.11977](https://arxiv.org/abs/2510.11977) | standardized harness, model×scaffold×benchmark analysis, cost-aware Pareto reporting, public logs | we publish all raw logs + token/cost ledger fields; single model family so far — named gap |
| HarnessOpt-Bench: Evaluating LLMs at Harness Optimization — [arXiv:2608.06301](https://arxiv.org/abs/2608.06301) | harness optimization as a measurable capability; hidden test partition enforced by a trusted execution environment | our holdout separation is procedural (CI disjointness check), not an enforced TEE — limitation stated |
| Meta-Harness — [arXiv:2603.28052](https://arxiv.org/abs/2603.28052) | search over harness code from prior source + scores + traces | our loop is close to this pattern, but manual-decision-gated: every version ships with a written accept/reject record |
| Agentic Harness Engineering — [arXiv:2604.25850](https://arxiv.org/abs/2604.25850) | observability-driven evolution of prompts, tools, middleware, memory | our observability is the gate ledger + telemetry join; middleware evolution is exactly our contour line |

The 2026-11-01 external review
([`results/external-review-2026-11-01.md`](../results/external-review-2026-11-01.md))
pointed at the same literature independently; its criticisms map to the
"not yet" cells above, which is why they are roadmap commitments rather than
prose.
