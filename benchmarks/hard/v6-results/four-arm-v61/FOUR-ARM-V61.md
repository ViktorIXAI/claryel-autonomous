# Four-arm on bank v6.1 (contour 0.0.2.28)

Bank `benchmarks/hard/bank-hard-v6.json` (v6.1), scorer `harness/parb_check_v6.py`, one rep.
Common set = 71 single-shot tasks scored in every listed arm; loop-D is N/A for raw arms (single-shot chat cannot emit the loop trajectory). Category E is scored by re-running the fixture battery in docker (`scripts/e_exec_v61.py`, cached in `E-EXEC.json`): 10 E tasks, 40 of 40 arm-by-task cells executed.

| arm | answers scored | strict on common set /71 | wins vs contour | losses vs contour | exact sign-test p |
|---|---|---|---|---|---|
| contour | 71 | **61/71** | - | - | - |
| codex | 71 | **50/71** | 15 | 4 | 0.0192 |
| grok | 71 | **54/71** | 11 | 4 | 0.1185 |
| basalt | 71 | **56/71** | 11 | 6 | 0.3323 |

## Per category (strict / n on the common set)

| cat | contour | basalt | codex | grok | n |
|---|---|---|---|---|---|
| A | 7/9 | 7/9 | 7/9 | 7/9 | 9 |
| B | 5/7 | 7/7 | 6/7 | 6/7 | 7 |
| C | 5/8 | 5/8 | 5/8 | 4/8 | 8 |
| D | 3/3 | 3/3 | 3/3 | 3/3 | 3 |
| E | 10/10 | 10/10 | 10/10 | 10/10 | 10 |
| F | 6/6 | 4/6 | 0/6 | 4/6 | 6 |
| G | 6/6 | 5/6 | 5/6 | 5/6 | 6 |
| H | 4/5 | 1/5 | 0/5 | 1/5 | 5 |
| I | 6/6 | 6/6 | 6/6 | 6/6 | 6 |
| J | 5/7 | 7/7 | 7/7 | 7/7 | 7 |
| K | 4/4 | 1/4 | 1/4 | 1/4 | 4 |

Loop-D (contour arm only): 5/6 strict — D-ex6-l0=1, D-ex6-l1=1, D-ex6-l2=1, D-ex6-l3=0, D-ex6-l4=1, D-ex6-l5=1

Raw-arm transports: basalt direct HTTP temp 0.7 seed 1000+rep; codex CLI xhigh
read-only; grok hermes CLI with toolsets disabled and the prompt inline (finding S3).
Reproduce: `python3 scripts/four_arm_v61_report.py` (add `--include-exec` on a docker host).
