# Four-arm on bank v6.1 (contour 0.0.2.28)

Bank `benchmarks/hard/bank-hard-v6.json` (v6.1), scorer `harness/parb_check_v6.py`, one rep.
Common set = 3 single-shot tasks scored in every listed arm; loop-D is N/A for raw arms (single-shot chat cannot emit the loop trajectory), category E = exec pending, excluded.

| arm | answers scored | strict on common set /3 | wins vs contour | losses vs contour | exact sign-test p |
|---|---|---|---|---|---|
| contour | 3 | **3/3** | - | - | - |
| codex | 61 | **2/3** | 1 | 0 | 1.0000 |
| grok | 42 | **2/3** | 1 | 0 | 1.0000 |
| basalt | 61 | **2/3** | 1 | 0 | 1.0000 |

## Per category (strict / n on the common set)

| cat | contour | basalt | codex | grok | n |
|---|---|---|---|---|---|
| A | 3/3 | 2/3 | 2/3 | 2/3 | 3 |

Raw-arm transports: basalt direct HTTP temp 0.7 seed 1000+rep; codex CLI xhigh
read-only; grok hermes CLI with toolsets disabled and the prompt inline (finding S3).
Reproduce: `python3 scripts/four_arm_v61_report.py` (add `--include-exec` on a docker host).
