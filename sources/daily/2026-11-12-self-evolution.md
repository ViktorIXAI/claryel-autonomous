# Daily Self-Evolution Research Summary — 2026-11-12

Selected 4 strongest recent papers with empirical or formal evidence on multi-agent recursive adaptation, catastrophic forgetting under continual evolution, harness-side cost reductions, and compositional security/admission control. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. SciMARS: Multi-Agent Recursive Self-Improvement for Closed-Loop Scientific Discovery
https://arxiv.org/abs/2611.12552 (2026-11-09)

**Core claim + evidence:** Multi-agent systems lose observations and repeat mistakes under fixed roles and memory policies. SciMARS uses a shared evidence graph plus separate component editors for roles/coordination and (in +Memory) for recording/retrieval. Candidate probes guide selection. On Autonomous Science Bench, SciMARS+Memory resolved 12/18 GPT-6-Astra attempts vs 8/18 for the base team; on ScienceAgentBench 14/38 vs 11/38; on AppWorld 11/20 vs 5/20.

**Concrete tasks for harness/autonomy:**
- Prototype a lightweight shared evidence graph (JSON or ledger entries) that records intermediate observations, tool results, and failure attributions across sequential gate runs so later proposals can reference them without full re-execution.
- Separate current autonomy rules into role-specific editors (solver, proposer, critic) and test whether editing only one role at a time reduces collateral regressions.
- Add a probe step that generates a small candidate harness variant and evaluates it on a fixed smoke subset before full admission.

**Potential risks:** Shared graph can grow large and raise context cost. Role editors may introduce inconsistencies if interfaces are not frozen. Probe evaluation still needs paired regression evidence.

## 2. Can Coding Agents Sustain Continual Evolution without Forgetting?
https://arxiv.org/abs/2611.03219 (2026-11-02)

**Core claim + evidence:** Continual harness self-evolution across sequential task distributions produces severe catastrophic forgetting. With DeepSeek-V4-Flash and Meta-Harness, performance on SWE-Bench rose to 94% after evolution, then fell to 32% after further evolution on FeatureBench (66% relative drop). Patterns hold across six evolution directions and two methods.

**Concrete tasks for harness/autonomy:**
- After every accepted harness change, re-run a fixed regression slice of earlier hard-bank categories and log the retention ratio in the autonomy ledger.
- Introduce a retention budget: proposals that drop more than a stated threshold on any prior category are rejected even if the current category improves.
- Periodically interleave evolution cycles with replay of a mixed historical task subset to measure and mitigate forgetting.

**Potential risks:** Regression re-runs increase evaluation cost. Retention thresholds may block legitimate specialization. Historical slices must stay frozen and paired.

## 3. System Optimizations for Cost-Efficient Agent Harnesses
https://arxiv.org/abs/2611.12122 (2026-11-09)

**Core claim + evidence:** Task accuracy depends mainly on the underlying model; harness-side changes mainly affect cost. Analysis of cost-accumulation patterns yields Agency, an interposition platform. Proof-of-concept techniques reduce cost by up to 35% on real-world benchmarks without accuracy loss.

**Concrete tasks for harness/autonomy:**
- Instrument gate_run.py traces to tag cost hotspots (redundant context, repeated tool calls, long reasoning chains) and log them per attempt.
- Prototype one low-risk harness-side optimization (e.g., history compaction or selective tool-result truncation) on a smoke subset and require paired evidence that accuracy is unchanged while token or energy use falls.
- Add a cost-efficiency metric (score per kWh or score per wall-second) to the autonomy ledger acceptance criteria.

**Potential risks:** Optimizations that appear cost-neutral on smoke sets may degrade rare failure modes. Interposition layers can introduce new failure surfaces. Local hardware telemetry must be reliable for energy claims.

## 4. From Attack Surface to Defense Architecture: Compositional Security for Agentic Coding Harnesses
https://arxiv.org/abs/2611.13960 (2026-11-10)

**Core claim + evidence:** Agentic coding harnesses turn dual-use tools into Living-off-the-Land platforms once instructions are injected. ActiveSecHarness uses Separation of Intelligence and Authority with capability tokens, taint lattices, deterministic Ring-0 guards, and audit logs. On 252 fixtures a local LLM judge refused 98.3% of benign work at high latency; Ring-0 guards achieved ABR=1.000 and FPR=0.000 in 12.7 µs (11,200× faster).

**Concrete tasks for harness/autonomy:**
- Map current tool calls in gate_run.py to capability rings and add a deterministic pre-execution guard that rejects calls outside the declared ring for the task.
- Log every tool invocation with a simple taint tag (trusted input vs retrieved content) and require an admission check before any self-modification that expands tool privileges.
- Add a kill-chain regression fixture set that must pass after any harness change touching tool or file interfaces.

**Potential risks:** Over-restrictive guards can block legitimate repairs. Taint tracking adds implementation surface. Security fixtures may not cover all local failure modes.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record a retention ratio on a small fixed prior-category slice and a simple cost proxy for every proposal; report how many recent changes would have been rejected under a retention or cost threshold. No production code change.
2. **For the operator:** Approve or reject adding a minimal shared evidence graph (or ledger extension) that stores intermediate attributions so later proposals can reference them without full re-execution.
3. **For the agent (after approval):** Draft a deterministic pre-execution tool guard that classifies calls by capability ring and logs rejections, specifying the exact insertion point and the regression fixtures that must still pass.

## Operator question

Do you approve defining a fixed small regression slice of earlier hard-bank categories that must be re-evaluated after every accepted autonomy change (results logged as a retention ratio), or should we first run a one-cycle pilot that only records the ratio without blocking proposals?
