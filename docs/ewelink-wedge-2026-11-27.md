# eWeLink integration wedge — 2026-11-27

## Symptom
- 20:00 UTC relay went `unavailable`; watchdog printed
  `RELAY PROBE FAILED: eWeLink entry reload http=000 while rssi and switch were stale for 1795s`.
- House egress fine (200/301), HA API fine (answered in 1 ms) — so neither WAN nor HA was down.

## Diagnosis
- HA log: `Cloud WS Connection error: WSMessageTypeError('Received message 257:None is not WSMsgType.TEXT')`
  plus a stuck task in `custom_components/sonoff/core/ewelink/base.py dispatcher_wait`.
- The config-entry reload endpoint (`/api/config/config_entries/entry/01M7P.../reload`) **hung**:
  watchdog's 20 s curl got `http=000`; a manual 60 s curl also hung. A wedged websocket makes the
  reload task deadlock — retrying the reload does not help and leaves another stuck task behind.

## Fix (verified)
- `docker restart homeassistant` → HA API back in ~25 s; relay back `off`, rssi −60, fresh telemetry
  at 20:04:56. Outage total ~5 min.
- Zigbee fallout: none this time — garden TS0201 reported 5.6 °C right after restart; only the
  already-dead office `wing_ts0201_2` remained unavailable.

## Watchdog change
- `motion-tavern-watch.sh`: when the reload call returns `000`, print
  `RELAY RELOAD HUNG ... run: docker restart homeassistant` instead of the normal reload line, and
  push `RELOAD_MARK` forward by 3000 s so the hung endpoint is not hammered every 10 minutes.

## Rule of thumb
`http=000` from the reload probe = the eWeLink task is deadlocked (not a network blip): one
`docker restart homeassistant` clears it; do not keep reloading.
