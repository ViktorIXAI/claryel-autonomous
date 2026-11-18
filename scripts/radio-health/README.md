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
