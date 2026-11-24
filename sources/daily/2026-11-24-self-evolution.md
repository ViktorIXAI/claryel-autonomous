# Daily Self-Evolution Research Summary — 2026-11-24

Selected 4 strongest recent papers with empirical evidence on modular gated harness evolution, requirement-centered selection, risks of feedback-free skill rewriting, and local verification of memory. All applicable to a frozen-model harness that requires paired evidence and an autonomy ledger.

## 1. Harnesses That Improve Themselves: A Unifying Framework for Self-Improving Agent Harnesses
https://arxiv.org/abs/2611.22299 (2026-11-17)

**Core claim + evidence:** Self-improving harnesses inspect execution traces, separate runtime bugs from model limits, and rewrite their own code. The framework pairs four editable components (context/state, agent control, action interfaces, verification/recovery) with a four-stage diagnose-propose-validate-deploy loop. Full-harness rewrites overfit or break across modules; modular updates with validation gates generalize across models while bounding token cost. On SWE-bench Lite, gated modular evolution outperforms prompt reflection and full rewrites at a fraction of the token cost. Practical defenses address prompt bloat, benchmark gaming, and evaluator tampering.

**Concrete tasks for harness/autonomy:**
- Map current gates, fixers, and validators to the four component categories and record which are currently treated as editable versus frozen.
- Require every proposed harness edit to target a single module and to pass a protected-case regression gate before ledger acceptance.
- Log token cost of each candidate edit so modular versus full-rewrite trade-offs can be measured on the hard bank.

**Potential risks:** Over-modularization can miss cross-module interactions. Validation gates that are too weak still allow gaming. Token accounting itself consumes budget.

## 2. Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses
https://arxiv.org/abs/2611.24924 (2026-11-18)

**Core claim + evidence:** Existing methods produce narrow, benchmark-specific patches because they ignore implicit user requirements and use a single evolution agent plus score-based selection. AHE-Beta uses a three-step loop: simulated users raise requirements as issues over multi-turn interaction, team-based modification produces generalizable changes, and requirement-driven selection merges a change only when it resolves a verified requirement and passes review. On held-out tasks, pass@1 rises from 21.9% to 33.3% with 40.8% fewer tokens; blind human A/B prefers it in 31 of 48 pairs. Gains transfer to other models without further evolution.

**Concrete tasks for harness/autonomy:**
- Add a standing requirement that every accepted harness change must cite the specific failure mode or operator instruction it resolves, not only a score delta.
- Pilot a short "issue" format in the autonomy ledger that records the observed requirement before any proposal is written.
- Prefer multi-turn diagnosis of a failure cluster over single-shot patch proposals.

**Potential risks:** Simulated-user requirements can diverge from real operator needs. Extra review steps increase latency. Human preference may not align with hard-bank scores.

## 3. How Feedback-Free Self-Evolution Reshapes Agent Skills: A Systematic Study
https://arxiv.org/abs/2611.25534 (2026-11-19)

**Core claim + evidence:** Models that rewrite expert skills round after round without any task, run, or judgment degrade the skills. Every tested model performs worse with the rewritten skills on every benchmark; average drop is 15 points on SkillsBench after thirty rounds. Rewriting pulls skills toward the model's prior and discards knowledge outside that prior first. Restoring the discarded knowledge recovers most of the loss. SkillDiff, which marks external knowledge in place, raises SkillsBench pass rate by 4.8 points on average without feedback or text changes.

**Concrete tasks for harness/autonomy:**
- Forbid pure self-rewrite of standing rules or prompts without paired hard-bank evidence; any proposal must cite the runs that motivated it.
- When a rule is edited, retain a diff of the original expert or operator text and require an explicit justification for each deletion.
- Add a ledger field that flags whether a proposed change preserves or discards previously recorded successful behavior.

**Potential risks:** Over-protection of original text can freeze useful adaptation. Marking "external knowledge" requires human judgment of what counts as expert content.

## 4. From Reflection to Co-Evolution: Self-Evolving Agents with Locally Verified Memory
https://arxiv.org/abs/2611.10382 (updated 2026-11-20)

**Core claim + evidence:** Plausible memories can be redundant or reinforce inappropriate actions. Anchor localizes consequential trajectory steps, extracts candidate memories, and replays each source decision with and without the candidate under the same context. Most candidates produce little distribution shift; both successful and failed source actions can be reinforced or suppressed. Only candidates that pass shift-magnitude and source-role-alignment tests are retained. On held-out ALFWorld and WebShop, Anchor improves success rate and mean score by up to 19.9% and 17.2% relative to the strongest baseline, while retaining 41% fewer cards than unfiltered retention.

**Concrete tasks for harness/autonomy:**
- Before promoting any new autonomy rule or memory note, require a paired replay of the source failure with and without the proposed note.
- Reject memory or rule additions that do not measurably shift the outcome of the source case under identical seeds.
- Log the fraction of candidate notes that survive local verification so memory bloat can be tracked.

**Potential risks:** Replay cost is non-zero. Local verification may miss long-horizon effects that only appear after several subsequent tasks. Over-filtering can discard useful but low-shift knowledge.

## Proposed concrete tasks (1-3)

1. **For the agent:** On the next autonomy cycle, record every proposed edit as a single-module change that cites the concrete requirement or failure it addresses, and attach a short "preserves prior successful behavior" note. Log only; no production code change.
2. **For the operator:** Approve or reject adding a standing ledger rule that pure self-rewrites of prompts or rules without paired hard-bank evidence are automatically rejected (feedback-free degradation warning).
3. **For the agent (after approval):** Draft the exact ledger fields for "module targeted," "requirement cited," and "local-verification result" so they can be added as standing rules without touching the hard bank.

## Operator question

Do you approve piloting the single-module + requirement-citation note (log only) on the next autonomy cycle, and/or adding the automatic rejection of pure feedback-free self-rewrites of standing rules?
