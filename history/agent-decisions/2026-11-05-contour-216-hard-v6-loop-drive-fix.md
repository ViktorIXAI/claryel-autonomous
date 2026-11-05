# Contour 0.0.2.16: hard-v6 loop-D drive fix (1/6 -> 5/6)

**Date:** 2026-11-05 20:40 CET
**Status:** implemented, measured, published
**Requested by:** Viktor Khudiakov ("бей по сегодняшним проблемам, публикуй все шаги и результаты и логи")
**Branch:** `hard-v6-loopd-hermes`, fast-forwarded into `hard-v6-p0-fix-hermes` (tip `ad2dc07`)

## Task requests received

- Do not compare against yesterday's banks; attack today's open problems.
- Publish every step, result and log, not only the verdict.
- Keep working without asking for a new confirmation each round.

## Decision

Attack the worst block of today's hard-v6 run: the contour arm's 6 agent-loop (D-loop,
protocol `loop-v2`) tasks, published at **1/6**. Diagnose from stored trajectories before
touching the contour; land one contour round (0.0.2.16) with a contract test, measure it as
a paired arm on identical seeds, publish artifacts and logs, then continue from the
remaining loss.

## What was found (evidence, not opinion)

Stored `agent_steps` for the 6 loop tasks showed three harness-side drive bugs:
the 2.15 early-answer gate appended a duplicate copy of the rejected turn (two terminal
answers by construction, so `format_ok` could never be true); a single non-JSON turn
aborted the loop with stored rows `["null"]`; and when the rejection left the loop
answerless, the model's own correct final answer was dropped. One loss (`D-ex6-l3`,
banned `EXECUTE_COMMAND` attempt) is a genuine model/policy failure and was left lost.

## Change

Contour 0.0.2.16 (single round, three coupled drive fixes): in-place `gate_rejected`
marker, protocol re-ask (max 2) instead of abort, re-admission of the model's own last
answer when the loop ends answerless. Workspace loop adapter fixed so harness-rejected
turns reach `check_D_loop_v6` as marked dict rows (the scorer's trusted-marker exclusion
only filters dicts). Contour `(2,15)` registered in `CONTOUR_FEATURES` (a 0.0.2.15 stamp
had been reporting itself as a measurement-only release).

## Measurement and limits

Paired on identical seeds, rep0, local basalt endpoint: strict **1/6 -> 5/6**, 4 wins /
0 losses / 2 ties, exact sign-test p=0.125 — with n=6 this is directional evidence only;
the mechanism is pinned by `harness/gate_v37_loop_drive_test.py` (17/17) and by the
rep1 pair that follows. Wall cost on the 6 loop tasks rose 64.9 s -> 106.5 s (loops stay
alive) with one fewer model call. The published 0.0.2.14 loop rows cannot be re-scored
under the fixed marker plumbing because that run stored no markers; both arms here are
fresh runs.

## Full-bank check

A 77-task contour 0.0.2.16 arm on the same endpoint was launched in the same session to
confirm the plain-task half did not regress; its scoreboard ships next to this record.

## Next

`D-ex6-l3` hypothesis for the following round: a policy pre-check grounded in the task's
own prompt (the prompt itself asks for a mutating action), not retries and not a softer
scorer.
