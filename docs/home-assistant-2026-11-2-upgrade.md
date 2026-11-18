# Home Assistant upgrade: 2026.7.1 -> 2026.11.2 (with verified backup)

Date: 2026-11-18 (01:52-02:00 CET). Host: the CLARYEL desk station (`claryel-it-home-001`).
Result: **done — Home Assistant Core 2026.11.2 is live, zero errors, history and registries intact.**

## What runs and where

| Item | Value |
|---|---|
| Container | `homeassistant`, compose project `claryel-box`, `network_mode: host`, `privileged: true`, restart `unless-stopped` |
| Image before / after | `home-assistant:2026.7.1` -> `home-assistant:2026.11.2` (4 monthly releases) |
| Config dir | `/srv/claryel/config/homeassistant` (32 MB, no custom_components, no HACS) |
| Image pin (runtime) | `HOME_ASSISTANT_IMAGE` in the station env file (line 81) |
| Image pin (desired state) | `stations/claryel-it-home-001/home-assistant/managed.yaml` in the fleet repo |
| Zigbee | ZHA via `/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0` -> `/dev/ttyUSB0` |
| Policy in fleet file | `automaticMajorUpdates: false`, `backupBeforeUpdate: true`, `validateConfigurationBeforeRestart: true` |

The jump was an explicit owner request, not an automatic major update.

## Backup taken before the change

`/srv/claryel/backup/homeassistant/pre-upgrade-20261118T005249Z/` (22.1 MB):

- `home-assistant_v2.db` — consistent copy via the SQLite backup API (handles WAL correctly)
- `zigbee.db` — same method
- `config-files.tar.gz` — everything else (556 entries: `.storage/`, `configuration.yaml`, `zha_quirks/`, `blueprints/`), live DB/WAL excluded
- `claryel-box.env.bak`, `compose.zigbee.yaml.txt`, `MANIFEST.sha256`

Verified after writing: `PRAGMA integrity_check` -> `ok` for both databases, `sha256sum -c` -> OK for all
files, 43 864 state rows and 4 721 events present in the copy. (The config dir still carries a
`home-assistant_v2.db.corrupt.2026-08-01...` marker from an old incident, which is why the pre-change
backup is done through SQLite's backup API rather than a raw file copy.)

## Upgrade sequence that was used

1. `check_config` with the **new** image against a **copy** of the config dir (never the live one):
   clean, only registry migrations pending (`core.device_registry` 1.12 -> 3.4,
   `core.entity_registry` 1.22 -> 1.24, `repairs.issue_registry` 1.2 -> 1.3).
2. `docker pull ghcr.io/home-assistant/home-assistant:2026.11.2` (old image kept for rollback).
3. Fleet desired state bumped and committed locally: `home-assistant(claryel-it-home-001): pin 2026.11.2`.
4. Station env bumped: `HOME_ASSISTANT_IMAGE=...:2026.11.2` (only that line changed; the previous file is
   saved next to the backup set as `claryel-box.env.bak`).
5. Recreated the single service with the station's own compose file set:
   `docker compose -p claryel-box ... up -d --no-deps homeassistant`.
6. Startup check: 0 ERROR lines, no deprecation warnings, HTTP 200 on the UI, `claryel-home-assistant-bridge`
   stayed healthy through the restart.

Root-free execution detail: the config dir and env file are root-owned and the agent has no passwordless
sudo, so every privileged step (read config, write env, run compose) ran inside a container that runs as
root and gets the host paths bind-mounted. Nothing on the host was chowned or sudoed.

## Post-upgrade verification

| Check | Before | After |
|---|---|---|
| Recorder state rows | 43 864 | 44 028 (still writing) |
| Recorder events | 4 721 | 5 115 |
| `core.entity_registry` entries | 173 | 180 (7 new entities added by the new version) |
| `core.device_registry` devices | 22 | 22 |
| Areas | 8 | 8 |
| SQLite integrity (live DB) | — | `ok` |
| Zigbee (ZHA) | quirks loaded | quirks loaded, `switch.sonoff_zbminil2` available |
| TV | `media_player.timvision_box_2` present | present (box itself offline at that hour) |
| HA's own migration backup | — | `core.device_registry.20261118_005541.migration_backup` |

## Backup automation added with the upgrade

The station had no recurring Home Assistant backup at all (the snapshot dirs on the backup volume covered
other services). Now:

- `~/.hermes/scripts/ha-nightly-backup.sh` — nightly consistent SQLite copies + config tar + integrity gate
  + `sha256sum` manifest, keeps the newest 14 sets, silent on success, exactly one alert line on failure.
  Tool image `claryel/ha-backup:1` (alpine + sqlite) so the run needs no package installs.
- `~/.hermes/scripts/ha-backup-fresh.sh` — guard: alerts if the newest set is older than 30 h (dead cron,
  full disk, machine off).
- Cron `Home Assistant nightly backup` (`1543ceb6ca6d`) at 03:00, and
  `Home Assistant backup freshness guard` (`c105d208189c`) at 09:00 and 21:00; both deliver to chat plus
  Home Assistant push, and stay silent when nothing is wrong.
- Both paths were exercised for real: success run produced a verified set (independent `sha256sum -c` -> OK),
  and a forced-failure run produced exactly one `HA BACKUP FAILED:` line with a non-zero exit.

## Rollback (kept possible)

```bash
# revert the pin, then recreate the one service
sed -i 's|^HOME_ASSISTANT_IMAGE=.*|HOME_ASSISTANT_IMAGE=ghcr.io/home-assistant/home-assistant:2026.7.1|' <station env file>
docker compose -p claryel-box <same -f list> up -d --no-deps homeassistant
```

The 2026.7.1 image is still in the local image store. If the config itself were damaged, restore
`config-files.tar.gz` plus `home-assistant_v2.db`/`zigbee.db` from the pre-upgrade set into the config dir.

## Follow-ups

- The fleet policy commit is local only: that repo is `ahead 4, behind 11` against its git primary and the
  other 4 commits belong to in-flight work by other agents, so it was not pushed. The station reconciler
  reads the working tree, so the pin is effective now.
- `compose.boot-approval.simulation.yaml` still carries `2026.7.1` defaults for the disabled
  `homeassistant-boot` / `homeassistant-main` boot-control profiles; not enabled, bump on next boot-stack work.
