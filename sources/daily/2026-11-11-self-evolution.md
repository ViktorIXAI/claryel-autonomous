# Daily Self-Evolution Research Summary — 2026-11-11

Selected 4 strongest recent papers with empirical evidence on reliability/coverage trade-offs, catastrophic forgetting under continual evolution, harness-side cost reductions, and trajectory-level error entry/control points. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not reliably imply better agents. Across four methods, two harnesses and general/coding tasks, all 16 evolved agents gained previously uncovered tasks while losing previously covered ones. Reliability can rise (e.g., +5.2 points) while losing 10 covered tasks; most reliability gains also raise deployment cost. Specific component changes outperform generic reminders, but effects reverse when combined. Strict admission can discard useful alternatives; transfer of gains is selective.

**Concrete tasks for harness/autonomy:**
- Extend the autonomy ledger to record both coverage (tasks solved at least once) and reliability (average success rate) deltas, plus per-task gain/loss lists, for every accepted proposal.
- Add a cost column (tokens, wall time, or energy proxy from telemetry) to acceptance decisions and reject proposals whose cost increase exceeds a stated threshold even if mean score rises.
- Maintain a protected-case set of previously solved hard-bank tasks; any proposal that regresses any protected case is rejected regardless of aggregate gain.

**Potential risks:** Over-emphasizing preservation can freeze useful evolution. Cost accounting depends on complete telemetry. Protected sets may become outdated if the task distribution shifts.

## 2. Can Coding Agents Sustain Continual Evolution without Forgetting?
https://arxiv.org/abs/2611.03219 (2026-11-02)

**Core claim + evidence:** Continual harness self-evolution across sequential task distributions produces severe catastrophic forgetting. With DeepSeek-V4-Flash and Meta-Harness, performance on SWE-Bench rose to 94% after evolution, then fell to 32% after further evolution on FeatureBench (66% relative drop). Similar patterns appear across six evolution directions and two methods. Insights point to the need for retention mechanisms when evolving across multiple task types.

**Concrete tasks for harness/autonomy:**
- After every accepted harness change, re-run a fixed regression slice of earlier hard-bank categories and log the retention ratio in the autonomy ledger.
- Introduce a retention budget: proposals that drop more than X% on any prior category are rejected even if the current category improves.
- Periodically interleave evolution cycles with replay of a mixed historical task subset to measure and mitigate forgetting.

**Potential risks:** Regression re-runs increase evaluation cost. Retention thresholds may block legitimate specialization. Historical slices must stay frozen and paired.

## 3. System Optimizations for Cost-Efficient Agent Harnesses
https://arxiv.org/abs/2611.12122 (2026-11-09)

**Core claim + evidence:** Task accuracy depends mainly on the underlying model; harness-side changes (prompts, tools, system interventions) mainly affect cost. Analysis of cost-accumulation patterns yields Agency, an interposition platform that applies portable optimizations to existing harnesses. Proof-of-concept techniques reduce cost by up to 35% on real-world benchmarks without accuracy loss.

**Concrete tasks for harness/autonomy:**
- Instrument gate_run.py traces to tag cost hotspots (redundant context, repeated tool calls, long reasoning chains) and log them per attempt.
- Prototype one low-risk harness-side optimization (e.g., history compaction or selective tool-result truncation) on a smoke subset and require paired evidence that accuracy is unchanged while token or energy use falls.
- Add a cost-efficiency metric (score per kWh or score per wall-second) to the autonomy ledger acceptance criteria.

**Potential risks:** Optimizations that appear cost-neutral on smoke sets may degrade rare failure modes. Interposition layers can introduce new failure surfaces. Local hardware telemetry must be reliable for energy claims.

## 4. Dependable Long-Horizon LLM Agents: A Trajectory-Centered Empirical Study of Where Errors Enter and Which Controls Reach Them
https://arxiv.org/abs/2611.13254 (2026-11-09)

**Core claim + evidence:** Failures in long-horizon multi-agent runs are usually not first detected at the symptom step. In 95 annotated failed trajectories, faults enter early (median 0.18 of the run), mostly as wrong decisions or fabrications; in 72% of runs the trajectory already contained contradictory evidence that no agent acted on. Independent judges, fixed task contracts, and belief re-checking against the environment cover most episodes; restoring the agent's own state would have sufficed in 35 of 95 cases.

**Concrete tasks for harness/autonomy:**
- Annotate a sample of recent gate_run failures with entry point (phase + state domain) rather than only final symptom, and store the annotation in the failure log.
- Add an independent critic step that receives only the task contract and the current trajectory state (no shared context with the solver) and can veto continuation.
- Implement a lightweight state-restore or belief-recheck gate after any tool result that contradicts prior commitments.

**Potential risks:** Extra critic steps raise latency and cost. Annotation protocol may be subjective without clear operational definitions. State-restore logic can itself introduce regressions if not regression-tested.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, log both coverage and reliability deltas plus a simple cost proxy (wall time or tokens) for every proposal; report how many recent accepted changes would have been rejected under a protected-case or cost-threshold rule. No production code change.
2. **For the operator:** Approve or reject adding a fixed regression slice (prior hard-bank categories) that must be re-evaluated after every accepted harness change, with a retention threshold recorded in the ledger.
3. **For the agent (after approval):** Draft a minimal independent-critic prompt and insertion point in the verification flow, specifying exactly what context it sees and how its veto is logged.

## Operator question

Do you approve defining a fixed regression slice of earlier hard-bank categories that must be re-run after every accepted autonomy change (with results logged as a retention ratio), or should we first run a one-cycle pilot that only records coverage/reliability/cost deltas without blocking any proposals?
