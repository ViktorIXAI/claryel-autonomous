# Claryel Agent Lab — Project Rules

This project uses a single Hermes profile (`default`) with Kanban tasks as
logical agents. Do **not** create a separate Hermes profile for every role.
Roles are task contracts, not long-lived visible agents.

## Board

Project board: `agent-lab`.

Logical roles are written in task titles and bodies:

- `CO-1 coordinator` — plans, decomposes, audits, synthesizes.
- `RUN-1 experiment-runner` — runs one bounded experiment and writes a ledger.
- `HWE-1 hardware-estimator` — collects public price snapshots and cost tables.
- `SEC-1 security-auditor` — scans artifacts and reports rule/path/count only.
- `DOC-1 publisher` — sanitizes and publishes research artifacts.

A coordinator may create child Kanban cards, but all child cards remain assigned
to `default` unless the maintainer explicitly approves separate profiles.

## Safety rules for every agent

1. No hostname, private IP, local username, SSH key path, token, password,
   cookie or personal account data may be committed or published.
2. Secrets and connection settings stay in local untracked configuration.
3. Security reports outside the repository use rule IDs, paths, commits,
   release names and counts; never secret values.
4. Browser profiles, cookies, login stores, cache and session state are never
   packaged.
5. External mutating actions require explicit maintainer approval.
6. Existing Git history and Releases are not deleted or rewritten without a
   separate maintainer decision.
7. New machines are onboarded first as idle workers; smoke tests are bounded
   and must not contaminate active paired gate runs.

## Experiment contract

Every worker card must finish with:

- input task or plan;
- exact command configuration;
- artifact paths or public asset names;
- result table;
- failures/retries;
- next recommended action;
- explicit statement whether data is safe to publish.

## Price-watch contract

Price cards publish dated snapshots only:

- component, model, MPN/SKU when available;
- condition: new / refurbished / used;
- region and currency;
- observed price and date;
- stock state when known;
- public offer URL;
- source class;
- no affiliate or tracking parameters.

The goal is a reproducibility dataset:

```text
hardware -> benchmark quality -> speed -> energy -> accepted result -> cost
```
