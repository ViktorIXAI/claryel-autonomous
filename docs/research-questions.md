# Research questions — answered so far, and what stays open

## RQ1 — Autonomous development
*Can an AI agent analyze its own system's failures, hypothesize, implement,
test, detect regressions, reject its own versions, save tokens, raise speed
without quality loss, cut releases, and pick the next direction?*

Answered for a concrete case: **yes inside the rails below**, evidenced by
v1.0→v1.9 (see `docs/autonomy.md` per-cycle ledger):

| capability | evidence |
|---|---|
| find causes of failure | v1.9: scorer/contour wiring mismatch diagnosed from ledger notes, not guessed |
| propose hypotheses | one-hypothesis-per-version chain in the decision log |
| write code + tests | `gate_fixers.py` + 12-case refusal suite; `gate_v19_d_test.py` before the fix |
| run trials | paired overnight A/B series, resumable runners, smoke-before-launch |
| detect regressions & reject versions | v1.4 banned, v1.5 no-op, v1.6 rejected — all agent-authored, agent-measured, agent-rejected |
| optimize tokens without quality loss | v1.7: −31% input tokens, 19/19 vs 19/19 |
| choose next direction | CHRONIC/LOTTERY/FIXED classification feeds the next version's hypothesis |

Open edges of RQ1: long-horizon drift (weeks, not two days), cross-domain
transfer (the protocol was never run outside these benchmark families), and
fully unsupervised adoption (we deliberately keep a human veto; see
`docs/EVOLUTION.md`).

## RQ2 — What a frozen model can do
Same weights, better software: avg content 0.905 → 0.933 (B2003, but see
plan-mix caveat), paired +0.047/+0.051 at v1.9, D-ea 0.34 → 1.00, input
tokens per attempt down ~30%+ from v1.3 to v1.7 with equal correctness.
**System-level gains, not model capability gains** — the labels in every
table keep the two apart. Open: how much of the remaining gap (F ≈ 0.68) is
contour-addressable at all.

## RQ3 — Hardware efficiency
Identical contour on identical plans: RTX 3060 12 GB / 24 GB RAM desktop vs
M3 Ultra 256 GB unified vs an RTX 5090-class laptop box for probes. Findings
so far: the consumer box completes the same 11-category suite at roughly half
decode throughput of the workstation, with per-attempt seconds ≈ 2×; seed
identical pairing makes cross-box deltas interpretable; heavy retry
categories run 3–4× slower than daytime rates on the small box.
Passports + sensor matrices in `hardware/`. Open: standardized power cost per
correct answer (B2003 has no per-component power meter; `not_available` is
recorded, not estimated).

## RQ4 — Local + cloud cooperation under a local privacy boundary
Designed, not yet measured (`docs/privacy-architecture.md`,
`benchmarks/privacy-boundary/`). Honest status: in *this* published record the
agent ran fully local-network; no cloud model received any of the data here;
the cooperation experiment is scheduled work, not a result.

## Anti-self-deception (cross-cutting)
Because the agent builds, tests and grades its own system, the protocol
forces: frozen references, paired methodology, independent recompute tooling
(`analytics/aggregate.py` + `results/independent-validation.md`), published
regressions, and format-repair never being counted as reasoning improvement.
Contradictions get published, not hidden.
