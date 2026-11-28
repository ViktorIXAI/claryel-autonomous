# Daily Self-Evolution Research Summary 2026-11-28

Selected four recent papers with strong empirical grounding and direct applicability to a frozen-model harness that uses paired evidence and an autonomy ledger.

### Agent-as-a-Verifier: From Scores to Evidence for General Verification (arXiv:2611.34132)
Core claim: Score-based verifiers lack auditable evidence; an agentic claim-obligation-certificate protocol (verdict-blind claim DAG + independent contract compilation + checkable obligations) produces certificates that improve accuracy and detect reward-hacking solutions that fool benchmark evaluators.
Evidence: Higher accuracy than SOTA on Terminal-Bench 2.1; in-loop improvements on FrontierMath, Terminal-Bench 2.1, and CyberGym; case study of retained counterexample for a rewarded but contract-violating solution.
Concrete tasks: Require a minimal claim-obligation certificate (extracted claims + acceptance-contract obligations + verification evidence) in every autonomy ledger entry before any repair or harness edit is accepted. Prototype the protocol on the last five hard-bank failures and log whether it surfaces silent or reward-hacked failures missed by current gates.
Risks: Certificate generation adds token cost and latency; incomplete claim extraction can produce false confidence or reject valid but underspecified solutions.

### Demystifying the Autoresearch Harness: How Context and Skills Shape Self-Evolving Agents (arXiv:2611.28244)
Core claim: For long-horizon self-evolving agents, preserving individually accessible records of past attempts (context folding) outperforms rolling summaries (up to +19.2% vs recency-truncation baseline); selectively discarding persistently unused skills outperforms consolidation or promotion to standing rules.
Evidence: Ablations across MLE-Bench and KernelBench with three models (gpt-oss-120b, gpt-6-luna, gpt-6-sol); MLEvolver combining folding + skill deletion reaches 72.7% medal rate on MLE-Bench Lite and 94% fast_1 on KernelBench Level 3 under fixed budget, outperforming AIDE and OpenEvolve.
Concrete tasks: Replace pure summarization of autonomy proposals with context folding (short digests + on-demand full retrieval) in the ledger; implement a skill-deletion policy that drops lessons unused for N consecutive proposals and measure hard-bank score and token cost versus current practice (paired).
Risks: Folding may still lose subtle cross-attempt patterns if digests are too aggressive; premature skill deletion can discard rare but high-value procedures.

### ARISE: Practical Self-Evolving Memory for Accurate and Cost-Efficient Enterprise Agents (arXiv:2611.23588)
Core claim: Memory can evolve from an agent’s own failures (no weight, tool, or workflow updates) via failure attribution → micro corrections → consolidated macro rules, accepted only when held-out accuracy rises; yields accuracy gains at equal or lower cost.
Evidence: Across 14 domains on SOP-Bench and τ²-bench with 5 models, ARISE-Teacher +10.9 pp (SOP) / +5.8 pp (τ²) vs baseline and beats GEPA; ARISE-Self still +10.0 pp on SOP-Bench; 4.0% fewer model calls and 5.2% fewer output tokens at comparable per-task cost.
Concrete tasks: Add a held-out acceptance gate for any proposed macro rule or ledger pattern (promote only if paired hard-bank subset accuracy rises); prototype micro-memory retrieval of past corrections for the current failure type and measure conversion rate versus no-retrieval baseline.
Risks: Over-consolidation into macro rules can erase useful instance-specific detail; held-out set must be strictly disjoint or the gate becomes circular.

### Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses (arXiv:2611.24924)
Core claim: Requirement-centered loop (user-driven issue raising → team-style generalizable modifications → requirement-driven selection that merges only when a verified requirement is resolved) produces more transferable harness improvements than score-only evolution and is preferred by real users.
Evidence: Held-out pass@1 21.9% → 33.3% with 40.8% fewer tokens; higher than Claude Code / Meta-Harness / AHE; blind human A/B preference in 31/48 pairs across five dimensions; gains transfer to GLM-5.3 (+15.8%) and DeepSeek-V4.1-Flash (+5.3%) without re-evolution.
Concrete tasks: Annotate every autonomy proposal with the explicit requirement (and any inferred implicit requirement) it claims to satisfy; accept only if a protected-subset replay shows the requirement is resolved without regression on unrelated cases. Run one simulated multi-turn requirement-collection cycle on recent failures and compare resulting patches to pure score-driven proposals.
Risks: Simulated users can invent requirements that do not match real operator needs; requirement verification itself can become a new source of benchmark gaming if not independently checked.

**Broader scientific note (systems engineering / organizational):** The claim-obligation-certificate pattern (Agent-as-a-Verifier) and requirement-driven selection (AHE-Beta) supply formal and process-level constraints that can be turned into measurable admission rules for the autonomy ledger, reducing reliance on scalar scores alone.

**Proposed concrete tasks (2026-11-28):**
1. Prototype a minimal claim-obligation certificate on the last five hard-bank failures and log detection of any silent or contract-violating cases (paired with current gates).
2. Implement context folding (digest + on-demand full record) for the last 10 autonomy proposals and measure token cost + hard-bank score versus current summarization (paired, non-production).
3. Add a held-out accuracy gate for macro-rule / pattern proposals and re-score the last three accepted or rejected ledger entries under it.

**Question for operator:** Approve a controlled, non-production experiment that implements the claim-obligation certificate check and context-folding prototype on a frozen subset of the hard bank (no production code changes, no hard-bank modifications)? Yes / No / Modify.
