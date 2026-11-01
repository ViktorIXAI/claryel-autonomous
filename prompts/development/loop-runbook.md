# The loop runbook (how the agent drove itself)

What made the version chain possible was not code but a **protocol** the
operator set and the agent recorded for itself. Reconstructed here from the
agent's own run notes and one-shot cron prompts; where text is the agent's
verbatim log output it is marked as such (Russian originals in
`history/agent-decisions/gate-versions.en.md`).

## Standing rules the operator imposed (paraphrase)

1. "Never stop when idle": with no new orders the agent continues the cycle —
   analyze results → new gate/validator version → new series → compare.
2. Each new version is built **only** from the previous version's analyzed
   failures (final results + ledger), with **exactly one substantive change**.
3. Launches overnight; morning report mandatory; alerts only on events.
4. Reports to a human: verdict first (fine / middling / bad), numbers only
   where middling or bad.

## What the agent scheduled for itself

* **Mid-night diagnostic crons** (one-shot, attached to the running series):
  each one pulls partial artifacts, aggregates, classifies failures, and
  proposes **exactly one hypothesis** for the next version. Cron diagnoses;
  only the main session builds and launches. (Pattern: `docs/EVOLUTION.md`.)
* **Morning report** (one-shot; verbatim task given to the reporting session,
  translated from Russian): *"Morning technical report 07:30. First run
  `morning.sh`; it pulls v1.8 and v1.9 artifacts into `v18-final`/`v19-final`
  and runs the report scripts…"* — the script itself is this repo's
  `analytics/aggregate.py` lineage.
* **Stop discipline**: series are stopped only via `harness/stop_series.sh`
  (matches the process by its `PARB_STATE` env var, never by a cmdline regex
  that could match the killer itself).

## The agent's own words as evidence

The decision log entry for v1.4 is a worked example of self-correction —
abbreviated translation:

> "v1.4 (cheap repair without source): BANNED. … CAUSE (clarified after
> v1.5): v1.4 had two changes at once — (1) repair without the source
> document and (2) repair attempts limited to one. The cheap repair never
> ran at all… What actually broke it was the retry cap: fixes 29 → 16 and
> unfinished format gave wrong numbers. Conclusion: repair attempts must not
> be capped; save tokens another way."

That entry cost the agent two wasted versions; it is kept verbatim because
it is the most reusable part of the lab.

## Running the loop yourself

`docs/EVOLUTION.md` restates the protocol as reproducible steps with the
commands in this repo. The protocol is model-agnostic: nothing in it refers
to this benchmark's categories — it operates on `results-*.jsonl` +
`gate-ledger-*.jsonl` shapes only.
