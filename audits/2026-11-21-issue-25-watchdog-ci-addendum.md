# Issue #25 audit addendum — latest watchdog change and CI evidence

- Audit date: 2026-11-21
- Audit time: 14:20 CET / 13:20 UTC
- Scope: bounded review of commit `3e5d7006734277990f87e6f4448b63cf38514522` and the GitHub Actions results attached to that HEAD.
- Provenance: this addendum is append-only. It does not rewrite `docs/taverna-camera-and-ghost-on-2026-11-20.md`, prior audit addenda, historical field notes, frozen results, or production/security policy.

## Verified repository state

- Repository: `ViktorIXAI/claryel-autonomous`
- Default branch: `main`
- Issue #25: **open**
- Latest HEAD at inspection: `3e5d7006734277990f87e6f4448b63cf38514522`
- Repository permissions exposed by the connector: admin/maintain/push/triage/pull
- Topics observed: `ai-safety`, `autonomous-agents`, `benchmark-harness`, `llm-evaluation`, `local-ai`, `reproducible-research`

## New commit reviewed

Commit `3e5d700` changes:

1. `docs/taverna-camera-and-ghost-on-2026-11-20.md`: adds a dated operational note describing two successful relay reload probes, the resulting one-second `unavailable` blips, and the reason successful probes should be silent.
2. `scripts/tavern-motion/motion-tavern-watch.sh`: adds a `PROVED_MARK` state file and a six-hour hold-down after a successful probe; successful HTTP 200 reloads no longer print routine output, while non-200 responses still emit a failure line.

This is an operational behavior change, not merely documentation. The diff is preserved by the commit URL and is not restated as a claim of independent field reproduction.

## CI evidence on this HEAD

Observed GitHub Actions runs created for `3e5d700`:

- `hard-v6 scoring contracts`: **failure**
- `secret-scan`: **failure**
- `contour self-tests`: **failure**
- `devsecops`: **success**
- `pages build and deployment`: **success**

The presence of successful workflows does not offset the failed gates. No acceptance claim is made for the current HEAD.

## Disposition

- The change is recorded as a current operational observation plus an implementation change with explicit provenance.
- The six-hour hold-down and the new `PROVED_MARK` path require independent verification for state-file lifecycle, stale-state recovery, and alert behavior after a real failure. Those checks were not executable through the available connector and were not inferred.
- The failed `secret-scan`, `contour self-tests`, and `hard-v6 scoring contracts` remain blocking evidence for issue #25.
- No credentials were inspected or guessed; no security policy, production setting, frozen benchmark, or historical record was modified.

## Remaining acceptance gaps

1. Complete repository-wide path inventory with explicit coverage evidence.
2. Independently verify the new watchdog path and its error handling.
3. Resolve or explicitly disposition the failed CI gates, especially `secret-scan`.
4. Complete independent QA and owner-question reconciliation.
5. Preserve issue #25 as open until all acceptance criteria are independently verified.
