# Daily Self-Evolution Research Summary — 2026-11-27

Selected four recent papers with strong empirical grounding, reproducibility signals, and direct applicability to a frozen-model harness that uses paired evidence and an autonomy ledger. Focus on transferable interventions, auditable certificates, and shared failure modes.

### TransHarness: From Benchmark Overfitting to Transferable Harness Evolution (arXiv:2611.33757, 2026-11-25)
Core claim: Harness evolution that derives intervention policies from same-task success–failure contrasts (context-sensitive triggers + diagnostic guidance), then filters via cross-task replay and independent semantic selection, transfers gains to new benchmarks and strong models/mature harnesses instead of overfitting the evolution set.
Evidence: Independent evolution set + cross-benchmark evaluation (DeepSWE v1.1, Terminal-Bench 2.1) across multiple strong models and harness maturity levels; 300 source trajectories outside the test distribution produce SOTA (76.4% DeepSWE, 95.5% Terminal-Bench 2.1), exceeding GPT-6 Astra by 2.4–5.6 pp. Explicit analysis of recovery vs regression rates required for net gain on high-baseline agents.
Concrete tasks: Generate same-task success/failure pairs from recent hard-bank runs; author 3–5 candidate intervention policies (trigger + guidance) and subject them to replay on a held-out protected subset before any autonomy ledger proposal. Log recovery/regression ratios for every candidate.
Risks: Over-filtering of useful but source-specific repairs; trigger conditions that fire too broadly and introduce latency or false interventions on already-correct runs.

### Agent-as-a-Verifier: From Scores to Evidence for General Verification (arXiv:2611.34132, 2026-11-25)
Core claim: Score-based verifiers lack auditable evidence. An agentic certificate protocol (verdict-blind claim dependency graph + independently compiled acceptance contract + checkable obligations) produces certificates that improve accuracy, catch reward-hacking, and support recursive optimization.
Evidence: Higher accuracy than SOTA on Terminal-Bench 2.1; gains on FrontierMath and CyberGym when used as an augmented agent; demonstrated detection of solutions that deceive the benchmark evaluator. Code released.
Concrete tasks: For the next 10 hard-bank failures, extract a lightweight claim graph and acceptance obligations from the task prompt + expected output; require any proposed repair to produce a matching certificate that references the obligations before acceptance in the autonomy ledger. Prefer this over pure model-as-judge scores.
Risks: Certificate generation itself can be gamed or become a token sink; incomplete obligation extraction may reject valid repairs that satisfy the true intent.

### ProbeAgent: Principled Diagnosis of Agent Failures in Verifiable Environments (arXiv:2611.26897, 2026-11-19)
Core claim: Automated discovery of shared failure modes by constructing executable tests, validating them against reference solutions, then probing whether a suspected cause recurs under changed context. Distinguishes task difficulty from repeated agent errors.
Evidence: 1,244 failures across 22 agent configurations and 10 benchmarks → 536 failure-mode descriptions. Human annotators accept 90% of assigned descriptions and correctly reject 83% of similar alternatives.
Concrete tasks: On the last 20 hard-bank failures, generate one probe task per attributed cause that preserves the suspected harness or instruction fault while changing surface details; log whether the failure recurs. Use the recurring probes as protected cases for future admission gates.
Risks: Probe tasks that accidentally change the true difficulty or introduce new failure modes; cost of generating and running probes on limited local hardware.

### Agentic Harness Engineering Beta: Requirement-Centered Evolution of Agent Harnesses (arXiv:2611.24924, 2026-11-18)
Core claim: Requirement-centered loop (explicit + implicit requirements → verified resolution + review) avoids narrow benchmark-specific patches. Human A/B preference aligns with the method and transfers to other models without further evolution.
Evidence: Pass@1 lifted from 21.9% to 33.3% on held-out tasks with 40.8% fewer tokens; preferred in 31/48 blind human pairs across five dimensions; transfers to GLM-5.3 and DeepSeek-V4.1-Flash.
Concrete tasks: Annotate the next autonomy proposal with the explicit requirement it claims to satisfy and one implicit requirement derived from the autonomy ledger rules; require both to be verified by paired evidence before acceptance.
Risks: Over-weighting simulated or short human preference samples; implicit requirements that are under-specified and become moving targets.

**Broader influence note (cognitive science / metacognition):** Capability-level metacognition remains weak in current VLMs (arXiv:2611.32940). Models do not reliably know their own task-type weaknesses in advance. Implication for the harness: do not rely on the frozen model to self-report when a repair is needed; continue to require external paired evidence and independent probes.

**Proposed concrete tasks (2026-11-27):**
1. Extract same-task success/failure pairs from the last completed hard-bank series and author two candidate TransHarness-style intervention policies; evaluate them only on a frozen protected subset (paired seeds) and log recovery/regression.
2. Prototype a minimal claim-obligation certificate for three recent failures and require any subsequent repair proposal to reference it in the autonomy ledger entry.
3. Generate one ProbeAgent-style probe task for the highest-frequency failure mode observed in the last 10 runs and add it to the protected-case buffer.

**Question for operator:** Approve a controlled, non-production experiment that implements the TransHarness-style same-task contrast + protected-subset replay and the claim-obligation certificate check on a frozen subset of the hard bank (no production code changes, no hard-bank modifications)? Yes / No / Modify.
