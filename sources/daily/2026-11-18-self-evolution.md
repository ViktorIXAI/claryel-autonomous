# Daily Self-Evolution Research Summary — 2026-11-18

Selected 4 strongest recent papers with empirical evidence on modular gated evolution, evaluation-free mechanism integration, the detection bottleneck in evolution, and falsification-gated admission of memory updates. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Harnesses That Improve Themselves: A Unifying Framework for Self-Improving Agent Harnesses
https://arxiv.org/abs/2611.22299 (2026-11-17)

**Core claim + evidence:** Self-improving harnesses pair four editable runtime components (context/state, agent control, action interfaces, verification/recovery) with a four-stage diagnose-propose-validate-deploy loop. Full-harness rewrites overfit or break across modules; modular updates with validation gates generalize across models while bounding token cost. Practical defenses address prompt bloat, benchmark gaming, and evaluator tampering. Experiments on SWE-bench Lite show gated modular evolution outperforms prompt reflection and full-harness rewrites across models and repositories at a fraction of the token cost.

**Concrete tasks for harness/autonomy:**
- Map current gate_run.py surfaces onto the four editable components and flag which ones are currently allowed to change under the autonomy rules.
- Require every candidate edit to declare its target component and pass a modular validation gate that checks only that component plus a small protected regression slice.
- Add a simple bloat/gaming check (token growth or protected-slice regression) as an admission filter before any ledger entry is marked accepted.

**Potential risks:** Over-modularization can miss cross-component interactions. Validation gates that are too narrow may accept locally better but globally worse compositions. Defense heuristics can reject useful but unusual edits.

## 2. Evaluation-Free Recursive Self-Improvement for Coding Agents (ELITE)
https://arxiv.org/abs/2611.21056 (2026-11-16)

**Core claim + evidence:** Coding agents can self-improve without using downstream task outcomes inside the evolution loop. ELITE proposes diverse focused improvements from the same parent, implements them independently, inspects the resulting programs for complementary/redundant/conflicting mechanisms, and reimplements a compatible subset as one coherent descendant. Only deterministic structural and operational validity checks are used inside the loop. On SWE-bench Pro it improves the initial agent from 60.0% to 85.6% (vs 86.7% DGM and 88.3% HGM) while using zero candidate task evaluations and reducing wall-clock evolution time by 8.8x and 3.2x respectively. Cross-benchmark transfer without further adaptation reaches 73.3% on SWE-bench Verified and 69.3% on Polyglot.

**Concrete tasks for harness/autonomy:**
- Pilot a small evaluation-free proposal cycle on a non-critical harness module: generate several focused edits, keep only those that pass deterministic validity checks, and integrate a compatible subset before any hard-bank paired evaluation.
- Log the number of discarded conflicting mechanisms and the final integrated patch size so later cycles can measure integration overhead versus downstream gain.
- Compare the cost of one evaluation-free integration round against the current evaluate-and-select autonomy cycle on the same protected slice.

**Potential risks:** Deterministic validity checks may be too weak to catch semantic regressions. Integration of complementary mechanisms can still introduce subtle conflicts that only appear on the hard bank. Zero downstream evaluation inside the loop removes an early signal that our current process relies on.

## 3. The Resolution Hypothesis: Agent Evolution's Key Is Identifying Improvements
https://arxiv.org/abs/2611.23068 (2026-11-17)

**Core claim + evidence:** Agent evolution stalls primarily because noisy evaluations cannot reliably identify true improvements, not because proposers fail to generate better artifacts. Across seven evolution methods and six models (over 10M LLM calls), helpful candidate artifacts exist, yet selection is no better than random at distinguishing them from harmful ones, so errors accumulate. At the method level, typical margins of a few percentage points are smaller than the difference between two independent runs of the same method, so published rankings often rest on luck. The bottleneck is making true improvements detectable and accumulable.

**Concrete tasks for harness/autonomy:**
- On the next paired audit, compute the observed variance of the primary metric on a fixed harness across independent runs and require any candidate improvement to exceed that variance before admission.
- Record for each rejected candidate whether a later larger paired sample would have reversed the decision (resolution gap).
- Prefer admission rules that accumulate evidence across multiple independent paired slices rather than a single noisy score.

**Potential risks:** Requiring improvements to exceed run-to-run variance can become overly conservative on small hard-bank slices. Tracking resolution gaps increases logging overhead. Treating published method rankings as noisy is already consistent with our paired-evidence rule but may slow external comparison.

## 4. When Should Agents Remember? Falsification-Gated Self-Evolution for LLM Agents
https://arxiv.org/abs/2611.14326 (2026-11-10)

**Core claim + evidence:** Episode-derived lessons should not be written directly into persistent memory. FGSE represents each candidate lesson as a structured hypothesis (precondition, behavior change, expected effect, verifier), applies it only in a temporary state, and tests it on target-transfer, falsification, and archived-regression probes before commit/refine/reject. Across web, app, tool-use, and long-term memory benchmarks it achieves strong task performance while reducing falsification failures to 5.0%, regression damage to 1.3%, and harmful committed updates to 3.6%.

**Concrete tasks for harness/autonomy:**
- Represent every proposed memory or rule update as an explicit hypothesis with a precondition and a verifier, and evaluate it first in a temporary state against a small archived-regression probe drawn from previous hard-bank successes.
- Reject or refine any update that fails the falsification or archived-regression probe even if it improves the triggering case.
- Log the hypothesis structure and probe outcomes in the autonomy ledger so later cycles can audit which classes of update survive falsification.

**Potential risks:** Temporary-state evaluation adds latency and token cost. Archived-regression probes that are too small can miss rare regressions. Overly strict falsification can block useful but context-sensitive memory updates.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, require every candidate edit to declare its target component (context, control, action, verification) and to pass a modular validation gate plus a protected-slice non-regression check before any ledger admission (log only; no production code change).
2. **For the operator:** Approve or reject a small evaluation-free integration pilot on one non-critical module (generate several focused edits, integrate only those that pass deterministic validity, then run one paired hard-bank comparison).
3. **For the agent (after approval):** Draft a minimal falsification-gated admission checklist that treats proposed memory/rule updates as hypotheses and tests them against an archived-regression probe before commit.

## Operator question

Do you approve piloting the modular component declaration + protected-slice non-regression filter on the next autonomy cycle, and/or a small evaluation-free integration experiment on one non-critical module?
