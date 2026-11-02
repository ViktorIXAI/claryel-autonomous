# Claryel Autonomous Harness

**An open local-AI automation harness for measuring model tasks, answer
quality, latency, memory, power and cost on real machines.** The system runs a
frozen model against a fixed task bank, records every attempt, repairs safe
harness mistakes by code, and compares versions only with paired evidence.

This is a working engineering project, not a finished product. It publishes
accepted versions, rejected versions, broken runs and hardware limits. The
main question is practical: how much reliable local AI can be obtained on
affordable hardware without hiding failures?

```
same model  ·  same frozen task prompts  ·  same seeds
        only the software around the model changes
```

An AI agent developed and tested many harness changes under operator rules.
The operator set objectives, constraints, publication scope and final adoption
decisions. The agent's own work is itemized in [`docs/autonomy.md`](docs/autonomy.md);
its limits are in [`docs/limitations.md`](docs/limitations.md).

Status checked: 2026-11-02

## Current version

The version scheme is four digits: `A.B.C.D`.

| part | meaning | current value |
|---|---|---|
| `A.B` | operator release line; the operator changes these first two digits | `0.0` |
| `C` | contour track; `1` is the first contour family, `2` is the second | `2` |
| `D` | contour revision inside that track | `4` for the full-Mac resource decision and current tooling release |

Current mapping:

| canonical version | legacy name | meaning | status |
|---|---|---|---|
| `0.0.1.9` | `v1.9` | D action-order normalization | full accepted baseline |
| `0.0.2.0` | `v2.0` | G/H post-normalization | accepted on Mac pair; B2003 partial |
| `0.0.2.1` | `v2.1` | H safety normalization | full Mac pair used as baseline; full P3001 complete |
| `0.0.2.2` | `v2.2` | F diagnostic grounding | full Mac paired run accepted: +0.0438 overall, +0.3259 F, 0 regressions |
| `0.0.2.3` | — | resource telemetry and documentation policy | current measurement release |
| `0.0.2.4` | — | full-Mac resource/economic verdict | current release line |

Legacy `v1.x` and `v2.x` names still work as inputs. New reports should use the
canonical four-part form.

## Current status

| item | status as of 2026-11-02 |
|---|---|
| P2005 targeted F smoke | complete; `0.0.2.1 -> 0.0.2.2`, 30 paired rows, 0 regressions |
| Mac targeted F smoke | complete; 30 paired rows, 0 regressions |
| P3001 targeted F smoke | complete; 30 paired rows, 0 regressions, perfect answers 3 -> 30 |
| Mac full `0.0.2.2` paired run | complete with resource telemetry; 2513 paired rows, +0.0438 overall, 0 regressions |
| B2003 offline replay | complete; recorded F answers replayed through `0.0.2.2`, n=323 |
| resource telemetry | permanent for full paired gates and hardware-class runs |
| documentation freshness | daily policy added; scheduled check added |

## Headline results

The numbers below are paired where they compare versions. Raw means across
different plan mixes are not comparable.

### F diagnostic grounding, targeted subset

`0.0.2.1 -> 0.0.2.2`, same task, same repetition, same seed:

| machine | pairs | answer score | better | unchanged | worse |
|---|---:|---:|---:|---:|---:|
| P2005 | 30 | 0.7167 -> 1.0000 | 29 | 1 | 0 |
| Mac Studio | 30 | 0.7500 -> 1.0000 | 30 | 0 | 0 |
| P3001 | 30 | 0.7167 -> 1.0000 | 27 | 3 | 0 |

Recorded B2003 `0.0.2.1` F answers replayed offline through `0.0.2.2`:
n=323, every F task average becomes 1.0000.

### Resource and cost side of the answer

The P3001 RTX 3060 12 GB targeted F smoke with 1 Hz telemetry measured:

| metric | value |
|---|---:|
| answer mean | 0.9944 |
| perfect attempts | 29 / 30 |
| latency median | 5.88 s |
| latency p95 | 7.96 s |
| peak VRAM used | 11,385 MB of 12,288 MB |
| VRAM headroom | 903 MB |
| peak GPU power | 113.4 W |
| estimated GPU energy | 0.15 Wh per attempt |

The important engineering lesson: answer quality alone can look acceptable
while the 12 GB GPU is already near its safe memory boundary. This is why
resource telemetry is now part of the testing method.

## How to use it

The runner uses Python standard library only. It works with any OpenAI-compatible
endpoint:

```bash
git clone https://github.com/ViktorIXAI/claryel-autonomous
cd claryel-autonomous
./install.sh
cp config.example.sh config.sh
source config.sh
bash run_gate.sh
python3 harness/gate_report.py
```

Set `PARB_API`, `PARB_MODEL`, `PARB_KEY_FILE` and `PARB_BOX` in `config.sh`.
For full paired gates, also set `PARB_TELEM` to a JSONL path; `run_gate.sh`
then starts the resource collector automatically and stops it when the run
finishes.
Select a contour generation with `PARB_GATE_VERSION`, for example `0.0.2.2`.

For paired A/B work, keep the same plan, task bank, per-task seeds and machine
passport. The method is documented in
[`docs/reproduction-guide.md`](docs/reproduction-guide.md).

## Documentation policy

The landing page is maintained daily and checked by a script. It must remain
short, dated, structurally stable and free of inflated self-labeling. See
[`docs/documentation-policy.md`](docs/documentation-policy.md).

The daily check verifies:

- required README sections;
- a `Status checked:` date no older than one day;
- local links that still exist;
- forbidden public self-labels;
- version statements that point to the current versioning map.

## Source and citation policy

The operator reads scientific, economics and sociology articles and cites them
when useful. External sources are recorded as methods, context, comparisons or
warnings. They are not used as automatic proof of this repository's results.
See [`docs/source-policy.md`](docs/source-policy.md) and
[`sources/reading-list.md`](sources/reading-list.md).

## Where the evidence lives

| area | location |
|---|---|
| version chronology | [`versions/VERSIONS.md`](versions/VERSIONS.md) |
| full results and summaries | [`results/summary-full.json`](results/summary-full.json) |
| independent second-opinion scorer | [`analytics/second_opinion.py`](analytics/second_opinion.py), [`results/independent-scorer.md`](results/independent-scorer.md) |
| hold-out bank | [`benchmarks/holdout/`](benchmarks/holdout/), [`results/holdout-mini.md`](results/holdout-mini.md) |
| resource telemetry | [`telemetry/README.md`](telemetry/README.md) |
| hardware passports | [`hardware/`](hardware/) |
| failures and rejected versions | [`history/failures/failures.md`](history/failures/failures.md) |
| agent decision log | [`history/agent-decisions/gate-versions.en.md`](history/agent-decisions/gate-versions.en.md) |
| open engineering and economic questions | [`docs/open-questions.md`](docs/open-questions.md) |

## Repository map

```text
docs/        operating policy, methodology, source policy, limitations, roadmap
harness/     runner, contour gates, validators, fixers, tests
benchmarks/  task banks, visual benchmarks, performance and privacy boundaries
versions/    version records, including rejected versions
history/     decision logs, failures, rollbacks, external inputs
hardware/    machine passports and measured hardware profiles
telemetry/   resource sampler, join tools, overhead notes
results/     summaries, paired deltas, independent validation notes
schemas/     schemas for runs, telemetry, hardware and experiments
analytics/   reproducible aggregation scripts
logs/        artifact index and samples
prompts/     contour prompts used in measured runs
experiments/ A/B runners and classification helpers
```

## What "self-improving" means here

The model weights are frozen. The measured improvement is the software around
the model: gates, validators, retries, repair paths, safety blocks and
measurement tooling. This is not a claim that the model's weights have learned
to improve themselves.

## Updates

Announcements are published on X: [@uctive](https://x.com/uctive).
Owner profile: [LinkedIn](https://www.linkedin.com/in/viktor-khudiakov-44a5447b).

MIT licensed. Keep the decision logs if you fork this: the failures and rejected
versions are as important as the accepted ones.
