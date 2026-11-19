# Radio health watchdog (Zigbee)

`radio-health-watch.py` reads Home Assistant `/api/states` and reports only Zigbee trouble:
a device that went offline, LQI below 40, RSSI below -92 dBm, battery below 25 %.
If Home Assistant itself cannot be read it prints `HA UNREADABLE: http=NNN` instead of
staying silent - a watchdog that cannot read its source is worse than no watchdog.

Findings are deduplicated in `~/.local/state/claryel-radio-watch/state.json`: the same set of
problems is repeated at most once every 24 h, and any change (new problem, recovered device)
is reported immediately. Empty stdout means nothing is delivered.

Cron job `e671b3f908dc` runs it at 08:00 and 20:00 (`no_agent`, delivered to bot-chat and
Home Assistant). The live copy is `~/.hermes/scripts/radio-health-watch.py`; this is the mirror.

Why the mesh needs a router at all, and what the L2 module can and cannot do:
`docs/zigbee-mesh-2026-11-18.md`.

## Battery rule (added after a false alarm)

A TS0201 battery channel is noisy: one sensor reported 1 % while the same device reported 100 % an hour
later, and its 60-day history holds four distinct values. The watchdog now records the last low reading
in `batt_low` inside its state file and only alerts when the **same device reads low twice in a row**.
A real dying battery is caught within a day; a single artefact never produces an alert.

## What it also watches: commands that never arrive (added 2026-11-18 night)

**One incident is reported once.** The container log window rolls (12 h), so counting every
hit inside it would re-alert the same incident on every run until it ages out. The scan keeps
a watermark (`deliv_seen` in the state file) and counts only lines stamped after it. HA writes
`2026-11-18 21:59:32.132+01:00 ...` with ANSI colour codes in front, and traceback
continuation lines carry no stamp of their own - the nearest preceding stamp is used, which is
what an unhandled exception in an automation does to these log lines.

A Zigbee device can look perfectly online in HA and still refuse every command: ZHA logs
`MAC_NO_ACK` / `NWK_NO_ROUTE` when a send never reached it. That is invisible in `/api/states`, so the
watchdog also scans `docker logs --since 12h homeassistant` and alerts when more than 5 sends failed,
naming the automations involved. This is how the ZBMINI L2 incident was found: 34 failed sends in 12 h
while its switch entity looked healthy.

Dedup keys have their digits replaced (`LQI=#`), so a sensor whose LQI bounces 7 -> 0 -> 21 stays one
problem instead of re-alerting on every tick.
