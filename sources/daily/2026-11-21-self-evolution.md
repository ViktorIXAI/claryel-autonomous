# Daily Self-Evolution Research Summary — 2026-11-21

Selected 4 strongest recent papers with empirical evidence on coverage-guided skill evolution, harness evolution as a complement to weight updates, evaluation-free recursive self-improvement, and the role of evaluation resolution in evolution success. All applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Evolve Where It Matters: Coverage-Guided Self-Evolution of Agent Skills
https://arxiv.org/abs/2611.25429 (2026-11-19)

**Core claim + evidence:** Self-evolving agents revise skills from runs, but outcome-level or failure-location signals cannot distinguish wrong instructions from unfollowed instructions. Instruction-level coverage (follow / not-follow / not covered) separates the causes. SkillPlumber uses coverage to target evolution, with a persistent root-cause agent that turns labels into revision questions, validates against the next run, and a maintainer that distills strategies. Across three benchmarks and three executors, solves 64.7–70.5% of tasks (+25.6 to +30.4 pp over initial skill, +8.7 to +14.0 pp over strongest baseline). Removing coverage reduces recovered failures by 20.8% on SkillsBench with GPT-5.5.

**Concrete tasks for harness/autonomy:**
- Instrument a lightweight coverage tag on current skill/instruction steps in gate traces (follow / not-follow / not-covered) for recent failures.
- Require proposals that edit skills or prompts to cite the coverage label they address and re-check the same label on a protected slice.
- Distill recurring coverage failure patterns into a small shared strategy note in the autonomy ledger.

**Potential risks:** Coverage instrumentation adds trace overhead. Mislabeling follow vs not-follow can drive wrong edits. Over-focus on covered instructions may ignore useful uncovered exploration.

## 2. Beyond Weight Updates: Evolving Agent Harnesses for Domain Specialization
https://arxiv.org/abs/2611.25380 (2026-11-19)

**Core claim + evidence:** Domain specialization is usually framed as weight updates (RL/SFT). Complementary axis: evolve the harness (system prompt, tool schemas, skill library, planning scaffolding) while keeping the policy frozen. Instantiated with GEPA as an RL-style outer loop. Harness adapters require no GPU training, load per domain, and compose with weight-based RL. On Codev (Claude Code-style) across SWE-bench Verified, OfficeBench, and Terminal-Bench: weight updates give strongest single-path gains; harness evolution recovers most of those gains at a small fraction of the compute; combining both is best. SFT specialization can shorten reasoning chains and increase truncation; harness adapters avoid this by construction.

**Concrete tasks for harness/autonomy:**
- Treat domain-specific prompt/tool/skill variants as loadable adapters and score them with paired hard-bank evidence before any acceptance.
- Log compute/token cost of harness-adapter search versus any future weight-related proposals so the relative efficiency remains visible.
- When process failures dominate a domain slice, prefer a harness adapter proposal over any weight-oriented request.

**Potential risks:** Adapters can overfit the search tasks if not held-out. Composition with frozen model may still hit content ceilings. Multiple adapters increase configuration complexity.

## 3. Evaluation-Free Recursive Self-Improvement for Coding Agents
https://arxiv.org/abs/2611.21056 (2026-11-16)

**Core claim + evidence:** Common self-improving coding agents use evaluate-and-select (downstream task outcomes to choose lineages), which is costly and risks benchmark-specific adaptation. ELITE (Explore-then-Integrate) proposes diverse focused improvements, implements them independently from the same parent, inspects the programs for complementary/redundant/conflicting mechanisms, and reimplements a compatible subset as one coherent descendant. Only deterministic structural and operational validity checks are used inside the loop; no downstream task outcomes or trajectories of candidates guide evolution. On SWE-bench Pro, improves initial agent from 60.0% to 85.6% (vs 86.7% DGM, 88.3% HGM) with zero candidate task evaluations and 8.8x / 3.2x lower wall-clock evolution time. Cross-benchmark transfer: 73.3% SWE-bench Verified, 69.3% Polyglot without further adaptation.

**Concrete tasks for harness/autonomy:**
- Prototype a small explore-then-integrate step on a non-production branch: generate 3–5 focused edit proposals from the same parent, retain only those that pass deterministic validity checks, then integrate complementary mechanisms.
- Require any multi-proposal cycle to report structural validity and mechanism compatibility before requesting paired hard-bank evaluation.
- Measure wall-clock and token cost of an evaluation-free exploration round versus a full evaluate-and-select round on a smoke subset.

**Potential risks:** Deterministic validity checks may miss semantic regressions. Integration of complementary mechanisms can introduce subtle conflicts not caught by structural tests. Transfer to non-coding task banks is unproven.

## 4. The Resolution Hypothesis: Agent Evolution's Key Is Identifying Improvements
https://arxiv.org/abs/2611.23068 (2026-11-17)

**Core claim + evidence:** Agent evolution loops (proposer writes candidates, selection accepts higher scores) often fail to bootstrap. Resolution Hypothesis: evolution stalls not because better artifacts are not proposed, but because noisy evaluations cannot reliably identify them. Across seven evolution methods and six models (>10M LLM calls), helpful candidates exist, yet selection is no better than random at distinguishing them from harmful ones, so errors accumulate. Calls for shifting effort from more candidate generators toward making true improvements detectable and accumulable.

**Concrete tasks for harness/autonomy:**
- Audit recent autonomy ledger decisions for cases where aggregate score rose while protected-slice or coverage evidence was noisy or disagreeing.
- Require any acceptance decision to include a resolution note: which deterministic signal (gate, coverage, non-regression) distinguished the accepted edit from rejected alternatives.
- Prefer paired evidence with low-variance metrics over single high-variance model judgments when resolving candidate quality.

**Potential risks:** Over-emphasis on resolution can slow cycles if every signal is required to be perfect. Small protected slices remain noisy. Ignoring useful but high-variance signals may discard real gains.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, add a coverage-style label (or equivalent first-signal tag) to at least one failure cluster and require the corresponding proposal to cite it; log only, no production change.
2. **For the operator:** Approve or reject a lightweight experiment that generates 3 focused edit proposals, filters them with existing deterministic checks only, and reports mechanism compatibility before any hard-bank run.
3. **For the agent (after approval):** Draft a short standing rule that every admission decision must name the resolution signal that separated the accepted edit from near-miss alternatives.

## Operator question

Do you approve piloting the coverage-style labeling + resolution-signal note on the next autonomy cycle (log only), and/or a small evaluation-free explore-then-integrate prototype on a non-production branch?
