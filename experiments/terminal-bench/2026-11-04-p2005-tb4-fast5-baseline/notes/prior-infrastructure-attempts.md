# Prior fast-baseline infrastructure attempts

These attempts are recorded because all attempts should be visible, but they are not counted in the fast-five model result.

## Built-in Harbor Hermes bootstrap

- Job: `tb4-fast-baseline-20261104-013524`
- Result: 6 exceptions, 0 trials entered the agent phase.
- Cause: the built-in Harbor Hermes bootstrap ran `hermes version`; Hermes v0.22.6 expects `hermes --version`.
- GPU telemetry during the attempt remained idle: mean approximately 8 W, zero GPU utilization.

## Repaired six-task run with one aborted trial

- Job: `tb4-fast6-baseline-repair-20261104-015224`
- `coq-block-bound` entered the agent phase and ran for approximately 1h08m.
- Harbor then failed during log collection with `RuntimeError: Event loop is closed`.
- No verifier result or reward was produced, so the task was not counted.
- GPU telemetry during the attempted agent phase averaged about 73.6 W, with an active-phase energy estimate of about 70.9 Wh.

The fast-five run excludes `coq-block-bound` and uses the corrected Hermes adapter without `VerifiedHermes`, without `task-discipline`, and without the Claryel Autonomous Harness contour.
