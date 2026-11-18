# Tavern light driven by a local motion detector (Motion + Home Assistant)

Date: 2026-11-18. Host: `claryel01` (station `claryel-it-home-001`).

## What was built

A USB webcam on `claryel01` is analysed by **Motion 4.6.0-1ubuntu2** running as its own
systemd service `motion-tavern.service`. Motion performs **frame-difference detection only**
and calls a small shell hook that posts to Home Assistant over the loopback REST API. Home
Assistant owns the light policy and switches the existing SONOFF BasicR4 switch.

```
USB cam -> motion-tavern.service (detection, no recording, no stream)
              |  on_event_start / on_event_end / on_camera_lost
              v
  ~/.local/libexec/tavern-motion-hook.sh  --loopback-->  HA REST API
              input_boolean.tavern_motion_now  (carrier)
                        v
  template binary_sensor.taverna_motion  (delay_on 1 s, delay_off 5 min)
  hook also commands the relay directly at on_event_start (fast path, see 'Response latency')
                        v
  automation -> switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1   (SONOFF BasicR4, TAVERNA-BASICR4)
```

Nothing in Home Assistant was reinstalled, re-paired or reset; the existing SONOFF entity is
reused. No Motion add-on, no camera/stream entity, no third-party integration was added.

## Files on the host

| Path | Purpose |
|---|---|
| `~/.config/motion/motion-tavern.conf` | detection-only Motion config (640x480 @ 2 fps, single-frame trigger) |
| `~/.config/motion/hass-token` | HA long-lived token, mode `0600`, never printed |
| `~/.local/libexec/tavern-motion-hook.sh` | `start` / `frame` / `end` / `failure` bridge into HA |
| `/etc/systemd/system/motion-tavern.service` | own unit, own cgroup, `Restart=always`, nice/cgroup caps |
| `~/.hermes/setup/install-motion-tavern-root.sh` | idempotent installer (root) |
| `~/.hermes/scripts/motion-tavern-watch.sh` | watchdog, silent while healthy |
| `/tmp/motion-tavern/start-ts` | boot-guard timestamp, recreated by `ExecStartPre` |

The distro's stock `motion.service` is stopped and **masked**: the tavern unit is the only
camera consumer, and a plain `apt install motion` can never steal the device again.

## Privacy / footprint guarantees (verified, not assumed)

* `picture_output off`, `movie_output off` -> no photos, no video files.
* `stream_port 0`, `webcontrol_port 0` -> no stream, no control port.
  Verified by diffing `ss -ltnp` before and while the real 4.6 binary ran with this config:
  **zero new listening sockets**.
* Option names were checked against the shipped 4.6 binary (`strings`) and the 4.6.0 source,
  because 4.6 renamed `output_pictures` -> `picture_output` and
  `ffmpeg_output_movies` -> `movie_output`; a silently ignored key would have broken the
  "no recordings" guarantee.
* `thread_limit 1`, `log_level 5`, no network exposure, hook posts to `127.0.0.1` only.

## Camera reality (measured)

* Device `32e6:9251 "USB Camera"`, `/dev/video0`, driver `uvcvideo`.
* The driver does **not** expose 320x240; the smallest mode is **640x480**
  (MPEG-JPEG up to 30 fps, YUYV up to 30 fps). Motion picks YUYV 640x480 and is throttled to
  **2 fps** with `minimum_frame_time 0` (the device offers 2/5/10/15/20/30; the old cap was
  `minimum_frame_time 0.5`). 2 fps + one-frame trigger gives the same 0.5 s reaction as 5 fps +
  two-frame trigger, at half the CPU and with a wider lamp-step suppression window (1.5 s vs 0.6 s).
* In a dark room the sensor is effectively blind: measured luma YAVG ~1-3 out of 255 even at
  79 % analogue gain. See "Darkness limitation" below.
* The device is opened exclusively by Motion; a second consumer gets `Device or resource busy`
  (that is also why ad-hoc `ffmpeg` grabs fail while the service runs).

## Light policy (Home Assistant side)

* `input_boolean.tavern_motion_now` - raw "Motion sees something right now" carrier.
* `binary_sensor.taverna_motion` (template, `device_class: motion`) - `delay_on: 1 s`,
  `delay_off: 5 min`: the sensor is the OFF authority and the backup ON path (the hook commands
  the relay directly at event start), and the light switches off
  5 minutes after the **last** motion; any new motion restarts the 5 minutes.
* Three automations: sensor on -> `switch.turn_on`, sensor off -> `switch.turn_off`, and
  `tavern_lamp_on_without_motion` -> any light that has been on for 10 minutes while the motion
  sensor is off gets switched off (see the incident section; `input_boolean.tavern_light_manual`
  disables that safety net when the room genuinely needs light without motion).
* A new event re-arms the boolean and cancels nothing that could leave the light latched.
* `on_camera_lost` and the hook's `failure` path clear the boolean: a dead camera cannot keep
  the light on.
* The latch itself is heartbeated by the hook (`input_boolean.toggle` per accepted frame) and
  cleared by `tavern_motion_latch_guard` after 15 minutes without a refresh.

## Anti-false-trigger measures (why the light does not blink by itself)

| Source of a false trigger | Countermeasure |
|---|---|
| Auto-exposure settling after Motion (re)starts | `ExecStartPre` writes `start-ts`; the hook drops every event in the first 30 s after the service starts |
| The SONOFF switching the lamp on/off (brightness jump in the picture) | Motion `lightswitch_percent 30` + `lightswitch_frames 3` ignore a global brightness change |
| Short noise blips | `threshold 2000`, `noise_level 20`, `despeckle_filter EedDl`, `delay_on: 1 s` on the HA sensor (the event itself opens from a single frame at 2 fps) |
| Sensor noise in near-dark frames (this specific camera is very noisy at high gain) | `noise_level 20`, `threshold 2000`, `despeckle_filter EedDl` |
| Service restart storm | `Restart=always` with a 5 s period + the 30 s boot guard + watchdog alert |

First tuning (`threshold 1500`, `noise_level 8`, `minimum_motion_frames 2`) produced **8 false
events in the dark within one minute** - the light switched on by itself. After the tuning
above the same dark room produced no events.

## Measured behaviour

| Measurement | Result |
|---|---|
| Light on after a motion event | ~3 s |
| Light off after the last motion | 300 s (boolean off 02:23:08 -> switch off 02:28:08) |
| Sensor hold expiry, camera-driven event | carrier off 02:52:20 -> sensor off 02:57:21 (301 s) |
| New motion during the hold | timer restarted, light stays on (verified through the boolean path) |
| 5 minutes of dark room after tuning | **0 false events** (before tuning the same room gave 8 in ~1 min) |
| Light switching off (global brightness jump) | no motion event -> `lightswitch_percent 30` guard works |
| CPU while idle (dark, no events) | **0.38 %** of one core |
| CPU while processing events | ~2 % of one core |
| Process RSS | **56.3 MB**; unit cgroup `MemoryCurrent` 20.3 MB, `TasksCurrent` 2 |
| `NRestarts` | 0 (before the drill) |
| Listeners opened by Motion | none (`ss -ltnHp` shows no socket owned by the live service) |
| Files written by the service | only `start-ts` (11 bytes) in the unit's private `/tmp` - no images/video |
| Crash drill (SIGTERM the daemon) | systemd restarted it in ~7 s (`NRestarts=1`), `ExecStartPre` refreshed the guard timestamp, camera re-opened (YUYV 640x480), HA stayed quiet through the 30 s guard and 40 s after |
| Manual light on / off (real pixels, both directions) | no motion event -> no light bounce-back |
| Boot persistence | unit `enabled`, `WantedBy=multi-user.target` |
| Caps actually applied by systemd | `MemoryHigh=300 MiB`, `MemoryMax=400 MiB`, `CPUWeight=20`, `Nice=10`, `RestartSec=5` |

## Response latency (retuned 2026-11-18: ~6 s -> ~0.9 s)

The owner reported the lamp coming on ~5 s after a person appeared. The camera was not the slow
part - four filters were stacked in series:

| stage | before | now |
|---|---|---|
| Motion needs N consecutive motion frames | 3 frames @ 2 fps = **1.5 s** | 1 frame @ 2 fps = **0.5 s** |
| hook -> Home Assistant REST | ~0.1 s | ~0.1 s |
| template sensor `delay_on` | **4 s** | **1 s** |
| ON automation -> Zigbee relay | ~0.3-0.5 s | skipped (hook commands the relay at `on_event_start`) |
| measured hook -> relay state `on` | - | **0.39-0.46 s** |
| **person -> light** | **~6 s** | **~0.9-1.0 s** |

What changed: `minimum_motion_frames 3 -> 1`, `minimum_frame_time 0.5 -> 0`, template
`delay_on: 4 s -> 1 s`, and the hook now calls `switch.turn_on` for the existing SONOFF entity at
event start. `automation.tavern_motion_light_on` stays as a backup path, and Home Assistant still
owns the OFF side (`delay_off: 5 min` -> `tavern_motion_light_off`).

Two frame-rate variants were measured against the same anti-noise settings
(`threshold 2000`, `noise_level 20`, `despeckle_filter EedDl`):

| variant | detection budget | Motion CPU (idle room) | lamp-step window |
|---|---|---|---|
| 5 fps + `minimum_motion_frames 2` | 0.4 s | 0.93 % of one core | 0.6 s |
| **2 fps + `minimum_motion_frames 1`** (live) | 0.5 s | **0.53 % of one core** | 1.5 s |

Both end at ~1 s person-to-light, because 0.39-0.46 s of it is the SONOFF relay plus REST, which no
frame rate can remove. 2 fps was kept: same speed, half the CPU, and `lightswitch_frames 3` then
covers 1.5 s of the relay's own brightness jump instead of 0.6 s. The single-frame trigger is the
open question, so it is being watched for an hour with five-minute reports
(`scripts/tavern-motion/motion-fps-monitor.sh`, cron `8bb76bb16562`, 12 samples); if false events
appear, the fallback is `minimum_motion_frames 2` at 2 fps (1.0 s) or 5 fps + 2 frames.

Cost and regression gates, measured on the host (`scripts/tavern-motion/speedup-test.sh`):

* CPU **0.38 % -> 0.93 %** of one core (24 cores) at 5 fps, **0.53 %** at 2 fps; RSS 54 MB, 2 threads;
* 2 min idle in the dark at 5 fps: **0** false events (re-running at 2 fps + single frame);
* lamp switched on/off inside the watch window (global brightness step): **0** false events -
  `lightswitch_percent 30` / `lightswitch_frames 3` still suppress the relay's own step at 5 fps;
* OFF leg re-verified after the change: the light went off **301 s** after the motion latch cleared.

Headroom, deliberately not used: the webcam offers up to 30 fps, so `framerate 10` with 2 frames
would bring detection down to 0.2 s for ~1.9 % CPU. It doubles the chance that one noise burst
opens an event, and the remaining ~0.4 s is Zigbee relay time, which no frame rate can remove.

### Latch guard (a lamp that would never go out)

The direct relay command has one consequence: the OFF automation is armed by the **sensor**, and the
sensor only turns on if the latch (`input_boolean.tavern_motion_now`) stays up for more than
`delay_on`. Real events always hold the latch for at least `event_gap` = 15 s, so the OFF path is
normally armed. If Motion's `on_event_end` never arrives (daemon restarted mid-event, HA restarting
at that moment) the latch stays up and the lamp would burn indefinitely.

Fix, entirely inside HA and the hook:

* the hook's `frame` handler **toggles** the latch (`turn_off` then `turn_on`) while motion continues;
  a plain `turn_on` over an already-on `input_boolean` changes nothing at all in Home Assistant -
  `state`, `last_changed` and `last_updated` all stay put (verified against the REST API on
  2026-11-18), so a no-op refresh cannot serve as a heartbeat;
* `automation.taverna_flazhok_dvizheniia_gorit_slishkom_dolgo_sniat` (`id: tavern_motion_latch_guard`)
  fires when the latch has been `on` **for 15 minutes** without a refresh and clears it, which
  re-arms the 5-minute sensor delay: worst case ~20 min of light instead of forever;
* `motion-tavern-watch.sh` only reports (`MOTION LATCH STUCK`) when the latch is still up 25 minutes
  after its last change - i.e. when the HA guard itself failed. It never writes to HA and never
  touches a light turned on manually.

Verified end to end on 2026-11-18 (`scripts/tavern-motion/latch-guard-verify.sh`): a synthetic event
was opened and its `end` deliberately never sent while `frame` toggles kept the latch alive -
**0 sensor blips** across the toggles; the last refresh was 05:24:58, the guard fired at **05:39:58**
(15 min), the sensor went off at **05:47:41** and the lamp at **05:47:42**. Before this guard the
same scenario left the lamp on indefinitely.

## Incident 2026-11-18: the lamp burned for 7 h 18 min in an empty room

Viktor found the basement/tavern lamp hot around 13:00 and it stayed on until he walked around
the room. Read from the Home Assistant recorder (`lamp-history.py`, `lamp-times.py`,
`lamp-window.py`, `relay-detail.py` in `scripts/tavern-motion/`) and the systemd journal - all
times local:

| time | what happened | evidence |
|---|---|---|
| 02:08 | the relay entity appears in HA for the first time | first recorded state of `switch.taverna_...` |
| 05:47:42 | last OFF produced by the motion chain | latch-guard drill |
| **06:01:38** | **relay goes ON** | state row `on`, `origin_idx=0` (device push), `context_user_id` empty |
| 05:50-06:10 | camera saw nothing | journal: 0 `Motion detected - starting event` |
| 06:01-13:00 | latch and sensor never went on | latch: 05:39:58 then 13:00:25; sensor: 05:47:41 then 13:00:26 |
| 11:35:56, 11:36:23 | relay `unavailable` (Zigbee) | 4 unavailable episodes that day: 11:35, 11:36, 13:01, 13:11 |
| 13:00:26 | Viktor enters: sensor ON, 8 camera events, latch toggling until 13:11 | journal 12:55-13:25 UTC |
| **13:20:12** | motion ends 5 min earlier -> sensor OFF -> **lamp OFF** | state row `off` at 13:20:12 |

So the lamp was on for **7 h 18 min** and the motion chain put it out within one second of the
sensor finally going off - the OFF path works, it just never had a state of its own to clean up.

Why nothing switched it off: every automation in this room only reacts to the motion chain's own
states, and the motion chain only switches off what it switched on. The ON at 06:01 came from
neither: no Motion event, no HA service call in the recorder, no user in the state context, and
`origin_idx=0` means the integration reported the device, not HA commanding it. The device's own
`power_on_behavior` is `off`, so a plain power cycle would have restored OFF, not ON. The four
Zigbee dropouts the same day say the radio link to that relay is marginal, which is the same
symptom class as a relay that reports a state nobody asked for.

What was added because of it:

* automation `tavern_lamp_on_without_motion` (`automation.taverna_svet_gorit_bez_dvizheniia_vykliuchit`):
  relay `on` for 10 minutes while `binary_sensor.taverna_motion` is off -> `switch.turn_off`.
* `input_boolean.tavern_light_manual` ("Таверна: свет вручную") - while on, the safety net stands
  down, so a deliberately switched-on light is left alone. Turn it off when leaving.
* watchdog lines: `LAMP ON WITHOUT MOTION` (still on 15+ minutes into that state, i.e. the HA
  automation failed) and `RELAY UNREACHABLE` (`unavailable` in HA).
* gate `scripts/tavern-motion/lamp-guard-drill.sh`: switches the relay on by hand while nobody
  touches the camera and waits for the safety net. Run on 2026-11-18: `turn_on` at 15:35:13,
  **lamp OFF at 15:45:13 = 610 s**, motion sensor `off` the whole time, **0** camera events during
  the drill (so the ON really was uncommanded), latch and manual override untouched. The 10 s over
  600 s is the automation's `for:` bookkeeping plus the 10 s poll.

Not fixed here (needs hands): the Zigbee path to the basement relay. Four `unavailable` episodes
in one day, including twice while Viktor was in the room, mean the relay is on the edge of the
mesh; a router device (any plugged Zigbee device) between the coordinator and the basement is the
fix. Also still present in the UI: `input_boolean.tavern_light_blind` and two `automation.taverna_*slepoe_okno*`
items from the abandoned blind-window design - all three are `unavailable` and can be deleted in
the Home Assistant UI.

## Why the frame rate is not switched on the fly

The obvious idea - idle at 2 fps, jump to 5 fps the moment something looks like motion, drop back
when it turns out to be nothing - cannot be done inside Motion without a stream restart: `framerate`
is only applied when the config is re-read, and each restart re-opens the camera, which is exactly
the auto-exposure noise the 30 s boot guard exists to swallow. It also cannot speed up the first
detection: at 2 fps the first candidate physically cannot exist before 0.5 s. Runtime changes would
mean re-enabling `webcontrol_port`, a listening socket deliberately disabled for the no-listener
guarantee, to save half a percent of one core. The same goal is reached instead by keeping 2 fps and
letting `threshold`/`noise_level`/`despeckle_filter` do the noise filtering that
`minimum_motion_frames` used to do.

Why not a heartbeat file for the watchdog: the service runs with `ProtectSystem=strict` +
`ProtectHome=read-only` + `PrivateTmp`, so the hook may write only inside its own private `/tmp` -
nothing it writes is visible to another process, and a write anywhere else would abort the hook
(`set -eu`) and take the whole chain down with it. A host-visible heartbeat would need
`ReadWritePaths=` in the unit (root edit); the HA-side guard needs nothing.

## Operations

```
systemctl status motion-tavern          # state, cgroup usage
journalctl -u motion-tavern -f          # detection events (EVT lines)
# config change:
sudo systemctl restart motion-tavern    # reloads ~/.config/motion/motion-tavern.conf
```

Watchdog cron job `1d1fd732ed3a` runs `motion-tavern-watch.sh` every 15 minutes: silent while
`active`, one alert line if the unit is down, restart-looping, or if `/dev/video0` disappeared.

## Darkness limitation (important)

A passive USB webcam cannot see a person in a pitch-black room, and this one has no IR
illumination: dark frames sit at YAVG ~1-3/255, i.e. there is no scene to compare. Practical
consequences and options:

* The detector works while there is *some* ambient light (street light through a window,
  a nightlight, the bar's standby lighting).
* For genuinely dark hours either keep a low-wattage nightlight inside the camera's field of
  view, or add a Zigbee PIR sensor for those hours (ZHA is already paired on this host) and
  keep the camera for the lit hours.
* Detection range in the dark should be re-measured after the camera is physically mounted in
  the tavern, because the webcam currently sits on the desk at `claryel01`.

## Known gaps / next steps

1. Person-in-frame acceptance test (wave in front of the camera, confirm the light path).
2. Reboot test: after a host reboot the unit must come up, the boot guard must swallow the
   initial noise and the light must follow motion.
3. Camera is still on the desk, not in the tavern - the detection area must be re-checked and
   `threshold`/`lightswitch` re-tuned for the real field of view.
4. Left-over orphan entities in HA from the removed blind-window helpers
   (`timer.tavern_blind`, `input_boolean.tavern_light_blind`) show as `unavailable` and
   disappear on the next full HA start; they are not referenced by any automation.
