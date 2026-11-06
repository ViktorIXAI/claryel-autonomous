# Independent preliminary review: why Codex/ChatGPT and Grok trail Contour on HARD v6.1

Date: 2026-11-06. Status: **preliminary, aggregate-level review; answer-by-answer audit pending**.

## Evidence and scope
- Source: `benchmarks/hard/v6-results/four-arm-v61/FOUR-ARM-V61.md`, `VS-V6.md`, `scripts/raw_v6.py`, `scripts/four_arm_v61_report.py`, `benchmarks/hard/bank-hard-v6.json`, `E-EXEC.json`, and `LADDER.md`.
- Same 71 single-shot task IDs; contour 0.0.2.28, raw Basalt, Codex CLI (configured `gpt-6.1-sol`, xhigh), Grok via Hermes CLI (`grok-4.7`). Six loop-D tasks excluded from cross-arm totals. The CLI configurations do not independently prove the precise served model builds.
- Strict /71: Contour 61, bare Basalt 56, Grok 54, Codex 50. Subsequent Contour 0.0.2.29 is 63/71 on v6.1, but the four-arm baseline is 0.0.2.28; do not present 63 versus old raw arms as a new matched four-arm experiment.
- Per-category (Contour / Basalt / Codex / Grok): A 7/7/7/7 of 9; B 5/7/6/6 of 7; C 5/5/5/4 of 8; D 3/3/3/3 of 3; E 10/10/10/10 of 10; F 6/4/0/4 of 6; G 6/5/5/5 of 6; H 4/1/0/1 of 5; I 6/6/6/6 of 6; J 5/7/7/7 of 7; K 4/1/1/1 of 4.
- F+H+K (15 tasks): Contour 14, Basalt 6, Codex 1, Grok 6. Other 56 tasks: Contour 47, Basalt 50, Codex 49, Grok 48. The observed deficit is concentrated in contract-sensitive categories, not broad evidence of inferior reasoning.
- Paired exact sign-test vs Contour 0.0.2.28: Codex p=0.0192, Grok p=0.1185, Basalt p=0.3323, one repetition only; no multiple-testing correction. Evidence of a score difference in this run is not evidence of general model superiority.
- Bank v6→v6.1 changed raw results unevenly (Basalt 49→56, Codex 49→50, Grok 59→54). Original raw answer rows did not preserve model/CLI/bank provenance; runner was later amended. Do not attribute Grok's shift to a specific cause.

## Preliminary explanations, NOT established causes
1. Contour has deterministic validation, format repair, retry/normalization and task-specific gates; raw arms get one unassisted answer. This is a system-vs-model comparison, not an equal-tools comparison of intrinsic intelligence.
2. F diagnostic JSON, H safety evidence/claim fields, K exact field lines/boolean/tax normalization are likely strict-contract failure modes. Verify against literal answers before classifying any failure as semantic, formatting, scoring, refusal, or transport.
3. Model execution differs: Basalt direct HTTP temp 0.7 and seeded; Codex CLI read-only with xhigh; Grok Hermes CLI with toolsets disabled. Actual sampling, system prompts, CLI stdout wrapping, truncation, finish codes and served model IDs require evidence.
4. All arms scored 10/10 on E; independently verify that each generated artifact was executed in an isolated Docker fixture and that the oracle did not accidentally reuse cached outputs or references.

## Required evidence-preserving audit
1. Freeze immutable input bank bytes and SHA-256, task IDs, reference answers, scorer code and SHA, raw response bytes for each arm, response finish status, CLI/stdout/stderr (sanitized), execution timestamps, model ID as reported by provider if available, parameters, transport version, tool policy, run IDs, prompt template and environmental metadata. Store sanitized public artifacts plus private integrity manifest where needed. Never publish secrets, private endpoints, tokens, private user data, or chain-of-thought.
2. Generate a 71-row cross-arm audit table: task ID/category, prompt/ref, verbatim final answer or evidence link, parser result, strict checker verdict, failure notes, independent semantic verdict, repairability without new inference, and classification: semantic error / contract-format error / checker defect / bank ambiguity / refusal / truncation / transport failure / unresolved. Preserve originals; never rewrite historical answers.
3. First audit every F/H/K cell (15 × 4), then all disagreements, then all 71. Human-review ambiguous cases blind to arm identity; dual reviewers and adjudication for disagreement. Independently inspect F/H/K scorer semantics and K synonyms, H evidence constraints, F JSON aliases.
4. Verify the 40 E-category execution records against actual container inputs, generated programs, outputs, oracle, cache keys, and isolated reruns. Ensure model answers were not replaced by references.
5. Run controlled factorial ablations: each model raw; each with the SAME deterministic parser/normalizer; each with SAME retry budget and tool access; each with its native full agent stack; and Contour with individual gates disabled. Report both exact-contract and semantic correctness, latency, calls, tokens, energy/cost and intervention provenance. Never silently supply reference answers to fix model output.
6. Run >=5 predeclared repeats per arm if budget permits (prefer 10), randomized interleaved arm order, pinned bank/scorer/versions and fresh external holdout. Report paired confidence intervals, variance, category-wise counts, multiple-comparison caveats, and seed limitations.
7. Audit benchmark validity: references, ambiguous prompts, accidental leaks/keyword shortcuts, benchmark contamination, category weighting, and changes from v6 to v6.1. Keep v6/v6.1 separate; disclose known defects. Compare on common eligible cells only.
8. Publish a reproducible, source-linked report with examples of *actual* failures and corrected scoring, plus uncertainty and limitations. Maintain a changelog and explicit owner review for security-relevant changes.

## Acceptance criteria
- Every published score cell can be traced to immutable prompt, raw answer, scorer version and evaluation record.
- At least 15 F/H/K tasks have four-arm, answer-by-answer classification and concrete cited examples.
- Semantic and strict-format scoreboards are separate; E execution is independently reproduced.
- A fair-controls experiment is completed or clearly marked blocked, and all unsupported claims are removed.
- Existing issues #6, #7, #8, #9, #11, #14 and #15 are cross-linked; respect owner pause #13 and security approvals #11.

**Owner-requested Hermes execution guidance:** Investigate, preserve evidence, propose fixes and PRs; do not modify frozen historical banks/results or production/security settings without explicit owner authorization. Report blocked access honestly. No fabricated model responses, scores, or evidence.

_Report authored by ChatGPT — OpenAI GPT-6; based on published repository artifacts, not an independent replay of original model answers._
