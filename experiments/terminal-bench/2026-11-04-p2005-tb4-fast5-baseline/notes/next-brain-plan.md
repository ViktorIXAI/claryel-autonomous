# Terminal-Bench next experiment: strongest local brain

Date: 2026-11-04

## Run A final result (2026-11-04, completed)

Job finished after 7 h 09 min 13 s over five tasks, one attempt each:

| task | outcome | trial wall time | active GPU energy |
|---|---|---:|---:|
| `embedding-drift-monitor` | solved, 11/11 tests | 10 min 34 s | 6.57 Wh |
| `fin-saccr-rwa` | failed, 22/24 tests | 1 h 09 min | 73.25 Wh |
| `mp-checkpoint-consolidation` | failed, 3 h agent timeout, 0/4 tests | 3 h 03 min | 102.44 Wh |
| `risk-scorer-replay` | infrastructure abort, no inference | 4 min 30 s | 0 Wh |
| `shadow-relay` | failed, 0/4 tests after 2 h 38 min | 2 h 41 min | 168.97 Wh |

Scored: 1 solved of 4 scored attempts (25%), mean reward 0.200. One trial is excluded from the percentage as an infrastructure failure.

Energy for the whole run: 351.2 Wh of active GPU energy, 376.0 Wh including idle samples, average active power 70.2 W, peak 80.4 W, GPU temperature never above 60 °C.

Three run-quality defects were found and must be fixed before the next arm:

1. **Session exports are empty on long trials.** Only the 10-minute trial produced a usable Hermes session export; the 1 h, 3 h and 2 h 41 min trials all wrote 0-byte session files, so token and call counts are missing for them. Token comparisons between arms are therefore not yet possible.
2. **The inference queue deadline can end a trial.** `shadow-relay` was killed by "inference queue wait deadline expired" after three retries. The cause is confirmed in the serving config on P2005: `max_queue = 3` with `queue_timeout = 20` seconds, so any request that waits more than 20 s behind the three queued slots is rejected by the server, Hermes retries three times and exits. A 20 s queue budget is far below the prefill time of long agent contexts. Raising it (the server accepts 0.1–600 s) requires restarting the inference service, which briefly interrupts the production brain, so it is pending an owner decision.
3. **`risk-scorer-replay` cannot install Hermes.** Reproduced twice: `hermes pm repair` exits 1 with `pm install failed` inside that task image. Local reproduction narrowed it: the same image as root installs and repairs Hermes fine under the same 4 GiB / 2 CPU budget, while the image's default `nobody` user (HOME=/nonexistent) cannot even create a home directory. So the blocker is Hermes' package bootstrap under an unprivileged agent account with a tight storage/memory budget, not the task itself. Fix direction: pre-provision Hermes for the task image instead of installing it per trial.

## Baseline snapshot used for the plan above (superseded by the final table)

Fast five-task baseline, no Claryel Autonomous Harness:

- Job: `tb4-fast5-baseline-20261104-070835`
- Agent: Hermes v0.22.6, bare baseline adapter
- Model: Qwen3.8 Flash Next IQ3_S on P2005 / Strata 0.2.10, engine 0.1.56
- Limit: 3 hours per task
- Result at first completion: `embedding-drift-monitor` solved, 1/1 completed
- Tokens: 26,044 input, 22,351 output, 620,650 cache-read
- GPU energy observed: about 37 Wh active, average 70.6 W

Two earlier infrastructure attempts are published separately and are not counted as model successes.

## Strongest available inference resource

Mac Studio M3 Ultra, 256 GiB unified memory:

- DeepSeek V4.1 Flash file already present: `DeepSeek-V4.1-Flash-1017-IQ2_XXS-Q2_K-imatrix.gguf`, 341 GiB
- Server: `ds4-server`
- Context: 32768 for the benchmark arm; a later 524288 single-session run can be tested separately
- Measured profile on clean memory: approximately 1,555 tok/s warm prefill, 701 tok/s cold long prefill, 26.7-31.4 tok/s decode
- Hermes currently uses P2005 Qwen. This is a candidate model, not an automatic replacement.

## Experiment design

Run the same five fast tasks with the same runner and no custom harness:

1. **A — P2005 Qwen baseline** (`tb4-fast5-baseline-20261104-070835`)
2. **B — Mac Studio DeepSeek baseline**
   - Host: Mac Studio M3 Ultra 256 GiB
   - Inference: `ds4-server`, OpenAI-compatible endpoint
   - Same five tasks, 3-hour cap, one attempt, sequential
   - `VerifiedHermes`: no
   - `task-discipline`: no
   - Claryel Autonomous Harness: no
3. **C — winning brain + harness**
   - Use the better brain from A/B
   - Same five tasks
   - Add only one controlled harness feature at a time
   - Compare solved tasks, wall time, model calls, tokens, and energy

## Decision rule

Choose DeepSeek over Qwen only if it solves more tasks or produces materially better failure analysis without exceeding the benchmark time budget.

Expected risk: DeepSeek is expected to be about 3-4 times slower in decode than Qwen on this fleet. A 3-hour cap is therefore the decisive constraint. A task that needs 22k output tokens may still fit, but long tool loops can exceed the cap.

## Energy accounting

- P2005 GPU telemetry is available and already running at 10-second intervals.
- Mac Studio wall power is unavailable without a socket meter. `powermetrics` adds sampling overhead and will not be run during a benchmark arm.
- Mac arm will report energy as `wall power: no data` and use runtime/token throughput for comparison.

## Safety and resource rules

- Do not stop the current fast5 run.
- Do not start DeepSeek while P2005 is actively running the current baseline.
- Do not stop the Mac Studio Qwen serve during file inspection or preparation.
- DeepSeek requires stopping the Mac Qwen serve before loading its 341 GiB model; do that only after the current fast5 run finishes and before starting arm B.
- All attempts, including infrastructure failures, are published.
