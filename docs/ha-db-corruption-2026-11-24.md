# HA recorder DB corruption found by the backup gate, 2026-11-23/24

## What the watchdog caught

The nightly backup job (cron 1543ceb6ca6d) failed twice, 2026-11-23 03:00 and 2026-11-24 03:00, with
`core db integrity check did not return ok`. The gate is `PRAGMA integrity_check` on the consistent
`.backup` copy of `home-assistant_v2.db` — a copy that only breaks when the source is broken.
Nightly sets up to 2026-11-22T020048Z are `ok`, so the damage happened between 03:00 on the 22nd and
03:00 on the 23rd. No host reboot (last boot Nov 17), no kernel I/O errors, md0/md1/md2 all `[UU]`.

## Live state when found

`PRAGMA quick_check` on the live DB (read-only via `claryel/ha-backup:1` container, config mounted `:ro`)
agreed: `statistics_short_term` (rootpage 15) plus indexes `ix_states_last_updated_ts`,
`ix_states_old_state_id`, `ix_statistics_short_term_*` were damaged — "invalid page number" pointing past
`pragma_page_count` and "2nd reference to page" in one b-tree. It was growing: Nov 23 listed pages up to
6428, live quick_check up to 6706 (page_count 6215). By Nov 24 only Tree 15 (the table itself) still
reported — the recorder had rebuilt the index trees, the table pages stay corrupt. HA itself logged no
sqlite errors; the recorder just keeps writing.

Precedent found during the swap: `/srv/claryel/config/homeassistant/home-assistant_v2.db.corrupt.2026-08-01T18:23:29+00:00`
— someone (past me) already quarantined a corrupt v2.db in August. Recurring failure mode, not one-off.

## Fix applied, 2026-11-24 03:04-03:06 CET

1. `sqlite3 live ".recover" | sqlite3 recovered.db` against the live DB. The `sqlite_stat1` parse errors
   are a known `.recover` quirk (internal table cannot be created); they are harmless.
2. Recovered DB: `PRAGMA integrity_check` = **ok**; counts events 11161, states 65485, statistics 62462,
   statistics_short_term 65204, recorder_runs 14 — history preserved.
3. `docker stop homeassistant` → moved the corrupt file to
   `/srv/claryel/backup/homeassistant/pre-dbfix-20261124T0306Z/home-assistant_v2.db.corrupt`,
   removed `-wal`/`-shm`, copied the recovered DB in as `home-assistant_v2.db` → `docker start`.
   HA down ~20 s, API back with 200.
4. Verified: new DB `integrity_check ok`, events table growing (11161 → 11546 within two minutes),
   recorder warning "could not validate ... shutdown cleanly / Ended unfinished session (id=158 from
   2026-11-20)" is expected after the swap, WAN egress fine.
5. Ran the nightly backup manually: rc=0, `2026-11-24T02:06:02Z ok` in `~/.hermes/logs/ha-backup.log`.

## Why this is the right fix, not "ignore it"

`home-assistant_v2.db` holds recorder history and statistics only; config lives in `.storage` JSON, which
was untouched. Left alone, the corrupt b-tree would keep spreading until the recorder purge or a statistics
query hits it and HA starts logging errors or crashes the recorder task. The backup gate is now the proven
detector: it fired two days in a row and never wrote a "green" night over a corrupt DB.

## Follow-ups left open

- Root cause unknown (no reboot, no I/O errors in kernel log; possible kill during WAL checkpoint or
  container-level interruption; second occurrence since August). If it happens a third time, look at
  whether HA is being OOM/force-killed (`docker inspect` OOMKilled, `docker events`).
- The corrupt set `nightly-20261124T020043Z` stays in the backup dir as evidence until retention (14 sets)
  prunes it.
