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
  template binary_sensor.taverna_motion  (delay_on 4 s, delay_off 5 min)
                        v
  automation -> switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1   (SONOFF BasicR4, TAVERNA-BASICR4)
```

Nothing in Home Assistant was reinstalled, re-paired or reset; the existing SONOFF entity is
reused. No Motion add-on, no camera/stream entity, no third-party integration was added.

## Files on the host

| Path | Purpose |
|---|---|
| `~/.config/motion/motion-tavern.conf` | detection-only Motion config (640x480 @ 2 fps) |
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
  **2 fps** by `minimum_frame_time 0.5` -> 0.5 s latency budget, ~1.2 MB/s USB traffic.
* In a dark room the sensor is effectively blind: measured luma YAVG ~1-3 out of 255 even at
  79 % analogue gain. See "Darkness limitation" below.
* The device is opened exclusively by Motion; a second consumer gets `Device or resource busy`
  (that is also why ad-hoc `ffmpeg` grabs fail while the service runs).

## Light policy (Home Assistant side)

* `input_boolean.tavern_motion_now` - raw "Motion sees something right now" carrier.
* `binary_sensor.taverna_motion` (template, `device_class: motion`) - `delay_on: 4 s`,
  `delay_off: 5 min`: the light only reacts to motion that persisted 4 s, and switches off
  5 minutes after the **last** motion; any new motion restarts the 5 minutes.
* Two automations: sensor on -> `switch.turn_on`, sensor off -> `switch.turn_off`.
* A new event re-arms the boolean and cancels nothing that could leave the light latched.
* `on_camera_lost` and the hook's `failure` path clear the boolean: a dead camera cannot keep
  the light on.

## Anti-false-trigger measures (why the light does not blink by itself)

| Source of a false trigger | Countermeasure |
|---|---|
| Auto-exposure settling after Motion (re)starts | `ExecStartPre` writes `start-ts`; the hook drops every event in the first 30 s after the service starts |
| The SONOFF switching the lamp on/off (brightness jump in the picture) | Motion `lightswitch_percent 30` + `lightswitch_frames 3` ignore a global brightness change |
| Short noise blips | `minimum_motion_frames 3` (1.5 s at 2 fps) plus `delay_on: 4 s` on the HA sensor |
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
