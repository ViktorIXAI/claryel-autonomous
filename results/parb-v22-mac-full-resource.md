# Mac Studio full paired result: `0.0.2.1` vs `0.0.2.2` with resource telemetry

Run completed on 2026-11-02:

- machine: Mac Studio, Apple M3 Ultra, 256 GB unified memory;
- contour compared: `0.0.2.1` legacy `v2.1` vs `0.0.2.2` legacy `v2.2`;
- result rows: 2513 unique paired `(task, series, rep)` rows;
- plan: frozen Mac full plan;
- telemetry: 1 Hz collector, `telemetry/collector2.py`;
- telemetry coverage: 1734 / 2513 attempts had at least one resource sample.

## Quality result

| metric | `0.0.2.1` | `0.0.2.2` | delta |
|---|---:|---:|---:|
| content mean | 0.9394 | 0.9833 | +0.0438 |
| perfect attempts | 2006 / 2513 | 2344 / 2513 | +338 |
| format pass | 2513 / 2513 | 2513 / 2513 | 0 |
| improved pairs | — | 338 | — |
| unchanged pairs | — | 2175 | — |
| regressed pairs | — | 0 | 0 |

The full-suite improvement is concentrated in category F:

| category | pairs | `0.0.2.1` mean | `0.0.2.2` mean | delta | regressions |
|---|---:|---:|---:|---:|---:|
| A | 355 | 1.0000 | 1.0000 | 0 | 0 |
| B | 218 | 1.0000 | 1.0000 | 0 | 0 |
| C | 215 | 1.0000 | 1.0000 | 0 | 0 |
| D | 229 | 0.9956 | 0.9956 | 0 | 0 |
| E | 216 | 0.9930 | 0.9930 | 0 | 0 |
| F | 338 | 0.6741 | 1.0000 | +0.3259 | 0 |
| G | 194 | 1.0000 | 1.0000 | 0 | 0 |
| H | 187 | 1.0000 | 1.0000 | 0 | 0 |
| I | 187 | 1.0000 | 1.0000 | 0 | 0 |
| J | 187 | 1.0000 | 1.0000 | 0 | 0 |
| K | 187 | 0.7888 | 0.7888 | 0 | 0 |

This makes `0.0.2.2` a full Mac-suite accepted contour for the F-grounding
line, not only a targeted smoke. The remaining open weakness is K.

## Latency

Ledger seconds are the end-to-end attempt seconds recorded by the gate. They
include retries and ladder attempts, so they are not a single-request measure.

| latency metric | `0.0.2.1` | `0.0.2.2` | change |
|---|---:|---:|---:|
| raw ledger total | 28,088.7 s | 13,294.5 s | −52.7% |
| mean non-zero attempt | 12.13 s | 5.79 s | −52.3% |
| median non-zero attempt | 4.82 s | 2.15 s | −55.4% |
| p95 non-zero attempt | 15.57 s | 15.54 s | −0.03 s |
| p99 non-zero attempt | 177.35 s | 25.31 s | −85.7% |
| max | 2162.24 s | 369.12 s | −82.9% |

The reduction is mostly from fewer repairs/retries and the F grounding change,
not because the local model suddenly became faster. The tail improvement is
especially important: the old contour sometimes produced very long repair
chains.

## Resource telemetry for the Mac run

The 1 Hz collector produced 11,282 samples over 193.9 minutes. It did not
cover the first ~60 minutes because it was deployed after the run had already
started; the tool therefore reports coverage explicitly rather than
interpolating.

Mac is unified-memory Apple Silicon. With the default rootless collector it
exposes RAM but not dedicated VRAM or system power. Those fields stay
`not_available`; they are not estimated.

| resource | observed value |
|---|---:|
| peak RAM used inside attempt windows | 177,900 MB |
| median peak RAM used | 172,027 MB |
| minimum RAM available inside attempt windows | 133,631 MB |
| peak RAM wired | 88,205 MB |
| peak RAM compressor | 0 MB |
| dedicated VRAM | `not_available` on default macOS collector |
| system power | `not_available` without root `powermetrics` |

The Mac had large absolute memory headroom. That is the expected profile for a
256 GB unified-memory machine, and it explains why this hardware is safe for
the current model context configuration. The same measurement discipline is
the reason a 12 GB GPU profile must be judged separately.

## P3001 12 GB resource contrast

The paired P3001 RTX 3060 targeted F smoke had much less memory headroom:

| metric | P3001 RTX 3060 12 GB |
|---|---:|
| answer mean | 0.9944 |
| perfect attempts | 29 / 30 |
| latency median | 5.88 s |
| latency p95 | 7.96 s |
| peak VRAM used | 11,385 MB |
| total VRAM | 12,288 MB |
| VRAM headroom | 903 MB |
| peak GPU power | 113.4 W |
| estimated GPU energy | 0.15 Wh per attempt |

This is the practical justification for keeping resource telemetry in the
method: the answer-quality score alone hides the 92.7% VRAM boundary.

## Collector overhead estimate

The overhead is small enough for the measurement value:

- P2005 previous 5-task/46-record smoke: 60 s without collector, 60.2 s with
  1 Hz collector plus join.
- P3001 paired F smoke with telemetry was 14.3 s faster in total than the
  previous no-telemetry run, so collector overhead was below normal run-to-run
  variance.
- Mac storage cost: 11,282 samples ≈ 13.7 MB JSONL for a ~3.2 hour sample
  window.

## Permanence decision

Resource telemetry becomes a permanent part of the full paired testing
methodology.

Required for:

- every full paired gate run;
- every hardware-class evaluation, especially 8–12 GB GPU boxes;
- every acceptance/rejection decision where latency, memory, VRAM or power
  could explain a regression;
- every report intended to support an economic decision.

Optional for:

- tiny smoke runs when the machine is idle and the goal is only to check that
  the endpoint responds.

The default rule is:

```text
quality answer score + end-to-end latency + RAM/VRAM peak + power/energy
```

A pass on answer quality alone is not enough if peak memory is close to the
hardware boundary.

## Cost / benefit estimate

Actual engineering cost for the first version:

- telemetry join tool and contract test: about 2–3 hours of agent work;
- macOS RAM parsing and multi-GPU selection: about 1 hour;
- documentation, versioning and QA integration: about 2 hours;
- Mac full round: 4 hours 14 minutes machine time; human setup was minimal.

Ongoing cost:

- collector startup: automatic in future wrappers, zero manual steps;
- report generation: one command, seconds of CPU;
- storage: a few MB per run per collector window;
- risk: small, because the tool reports `not_available` instead of inventing
  missing sensors.

Benefit:

- prevents false acceptance on memory-tight hardware;
- makes quality gains comparable across machines;
- exposes tail latency and repair-chain cost;
- gives electricity/cost analysis a measured base;
- keeps public claims tied to actual hardware constraints.

Verdict: the benefit is clearly larger than the cost. Keep it permanently.
