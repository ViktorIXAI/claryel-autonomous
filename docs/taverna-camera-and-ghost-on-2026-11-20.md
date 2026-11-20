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
