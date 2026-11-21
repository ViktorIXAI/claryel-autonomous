# Taverna camera view in Home Assistant, and the relay that switches itself on

Date: 2026-11-20. Host: claryel-it-home-001 (claryel01), Home Assistant 2026.11.2 in Docker.

## What was wrong

Two light-ON events this morning that nobody ordered:

| local time | lamp state | motion events | how the state arrived |
|---|---|---|---|
| 08:19:06 | on -> off 08:29:07 | none in 14 h | `origin=device_push`, `context_user=none` |
| 09:15:34 | on -> off 09:18:48 | none | same |

The lamp is a SONOFF BasicR4 on Wi-Fi through the eWeLink **cloud** (custom `sonoff`
integration). The same integration logs repeated `Cloud ERROR: 504 Request Timeout` for this
device (2026-11-19 13:52, 15:17, 15:54, 17:26) and the entity went `unavailable` twice overnight
(22:20:45->22:20:52, 03:53:20->03:57:33). So the ON commands did not come from Home Assistant, from
the app user, or from the camera: the cloud/relay pushed them.

The visible damage was worse than a burning lamp: the greeting automation triggers on "the lamp
turned on, any source", so at 09:15 the machine greeted an empty room and started the radio bed
(09:15:45 -> 09:18:48).

## What changed

1. **The greeting is gated on presence.** `taverna_greeting_voice` now requires
   `binary_sensor.taverna_motion` on, or `input_boolean.tavern_motion_now` on, or
   `input_boolean.tavern_light_manual` on. A relay that switches itself on stays silent.
2. **A light nobody ordered is cut after 60 s** instead of 10 min: new automation
   `tavern_lamp_on_ghost_fast_off` (lamp on for `00:01:00` while the motion sensor is off and the
   manual flag is off -> `switch.turn_off`).
3. **The operator is told.** Cron job `9eb5c52d759a` runs `taverna-ghost-on-watch.py` every 5
   minutes and prints one line per uncommanded ON (deduplicated in
   `~/.local/state/taverna-greeting/ghost_seen`); empty output sends nothing.
4. **The camera can be watched from Home Assistant** (see below), plus a button for 5 fps.

Verified on 2026-11-20 09:18-09:21: an uncommanded ON at 09:18:53 produced **no greeting** and the
fast-off automation switched the lamp off at **09:19:53**, exactly 60 s later; the radio stopped and
0 audio containers were left.

## Camera path

Motion 4.6 on the host serves the webcam at 2 fps. It was given an MJPEG port that is bound to
loopback only (`stream_port 8125`, `stream_localhost on`), so nothing new is exposed on the LAN;
`webcontrol_port` stays 0.

    webcam -> Motion (2 fps, loopback :8125)
           -> taverna-camera-ctl.py (127.0.0.1:8126) -- /frame.jpg  single JPEG
                                                    -- /fps /boost /unboost
           -> HA Generic Camera "camera.127_0_0_1" (still_image_url=:8126/frame.jpg,
              stream_source=:8125/shot.jpg) -> dashboard "Таверна"

Why the extra hop: Home Assistant 2026 refuses `camera: platform: generic` in YAML (config entry
only, created through the config-flow API) and its `still_image_url` validator cannot read
Motion's `multipart/x-mixed-replace` answer ("unable_still_load"), so `camera-ctl` cuts one JPEG
out of the stream and caches it for 2 s.

Frame rate switch: Motion has no runtime API here, but its config file belongs to this user and the
unit re-execs on exit, so changing `framerate` and sending SIGTERM to MainPID switches 2 <-> 5 fps
without sudo. The dashboard button `input_boolean.taverna_camera_boost` calls
`rest_command.taverna_camera_boost` -> `POST /boost/<secret>`; the boost lasts `camera_boost_s`
(600 s) and then reverts to `camera_base_fps` (2) by itself and flips the button back off.
Verified both directions: 09:04 -> framerate 5 through the HA button, and back to 2 on OFF.

Each fps change restarts Motion, which re-runs its 30 s boot guard (no detection during it). That
is why 2 fps is the resting value and 5 fps is only for a look.

## Restart accounting (same day, after a watchdog alert)

The motion watchdog (`scripts/tavern-motion/motion-tavern-watch.sh`) alerted "restarted 2 time(s)
since last check" — both restarts were my own config/fps changes, not a fault. An fps switch is a
restart, so the watchdog needed to know which restarts were ordered:

- `taverna-camera-ctl.py` appends `epoch pid=… fps=…` to
  `~/.local/state/taverna-greeting/motion-restarts.log` **before** it signals Motion, then polls
  `ExecMainPID` (8 s) and reports `pid A -> B`. A switch that does not bring the service back returns
  `ok: false` with the unit state instead of claiming success — the earlier version answered
  `{"ok": true}` from the config write alone and never checked the restart.
- the watchdog state file now holds `"<NRestarts> <marker_lines>"`; only restarts beyond the markers
  recorded since the previous check are reported.

Verified live: fps switch through the API → one marker, `pid 2699640 -> 2721006`, watchdog silent;
`kill -TERM` on the MainPID with no marker → exactly one line
"restarted 1 time(s) since last check (total 10, 0 were fps switches)".

## Relay outage 11:07-11:19 (2026-11-20)

`switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1` went `unavailable` at 11:07:08 and returned `off`
at 11:19:37 (12.5 min). Home Assistant logged `Cloud ERROR: 504 Request Timeout` for the device, and
the OFF that the 3-minute hold tried to send at 11:11:58 failed with "Referenced entities … are missing
or not currently available".

Impact, stated plainly: motion was detected at 11:06:54 (somebody went downstairs), the ON command
never reached the relay, so the room stayed dark. While the entity is `unavailable`, every lamp guard
(the 60 s fast-off, the 10-minute guard, the watchdog's lamp branch) is blind - the watchdog's
`RELAY UNREACHABLE` line is the only thing that sees it, and that is what fired.

Recovery from the host: `POST /api/config/config_entries/entry/<eWeLink entry>/reload` - the entity
came back 45 s later. Safe here because the Zigbee devices live on a *different* config entry (checked
through the entity registry: the eWeLink entry owns only the 7 BASICR4 entities), so reloading it does
not touch the mesh. Confirm that ownership before ever reloading an entry; the REST entity-registry
endpoints are 404 in HA 2026, use WS `config/entity_registry/list`.

Root cause is now measurable: the integration ships `sensor.taverna_basicr4_sonoff_1002bd4e01_rssi`
and `..._connection` **disabled**; `scripts/tavern-motion/ha-enable-relay-diagnostics.py` turns them on
and they read **RSSI −72 dBm**, **connection = cloud**. A Wi-Fi relay at −72 dBm reachable only through
the eWeLink cloud explains the 504 timeouts, the two uncommanded ONs and this outage as one class.
What could actually change it needs a hand at the eWeLink app (DIY Mode / local control) or better
placement / a wired or Zigbee relay.

Log hygiene: the sonoff integration prints the per-device eWeLink apikey (a UUID) inside those WARNING
lines, so `docker logs` excerpts are never committed; the push gate carries a UUID rule for exactly this.

### Self-heal added after the 3rd drop (11:30)

The relay dropped three times in 25 minutes (11:07:08, 11:21:21 for 0.5 s, 11:30:30) and the integration
stopped refreshing the device on its own. The watchdog (`scripts/tavern-motion/motion-tavern-watch.sh`)
now does what was done by hand: on `unavailable` it reports the line with the last known
`rssi`/`connection`, then POSTs the eWeLink entry reload itself, at most once per 10 minutes
(`/tmp/motion-tavern/relay-reload.state`), and prints `RELAY RELOAD: … http=200`. Verified live at
11:31: alert + `http=200`, entity back to `off` 40 s later, next check silent. Measured RSSI on the two
replies: −72 dBm then −67 dBm — marginal, which is why this will keep happening until the relay gets DIY
Mode (local control), a better position, or a wired/Zigbee replacement.

## Files

- `~/.hermes/scripts/taverna-camera-ctl.py` — loopback fps switch + JPEG frame service
- `~/.hermes/scripts/taverna-ghost-on-watch.py` — uncommanded-ON watchdog (cron `9eb5c52d759a`)
- `~/.hermes/scripts/taverna-state-timeline.py` — state timeline for the lamp/motion/manual flag
- `~/.hermes/scripts/ha-add-generic-camera.py` — drives the Generic Camera config flow
- `~/.hermes/scripts/ha-taverna-dashboard.py` — WS: name the camera, create the "Таверна" dashboard
- `~/.hermes/scripts/taverna-greeting-ensure.sh` — keeper for the greeting listener and camera-ctl
- Home Assistant `/config/configuration.yaml` (+ `configuration.yaml.bak-ghost-20261120`,
  `configuration.yaml.bak-camera-20261120`)

Secrets (HA token, eWeLink credentials, the loopback path secrets) stay out of this repository.

## Can this relay be driven without the eWeLink cloud? (tested 2026-11-20)

Asked after a walk downstairs at 11:06-11:09 produced **no light**: motion was detected at 11:06:54
and the relay dropped at 11:07:08, so the ON never arrived. An earlier walk at 10:20:07 worked
normally (ON 10:20:07, OFF 10:23:23 = the 3-minute hold).

What was probed, with the tools in `scripts/tavern-motion/`:

- `mdns-ewelink-probe.py` - multicast query for `_ewelink._tcp.local.` (the zeroconf type the Sonoff
  integration uses to find LAN devices): **no answers on this LAN**.
- `relay-local-probe.py` - TCP 8081 against every host in the ARP table: **only a docker bridge answers**
  (uvicorn), no eWeLink LAN API. No ARP entry carries an Espressif/eWeLink OUI.
- Integration is `custom_components/sonoff` = **SonoffLAN 3.13.3**, whose `mode` option already defaults
  to `auto` (prefer LAN when the device is reachable). So the Home Assistant side is configured for
  local control; the device simply does not expose a local protocol here.
- Relay radio: **RSSI −72 dBm then −67 dBm**, `connection = cloud`.

Vendor reality (checked in the docs and the integration's issue tracker): the official DIY-mode list is
BASICR3 / RFR3 / MINIR2 / MINIR3 / D1 / SPM-Main / bulbs - **BASICR4 is not in it**, and the R4 generation
is reported by users to have lost DIY/local HTTP entirely; its "local" story is eWeLink-Remote
(Bluetooth) through an iHost gateway, which is another box.

Verdict: with this relay Home Assistant has no path except the eWeLink cloud, so "work locally, no
cloud" is not achievable for the tavern lamp as installed. Real options:

1. Replace the relay with a **Zigbee** relay on the existing CC2652 coordinator - fully local, and being
   mains-powered in the basement it becomes a Zigbee router, which also helps `wing_ts0201` (LQI 25) and
   the garden wing (LQI 40). Needs a neutral at the lamp box for some models - check before buying.
2. Replace with **BASICR3** (DIY mode = local HTTP on 8081) - local, but still Wi-Fi at −72 dBm.
3. Keep the cloud and live with the mitigations: 60 s cut of an uncommanded light, the watchdog reloading
   the integration entry by itself, and a loud phone alert the moment the relay is lost.

Mitigation 3 shipped the same day: automation `tavern_rele_nedostupno_ne_molchat`
(id `tavern_relay_unreachable_alert`) sends an iOS **critical** notification after the relay has been
`unavailable` for 60 s (config backup `configuration.yaml.bak-relay-alert-20261120`). Test-fired at
12:41:07 - `last_triggered` moved, no notify error in the HA log.

## Night test of the camera, 2026-11-21 03:33-03:53 (the camera has no night illumination)

Measured with the loopback still endpoint (`:8126/frame.jpg`) and ffmpeg `signalstats`:

| condition | YAVG | verdict |
|---|---|---|
| 03:33, lamp off, basement dark | 32.4 - 34.9 | noise floor; vision model rated usable detail **0/10**, no IR glow |
| 03:51, lamp on, same framing | 133 - 145 | picture is fine, framing kept |

So the USB webcam (`32e6:9251 USB Camera`, no IR LEDs, no IR-cut control exposed) is **blind when the room is
dark**. Both real detections on 2026-11-20 (10:20:06 and 11:06:51) happened when the basement already had
daylight; at night the chain cannot start by itself, because the first link (motion) sees nothing. Nothing
was bought or moved - this is a placement/ambient-light problem, and the fixes are free: aim the camera at the
stair/entrance area where light leaks in, leave a small night light in the basement, or run the lamp from the
manual flag `input_boolean.tavern_light_manual` during the hours the room is occupied.

What the same test proved about night use, stated carefully: motion event 3 started 03:51:48, two seconds
after `turn_on`, and ended 03:52:34 - but the frames taken after the lamp came on show **a person standing
in the background** (visible at 03:51 and still at 03:56, room YAVG ~140). The event therefore cannot be
attributed to the lamp alone: the room became visible for the camera at the moment the lamp lit. The useful
rule that follows is the one that matters at night - **the camera is blind until there is light, and works
normally the second the lamp is on**. So a night arrival can be handed over manually: switch the lamp on
from the phone (eWeLink app or the HA dashboard), and from that instant the camera and the 3-minute hold do
their job. Motion 4.6 also has `lightswitch_percent/frames` and no `lightswitch_ignore`, so a genuine
light-change event cannot be filtered in the daemon.

The relay dropped again during this test (entity `unavailable` from 03:53:03, the OFF command never reached
the device, so the lamp stayed physically on while the camera confirmed it: YAVG 143.7 at 04:01). The
watchdog reload was issued at 03:54:28 (`http=200`); `input_boolean.tavern_light_manual` was raised at
03:56:55 so the ghost-light cutoffs would not switch off the light of a person standing in the room.
Resolution: the `unavailable` window was **03:53:03 → 04:01:30** (8 min 27 s, the longest of the night), after
which the entity went `off` → `on` (04:05:02) - matching the lamp being physically lit, which the camera
confirmed. At the same moment `rssi` moved from **-69/-70** to **-53…-57 dBm** and `connection` became
`duplex`. No further reload had been issued after 03:54:28, so either the device recovered by itself or the
reload took several minutes - the two cannot be separated from these logs. Re-running the LAN probes at
04:05:57 still found **no `_ewelink._tcp.local.` announcement**, so `duplex` is the integration's own label
and not proof that the lamp can be driven without the eWeLink cloud. During the outage HA logged six
`Referenced entities … are missing or not currently available` warnings: every lamp automation was blind, as
expected.

## The relay flapped four times in one hour at strong signal, 2026-11-21 03:35-04:31

Recorder history for `switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1` between 03:35 and 04:31:

| `unavailable` from | back | how long |
|---|---|---|
| 03:35:52 | 03:40:10 | 4 min 18 s |
| 03:53:03 | 04:01:30 | 8 min 27 s |
| 04:16:18 | 04:16:19 | 1 s |
| 04:30:25 | 04:30:52 | 27 s |

`rssi` in that window: -70, -69 before the first two drops, then **-53 to -57 dBm** from 04:01 onwards - the
last two drops happened while the signal was good. The 504 `Cloud ERROR` line is logged by the integration for
this device at 03:53:08. Conclusion, replacing the earlier "weak signal is the single root cause": signal
quality is a contributing factor, not the cause - the eWeLink path blinks even at -55 dBm. That also means a
Wi-Fi repeater is worth having but will not make the lamp dependable by itself.

Watchdog change made from this data (`scripts/tavern-motion/motion-tavern-watch.sh`): besides the per-drop
alert it now counts `unavailable` transitions for this entity over the last 60 minutes from the HA recorder
and prints one `RELAY FLAPPY: N transitions (longest Xs)` line whenever that count grows, so the trend is
visible instead of a stream of identical alerts. Verified live: first run printed
`4 transitions ... longest 506s`, the next run stayed silent.

Operational note from this test: the mute failed because the automation was addressed by its YAML `id`
(`automation.taverna_greeting_voice`), which is **not** its entity id - the entity id comes from the alias
(`automation.taverna_italianskoe_privetstvie_i_muzyka_pri_vkliuchenii_sveta`). Calling
`homeassistant/update_entity_state` on the non-existent id returns 400 Bad Request; mute with
`automation/turn_off` against the alias-derived entity id instead. The test therefore played the greeting
and radio for ~20 s at 03:51 while the lamp was on.

## The operator added a dedicated Wi-Fi repeater in the tavern, 2026-11-21 ~04:00

The relay was moved onto the repeater's own access point (the tavern now has its own Wi-Fi network).
Measured around that change:

| | before | after |
|---|---|---|
| `rssi` | -69 / -70 dBm | **-53 to -57 dBm** steady (04:31-05:46) |
| `connection` | `cloud` | `duplex` (since 04:00:05) |
| cloud `504 / Request Timeout` in HA log | recurring | **0 in the following hour** |
| `unavailable` drops | 4 in the hour 03:35-04:31 | 04:16:18 (1 s), 04:30:25 (27 s), **none after 04:30:52** |

The two short drops right after the switch are the relay re-associating. So the repeater did what it should:
signal improved by ~14 dB and the hour since has been clean. It has **not** created a local control path:
`_ewelink._tcp.local.` still gets no mDNS answers, nothing on TCP 8081 belongs to eWeLink, and the ARP table
has 31 clients on the house `/24` with no Espressif/ITead OUI among them - the relay is on the repeater's own
network and is not visible from the house LAN at all. That is fine for cloud control and is an extra wall for
any future local control.

## The manual-light flag is now time-boxed to 4 hours, 2026-11-21 05:50

What was wrong: `input_boolean.tavern_light_manual` was raised at 03:56 for a camera test and was still on at
05:46 in an empty, dark room. While that flag is on, the 60-second uncommanded-ON guard stands down, so a
forgotten flag disables the protection for as long as nobody remembers it.

Added to `/config/configuration.yaml` (backup `configuration.yaml.bak-manual-timer-20261121`):

- `timer.tavern_light_manual` - 4 hours
- `automation.tavern_light_manual_armed` - raising the flag starts the timer
- `automation.tavern_light_manual_release` - the lamp going OFF ends the window (flag off, timer cancelled)
- `automation.tavern_light_manual_expiry` - `timer.finished` drops the flag and writes a logbook line

Verified live: flag ON gave `timer.tavern_light_manual = active, 4:00:00`; restarting the timer with
`duration: 00:00:05` expired and the flag went `off` by itself, timer back to `idle`.

Pitfall found while doing it: `automation/reload`, `timer/reload` and `input_boolean/reload` all answer 200
even when the YAML insert never happened - the first attempt added the three automations but skipped the
timer, because the insert guard matched the `input_boolean:` helper block which already contains the same
name. After any helper reload, query the new entity id over `/api/states/...`; the HTTP code proves nothing.

## The relay alert at 06:16 was a symptom: the house lost the internet, 2026-11-21 06:08

Triage of `RELAY UNREACHABLE` (drop 06:08:57, "back" 06:15:58):

- egress from claryel01 is dead: `https://example.com` and `http://1.1.1.1` both fail, `ping 1.1.1.1` loses
  100 %, and name resolution through the house router (`homenet.telecomitalia.it` resolver) returns nothing
- Home Assistant logs the same cause: `Cloud WS Connection error: ClientConnectorDNSError` repeated
  06:08-06:16, and `Can't load devices` at 06:15:52
- the Hermes Telegram adapter disconnected at the same time and its reconnects fail - so **Telegram-delivered
  alerts do not arrive during a WAN outage**, and HA push to the phone goes through the cloud as well
- the LAN is fine: LAN peers answer, Docker/HA/Zigbee/Motion/camera all healthy, RSSI of the relay sensor
  was -56/-57 just before the drop

The important correction about local control: after the reload the `..._connection` sensor read **`local`**,
which looks like the repeater finally gave the relay a LAN path. It did not. The integration's own data for
the device has `local: True` but `host = None`, and every command raises inside
`custom_components/sonoff/core/ewelink/local.py:183` - `host = device["host"]` → **`KeyError: 'host'`**
(repeated 06:16-06:20). The ARP table holds 31 clients on the house `/24` and the relay is not one of them,
because the repeater serves its own network. So `local`/`duplex` are labels, not a path: with the WAN dead the
lamp is unswitchable, and the entity state that came back at 06:15:58 was restored from cache - the worst kind
of blind, because nothing looked broken.

Watchdog additions from this (`scripts/tavern-motion/motion-tavern-watch.sh`):

1. **Egress probe** - `https://example.com` (needs DNS) and `http://1.1.1.1` (raw IP) are checked every run;
   `HOUSE INTERNET DOWN` / `HOUSE DNS BROKEN` / `HOUSE INTERNET BACK` is printed once per transition, so a
   WAN outage is named as the cause instead of an endless stream of relay alerts. Verified live: printed once,
   the second run stayed quiet.
2. **Telemetry staleness** - if `sensor.…_rssi` has not changed for >20 min, the relay is unreachable even
   when the switch entity still reads `off`/`on`: one `RELAY SILENT` line on entering that state, one
   `RELAY TALKING AGAIN` on leaving it. `unavailable` alone is not a reliable reachability signal.
3. The reload message no longer suggests DIY Mode for this relay (BASICR4 has no local API - measured twice).

The new alerts proved themselves during the same outage: at 06:46 `RELAY SILENT` reported 1801 s without
telemetry while the switch entity still read `off` (cached), and the egress line stayed suppressed after its
first print instead of repeating. One more behaviour added from the same event: when egress returns, the
watchdog pushes whatever `~/sah-main` has pending (`ahead > 0`) with `ALLOW_HARD_V6_PUSH=1` and prints
`REPO PUSHED` or `REPO PUSH FAILED` once - commits must not sit unpushed because nobody noticed the internet
was gone. The push branch was exercised while offline: it printed the `PUSH FAILED` line with the DNS error
verbatim and the watchdog itself stayed silent because its own egress probe said `wan`.
