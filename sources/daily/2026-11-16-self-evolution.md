# Daily Self-Evolution Research Summary — 2026-11-16

Selected 4 strongest recent papers with empirical evidence on falsification-gated memory admission, co-evolution of execution and evaluation harnesses without external feedback, automated verifier generation, and multi-agent harness optimization. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. When Should Agents Remember? Falsification-Gated Self-Evolution for LLM Agents
https://arxiv.org/abs/2611.14326 (2026-11-10)

**Core claim + evidence:** Local success is an unreliable signal for writing episode-derived lessons into persistent memory. FGSE represents each candidate lesson as a structured hypothesis (precondition, behavior change, expected effect, verifier). The hypothesis is applied only temporarily and tested on target-transfer, falsification (counterexample), and archived-regression probes; it is committed, refined, or rejected according to measured gain and risk thresholds. On WebArena, AppWorld, and τ-bench (Retail/Airline) the method achieves strong task performance (e.g., 39.8 WebArena success, 78.8 AppWorld average completion, 0.724/0.487 Pass¹) while reducing falsification failures to 5.0 %, regression damage to 1.3 %, and harmful committed updates to 3.6 %.

**Concrete tasks for harness/autonomy:**
- Represent every proposed memory or rule update as a structured hypothesis with explicit precondition, expected effect, and verifier.
- Add a temporary-state evaluation step that runs target-transfer, falsification, and archived-regression probes before any ledger admission.
- Log commit/refine/reject decisions with the measured gain, falsification rate, and regression damage; require all three to clear pre-set thresholds.

**Potential risks:** Probe construction adds evaluation cost and may reject useful but narrow updates. Thresholds on small paired slices are noisy. Overly strict falsification can block legitimate specialization.

## 2. Verify by Doing: Co-Evolving Agent Execution and Evaluation without External Feedback
https://arxiv.org/abs/2611.15276 (2026-11-11)

**Core claim + evidence:** When external feedback is unavailable, agents must infer success from observable evidence; incomplete verification misguides updates. VbD co-evolves Actor and Evaluator harnesses inside a single task while keeping model weights fixed. The Evaluator actively inspects artifacts and environment state with tools; its findings supply an internal signal for output selection and guide updates to both execution and verification procedures. Proposed Evaluators are comparatively reviewed on common candidates; Actor updates require support from their own fresh outputs. Across AutomationBench, τ³ Banking, and selected GDPval tasks, VbD obtains the highest overall scores among methods that operate without external feedback (gains of 3.3, 4.1, and 2.3 pp over the strongest baselines on the main backbone).

**Concrete tasks for harness/autonomy:**
- Pilot a lightweight co-evolution loop in which an Evaluator harness inspects gate_run.py artifacts and telemetry with tools and proposes bounded checks.
- Require that any Actor-harness proposal be supported by fresh outputs produced under the candidate Evaluator.
- Record the internal verification signal and its agreement with any available deterministic gates in the autonomy ledger.

**Potential risks:** Tool-based inspection can itself be incomplete or hallucinated. Comparative review of Evaluators increases token cost. Shared findings may create correlated blind spots between Actor and Evaluator.

## 3. Veritas: A Verifier Generation Harness for Agent Tasks
https://arxiv.org/abs/2611.13336 (2026-11-09)

**Core claim + evidence:** Self-improving systems depend on verifier quality, yet most verifiers are hand-written and do not scale. Veritas is a specialized harness that generates verifiers automatically by adding three mechanisms: an evidence header that states what the verifier will observe, a library of domain rules that tasks leave unstated, and authoring principles (partly refined by a self-improvement loop). On six benchmarks (four execution-scored whose official verifiers were first certified, two pairwise), with the model fixed, Veritas-generated verifiers agree better with official verdicts than those of seven other harnesses on all four execution-scored sets and are at or near the best on the pairwise sets. The same mechanisms improve 9 of 12 harness–benchmark pairs when plugged into other harnesses.

**Concrete tasks for harness/autonomy:**
- Add an evidence-header template to any new deterministic or model-assisted verifier so that the observable inputs are declared before generation.
- Maintain a small domain-rule library (initially extracted from hard-bank task descriptions) that verifier-generation steps can search.
- Pilot automatic generation of one additional deterministic check for a recurring failure cluster and measure agreement with existing gates before admission.

**Potential risks:** Generated verifiers can be overly restrictive (rejecting valid alternative solutions). Domain-rule library can become stale or incomplete. Self-improvement of authoring principles risks reward hacking if not anchored by certified official verdicts.

## 4. MULTILOOP: Evolving Multi-Agent Harnesses for Complex Information-Seeking Tasks
https://arxiv.org/abs/2611.15754 (2026-11-11)

**Core claim + evidence:** Automated harness optimization has focused on single-agent systems; multi-agent harnesses are harder because fixes must also change how agents interact. MULTILOOP applies a simple optimization loop (analyze traces, evaluate, edit harness) to complex information-seeking tasks from DeepSearchQA. With only 10 training samples the evolved harness improves accuracy by 4.6 % over the base harness and by 3.2 % over the best single-agent system. A failure-mode taxonomy shows that orchestration failures largely persist, motivating methods that encourage structural changes to delegation and information sharing.

**Concrete tasks for harness/autonomy:**
- When the autonomy loop involves multiple interacting components (gate, fixer, critic), record interaction traces and diagnose orchestration failures separately from single-component failures.
- Propose one structural edit (e.g., changed hand-off or shared evidence format) and evaluate it with paired evidence on a held-out slice.
- Maintain a short taxonomy of orchestration failure modes in the ledger to guide future proposals.

**Potential risks:** Structural changes to multi-component interaction can introduce new failure modes that are harder to detect than local bugs. Small training slices (10 samples) may overfit orchestration patterns. Evaluation cost rises with multi-agent rollouts.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, format any proposed memory or rule update as a structured hypothesis and run (or sketch) the three probes (target-transfer, falsification, archived-regression) before logging an admission decision. Log only; no production code change.
2. **For the operator:** Approve or reject a small pilot that adds an evidence-header template to one existing verifier and extracts a seed domain-rule library from the hard bank.
3. **For the agent (after approval):** Draft a minimal co-evolution sketch in which an Evaluator inspects recent gate_run.py traces and proposes one additional check, with the proposal required to be supported by fresh paired outputs.

## Operator question

Do you approve piloting the structured-hypothesis + three-probe admission logging for memory/rule updates on the next autonomy cycle, and simultaneously adding an evidence-header template to one verifier, or should we start with only the hypothesis logging?
