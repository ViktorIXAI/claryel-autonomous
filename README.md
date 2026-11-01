# Claryel Autonomous Harness Lab

**Open Research into Autonomous Local AI Evolution**
*An AI-built, self-improving harness for local language models.*

This is an open research experiment, not a finished commercial product.

We investigate whether local AI systems can autonomously develop and improve
their own software harnesses — discover failures, write code, test changes,
optimize performance, and evolve over time. The project also explores
cooperation between local and cloud AI, with locally-enforced privacy
boundaries. The same frozen model is measured across very different
hardware, from an affordable consumer GPU to a high-memory workstation.

**The full research history matters more than impressive benchmark numbers.**
Every version below — including the rejected ones — ships with its decision
record. Results are preliminary until independently verified; the tooling for
that independent verification is part of this repository.

```
same model  ·  same frozen task prompts  ·  same seeds
        only the software around the model improves
```

Every line of the published code — runner, validators, mechanical fixers,
task bank, A/B tooling, experiment scripts — was written, tested, benchmarked
and (sometimes) rolled back by an autonomous AI coding agent between
2026-10-30 and 2026-11-01, under an operator who set the standing rules.
Who did what is itemized in [`docs/autonomy.md`](docs/autonomy.md): no human
work is claimed as autonomous, and nothing autonomous is hidden behind "the
team".

## Live research infrastructure

| what | where |
|---|---|
| public dashboard (built only from repo JSON) | https://viktorixai.github.io/autonomous/dashboard/ |
| automatic publication pipeline + watchdog | [`scripts/publish/pipeline.py`](scripts/publish/pipeline.py), package index [`logs/PIPELINE-PACKAGES.md`](logs/PIPELINE-PACKAGES.md) |
| every contour generation incl. rejected, auto-aggregated | [`results/summary-full.json`](results/summary-full.json) |
| independent second-opinion scorer + its dissent | [`analytics/second_opinion.py`](analytics/second_opinion.py), [`results/independent-scorer.md`](results/independent-scorer.md) |
| dedup-rule sensitivity of published deltas | [`results/dedup-sensitivity.md`](results/dedup-sensitivity.md) |
| held-out bank (never used in dev) + pilot | [`benchmarks/holdout/`](benchmarks/holdout/), [`results/holdout-mini.md`](results/holdout-mini.md) |
| per-run telemetry (run_id-bound) + join | [`telemetry/`](telemetry/), example [`telemetry/runs/smoke-tel-4.join.json`](telemetry/runs/smoke-tel-4.join.json) |
| privacy-boundary gateway prototype + tests | [`benchmarks/privacy-boundary/`](benchmarks/privacy-boundary/) |
| CI: self-tests, data sanity, link integrity, and a `reproduce` job that re-hashes the public archive and recomputes the published summary | [`.github/workflows/selftest.yml`](.github/workflows/selftest.yml) |

## What "self-improving" means here — and what it does not

The model is **frozen** end to end: identical GGUF weights
(`qwen3.8-flash-next-iq3_s`, served over an OpenAI-compatible API), identical
task prompts, identical per-(task, repetition) seeds. No fine-tuning, no
weight editing, no prompt rewriting on the measured tasks. Improving the
harness is *not* evidence of improving the model's own capabilities — we
measure the whole system and label the parts.

The **harness** (the lab calls it the *contour*): structured-output gates,
code validators, mechanical form fixers, refusal retries, max-token ladders,
and safety blocks around agent-style tasks. Every published delta is a
contour-only delta.

## Headline results (recomputed from raw ledgers, pinned snapshot)

Two physically different machines ran the identical frozen plan — a consumer
desktop (**B2003**: RTX 3060 12 GB, 24 GB single-channel DDR5) and a
high-memory workstation (**Mac Studio**: M3 Ultra, 256 GB unified) — so every
version delta is paired per `(task, rep)` *and* replicated on independent
hardware. `results/summary.json` recomputes byte-identically from the release
archive via `analytics/aggregate.py` (pinned snapshot `release-2026-11-01`;
the v1.9 series was still running when it was frozen — in-progress vs final
is marked, never mixed).

| contour | B2003 n / avg content / format | Mac n / avg content / format |
|---|---|---|
| v1.2 (first full series) | 590 / 0.905 / 92% | 645 / 0.823 / 94% |
| v1.7 (code-only form repair) | 717 / 0.905 / 92% | 1317 / 0.887 / 93% |
| v1.8 (targeted nudges) | 3117 / 0.880 / 89% | 2513 / 0.875 / 92% |
| **v1.9 (slot normalization)** | **2127 / 0.933 / 97%** | **2416 / 0.926 / 100%** |

Raw means across versions are *not* comparable (the plan mix changed); the
honest numbers are the **paired deltas**:

| change | pairs | avg Δ content | improved : regressed |
|---|---:|---:|---|
| v1.7 → v1.8 (B2003) | 717 | +0.012 | 43 : 21 (weak cats H +0.18, F +0.04) |
| v1.8 → v1.9 (B2003) | 2127 | **+0.047** | 229 : 79 |
| v1.8 → v1.9 (Mac) | 2416 | **+0.051** | 183 : **0** |

Cost curve (same-seed A/B, from the decision log): v1.3→v1.7 cut input
tokens **−31%**, generation −24%, wall time −19%, model calls spent on form
**−45%**, with zero quality loss (19/19 vs 19/19).

The single biggest win is a **diagnosis, not a patch**: category D-ea scored
0.34 for three versions straight. v1.9 found the model was never wrong — the
contour emitted a prose tool-sequence while the scorer demanded JSON steps.
A 20-line mechanical normalization took D-ea from **0.34 → 1.00** on both
boxes (`logs/samples/D-ea-v18-example.json` vs `D-ea-v19-example.json`).

## What the agent got wrong (kept in the repo, not hidden)

* **v1.4** bundled two changes (cheap repair + retry cap). 19/19 → 3/19
  correct answers. The log pinpoints the retry cap as the real killer — the
  cheap-repair branch never even executed (dead code). Banned.
* **v1.5** added a guard that fired **zero times** in the whole A/B — an
  unexercised guard is an unverified guard.
* **v1.6** saved 45% input tokens and cost 3/19 correct financial answers.
  The skeleton guard passed every corrupted answer (skeleton intact, values
  wrong). Rejected for finance tasks.
* **v2.0** is published as experimental: 18 probe rows, one box, not adopted.
* Two runs invalidated by harness bugs are preserved as named artifacts
  (`…401-invalid`, `…partial-harnessbug`) — see `history/failures/`.

Full chronology: [`versions/VERSIONS.md`](versions/VERSIONS.md) (English);
primary source: [`history/agent-decisions/gate-versions.log`](history/agent-decisions/gate-versions.log)
(the agent's own decision log, verbatim Russian).

## Two ways to use this lab

**Mode 1 — run the finished v1.9 harness against your own local model.**
Any OpenAI-compatible endpoint (llama.cpp, vLLM, Ollama, LM Studio, …),
Python ≥ 3.9, standard library only:

```bash
git clone https://github.com/ViktorIXAI/autonomous
cd strata-autonomous-harness
./install.sh                       # venv + contour self-tests (12 fixer cases, D-normalizer contract)
cp config.example.sh config.sh     # set PARB_API / PARB_MODEL
source config.sh
bash run_gate.sh                   # 178 tasks × 11 categories, resumable, budgeted
python3 harness/gate_report.py     # per-category scores, costs, failure causes
```

**Mode 2 — Autonomous Evolution Mode.** The loop under which the contour
grew — measure → diagnose → one hypothesis → smoke → paired A/B → cross-box
replication → accept/reject → append to the decision log — is documented
with its rails in [`docs/EVOLUTION.md`](docs/EVOLUTION.md). Adoption requires
paired evidence; three agent-authored versions were rejected on numbers the
agent itself generated. Safety rails: [`docs/SAFETY.md`](docs/SAFETY.md).

## Repository map (research-infrastructure layout)

```
docs/          mission, research questions, methodology, autonomy ledger,
               hardware methodology, privacy architecture, limitations, roadmap
harness/       runner + contour v1.9: gates, validators, fixers, plan builder,
               baseline (contour-free) control runner
benchmarks/    text-gates/    11 categories A–K, 178 frozen synthetic tasks + self-tests
               browser-visual/ WebGL/SVG code-gen contour (single-shot 1/5 → 5/5)
               performance/   speed-vs-quality methodology
               privacy-boundary/ design + planned tests (status stated honestly)
versions/      v1.0…v1.9 records incl. rejected + code-snapshot status
history/       timeline, agent decisions (verbatim log), failures, rollbacks,
               human interventions
hardware/      per-machine passports (live-verified), launch configs, change log
telemetry/     phase-1 collector + CSV, sensor-availability matrix
results/       summary.json, version comparisons, regressions, independent-validation
schemas/       run / telemetry / hardware / experiment record schemas
analytics/     aggregator that reproduces every published number
logs/          SHA-256-pinned artifact index + samples (raw archives: Releases)
prompts/       development / testing — contour prompts verbatim + translations
experiments/   A/B runners, deep-probe classifier (CHRONIC/LOTTERY/FIXED), audits
```

Research questions answered so far and what stays open:
[`docs/research-questions.md`](docs/research-questions.md).
Known limits of this record: [`docs/limitations.md`](docs/limitations.md).
Roadmap by stages: [`docs/roadmap.md`](docs/roadmap.md).

## Provenance and licensing

Built by **[Hermes Agent](https://github.com/NousResearch/hermes-agent)**
(Nous Research, MIT) operated by Viktor Khudiakov on home-lab hardware
(passports in `hardware/`) — every instruction in the experiment, including
all "improve the harness" directives, reached the lab through that agent.
Serving engine: **[Strata](https://github.com/Niko1221/Strata)** by Niko1221
and contributors (MIT) — not part of this repo and not required; any
OpenAI-compatible endpoint works. The benchmark subject is
**[Qwen3.8-Flash-Next](https://huggingface.co/Qwen/Qwen3.8-Flash-Next)**
(Qwen team, Alibaba Group), in the recommended IQ3_S build from
**[ISTA-DASLab](https://huggingface.co/ISTA-DASLab/Qwen3.8-Flash-Next-GSQ-RCO-GGUF)**
(Institute of Science and Technology Austria). No weights redistributed —
identifiers, sizes and SHA-256 in `hardware/inventory/model-iq3s.md`.
Full credits: **[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md)**.

MIT licensed (`LICENSE`). Publication edits vs the exact run snapshots are
itemized in `PUBLICATION-NOTES.md`. Keep the decision logs if you fork this —
they are the part with the most value.

> Publish the evidence, not just the claims.
> Preserve the failures, not just the successes.
> Measure the entire system, not just the model.
