# Daily Self-Evolution Research Summary — 2026-11-13

Selected 4 strongest recent papers with empirical or formal evidence on reliability vs. coverage trade-offs in harness evolution, falsification-gated admission of lessons, statistical control of false updates, and the limited incremental value of failure traces. All are applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Beneath the Surface: What We Overlook When We Talk About Agent Evolution
https://arxiv.org/abs/2611.07624 (2026-11-05)

**Core claim + evidence:** Higher benchmark scores from harness evolution do not imply reliable, efficient, or transferable improvement. Across four methods, harnesses, and general/coding tasks, all sixteen evolved agents gained previously uncovered tasks while losing previously covered ones. In one case reliability rose 5.2 points while losing ten previously covered tasks. Most reliability gains increased deployment cost. Specific changes usually outperformed generic reminders, but combinations altered benefits. Strict admission can discard useful alternatives; transfer selectively preserves gains. EvoAudit revises select/analyze/mutate/gate and achieved the best performance.

**Concrete tasks for harness/autonomy:**
- After every accepted change, log both newly covered and newly regressed hard-bank tasks (preservation-aware metrics) rather than only net score.
- Require proposals to declare applicability conditions and expected side-effects; reject those that improve the current slice while regressing a fixed protected subset.
- Prototype an EvoAudit-style review step that replays recent autonomy decisions and suggests revisions to the gate rules before the next cycle.

**Potential risks:** Over-emphasizing preservation can freeze useful specialization. Extra logging increases ledger size. Admission replays add evaluation cost.

## 2. When Should Agents Remember? Falsification-Gated Self-Evolution for LLM Agents
https://arxiv.org/abs/2611.14326 (2026-11-10)

**Core claim + evidence:** Episode-derived lessons written directly into memory are unreliable signals for persistent state. FGSE represents each candidate as a structured hypothesis (precondition, behavior change, expected effect, verifier), applies it only temporarily, and tests on target-transfer, falsification, and archived-regression probes before commit/refine/reject. On WebArena, AppWorld, and τ-bench variants it achieved strong scores while cutting falsification failures to 5.0%, regression damage to 1.3%, and harmful committed updates to 3.6%.

**Concrete tasks for harness/autonomy:**
- Require every autonomy proposal that adds a reusable lesson or rule to include an explicit precondition, expected effect, and verifier assertion.
- Before ledger acceptance, run the proposal in a temporary state against a small target-transfer slice, a falsification set of near-miss cases, and an archived-regression set; commit only if all three pass thresholds.
- Log the probe outcomes in the autonomy ledger so later reviews can audit why a lesson was retained or rejected.

**Potential risks:** Probe sets must be carefully constructed or they become another source of overfitting. Temporary-state application adds implementation complexity. Overly strict falsification may reject useful narrow lessons.

## 3. Trustworthy Recursive Self-Improvement with Statistical Guarantees
https://arxiv.org/abs/2611.10787 (2026-11-07)

**Core claim + evidence:** Greedy gates that accept any higher validation score produce many inferior updates (45.59% on average). TRUST adapts online multiple-hypothesis testing to control the rate of false evolution, with an LLM helping set evidence thresholds from historical context. Under stated assumptions it bounds the proportion of accepted updates that cause unacceptable loss and provides a lower bound on final gain. On HotpotQA, DROP, and APPS with DeepSeek-V4-Flash and Qwen-3.8-Flash it reduced accepted inferior updates to 2.78% while matching or exceeding stronger statistical baselines.

**Concrete tasks for harness/autonomy:**
- Replace pure score-threshold admission with a simple statistical gate that requires the observed gain to exceed a historical-variance-adjusted threshold before acceptance.
- Maintain a running estimate of false-evolution rate in the autonomy ledger and raise the evidence bar when the recent rate exceeds a bound.
- Pilot the gate on a replay of the last 10 autonomy decisions and report how many would have been rejected under TRUST-style control.

**Potential risks:** Conservative thresholds can slow progress. Variance estimates on small hard-bank slices are noisy. The LLM-assisted threshold setting itself needs deterministic fallback.

## 4. Agent Self-Improvement with Frozen Weights: The Added Value and Limits of Failure Traces
https://arxiv.org/abs/2611.11342 (2026-11-08 / v2 2026-11-11)

**Core claim + evidence:** A harness (notes) can learn from an agent's failure traces beyond a matched search that never sees them, but the incremental value is modest. With a frozen 9B model and a larger teacher writing notes, seeing mistakes improved accuracy by 4.0 pp on generated customer-service decisions; the search process alone captured ~60% of the total gain. In full conversations the same notes showed no demonstrated improvement. A neutral note without procedure outscored the learned lessons in exploratory tests. Many tool-use test items were judged defective.

**Concrete tasks for harness/autonomy:**
- When mining failure.md entries for proposals, always compare against a matched baseline that sees only successful traces or no traces; require the failure-aware proposal to show a measurable paired gain over that baseline.
- Prefer short, neutral, or procedure-free notes when the incremental value of failure details is not demonstrated on a hold-out slice.
- Add a quick audit step that flags defective or underspecified test cases in the hard bank before using them to drive evolution.

**Potential risks:** Ignoring failure traces entirely may miss systematic harness bugs. Neutral notes can underfit. Defective test items can produce misleading paired evidence.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record both newly covered and newly regressed tasks for every proposal, plus a simple probe outcome (transfer / falsification / regression) if the proposal adds a reusable rule. Report the numbers in the ledger without blocking. No production code change.
2. **For the operator:** Approve or reject adding a minimal structured-hypothesis template (precondition + expected effect + verifier) that autonomy proposals must fill when they introduce a persistent lesson or gate change.
3. **For the agent (after approval):** Draft a statistical-admission sketch that uses historical variance of hard-bank scores to set a minimum gain threshold, specifying exactly where it would be inserted in the current ledger process and which regression fixtures must still pass.

## Operator question

Do you approve piloting preservation-aware logging (newly covered vs. newly regressed tasks) plus a structured-hypothesis template for reusable lessons on the next autonomy cycle, with results recorded but not yet used to block proposals, or should we first run only the logging pilot?
