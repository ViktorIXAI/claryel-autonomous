# Contributing

This is a research record first and a tool second. The rules below exist to
keep the record trustworthy.

## Non-negotiables

1. **The decision log is append-only.** Never edit `history/agent-decisions/`
   or any frozen artifact (`logs/INDEX.md` hashes pin them). Corrections go in
   a new dated entry.
2. **Frozen prompts and references are frozen.** Do not edit task text,
   `ref` values or scorer thresholds to make statistics look better — that
   action is the definition of a failed experiment here. Changing a scorer is
   allowed only as a *versioned contour change* evaluated with paired A/B
   under `docs/EVOLUTION.md` rules, with the change visible in results.
3. **One substantive contour change per version.** Paired `(task, rep)` A/B
   on the same frozen plan before adoption; cross-box replication required
   for adoption.
4. **Failures stay in.** A version that regresses gets a post-mortem, not a
   deletion. Regressions are reported in `results/`.
5. **Unmeasured means `null`/`not_recorded`** — never a guessed number.

## Adding a benchmark series

Add tasks via `harness/parb_bank.py` generators (deterministic seeds), freeze
a new bank + plan, record `plan_hash`, then follow the version protocol.
Category letters are never reused with a new meaning.

## Adding a machine

Add a hardware passport under `hardware/inventory/` (live-collected, per
`docs/hardware-methodology.md`), register sensor availability honestly
(`not_available` is a valid value), and record every configuration change in
`hardware/changes/`. Comparisons must name machines by passport id.

## DevSecOps automation

Every push and pull request runs:

- contour unit tests, v1.9/v2.0/v2.1 contracts;
- bank and plan sanity checks;
- privacy-boundary tests;
- link integrity checks;
- JSON/JSONL and schema validation;
- dependency-policy checks;
- Gitleaks secret scanning with a self-test canary;
- release asset scanning for published archives.

For local pre-push gating, install and run:

```bash
scripts/devsecops/install_hook.sh
scripts/devsecops/prepush.sh
```

The repository ships a `.git/hooks/pre-push` installer pattern; if the hook is
present, these gates run before each push. Raw security scanner reports are kept
outside the public repository.

## PRs

PRs that touch `harness/` must state: hypothesis, files changed, test run
(`install.sh` self-tests at minimum), and paired A/B numbers for contour
changes. PRs that touch results need the same paired methodology.
