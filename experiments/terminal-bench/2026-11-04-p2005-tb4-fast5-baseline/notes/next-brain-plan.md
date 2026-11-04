# Terminal-Bench next experiment: strongest local brain

Date: 2026-11-04

## Current baseline

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
