# Prompts

- `testing/` — contour prompts verbatim (nudges, refusals, retries, agent-loop
  system prompt) with English translations, and task-prompt examples.
- `development/` — the loop runbook: the protocol and operator standing rules
  under which the agent drove its own version chain.
- `history/` — pointer: decision-bearing text lives verbatim in
  `history/agent-decisions/gate-versions.en.md` (translation; verbatim Russian archived in the ru-source-records release asset).

Contour text changes are reviewable in one place (`harness/gate_run.py`);
prompts/ mirrors them so reviewers never have to diff 1,200 lines of runner
to see what the harness says to the model.
