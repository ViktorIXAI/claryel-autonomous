# Taverna greeting (voice + background radio on light ON)

When the taverna lamp turns on — from the motion camera, from the app, or from the physical
relay — the server speaks an announcement over the analog Line Out and then plays quiet
internet radio until the lamp goes off.

## Chain

```
lamp ON (any source)
  -> HA automation taverna_greeting_voice        (trigger: state -> on)
     -> rest_command.taverna_greeting  = POST http://127.0.0.1:8124/greet/<secret>
        -> taverna-greeting-listen.py on the host plays:
             1. greeting_voice.wav  "Добро пожаловать!" + Italian phrase (8.0 s)
             2. radio stream https://stream.radioparadise.com/mellow-32 (32 kbit/s AAC)
lamp OFF
  -> HA automation taverna_greeting_music_off -> POST /stop/<secret> -> radio ends
```

Home Assistant runs with host networking, so `127.0.0.1:8124` from inside the container is the
host. The listener binds loopback only and requires the secret in the path.

The host user is not in the `audio` group, so audio is played inside the `taverna-audio`
container (`Dockerfile.audio`: alsa-utils + ffmpeg) with `--device /dev/snd`.

## Files on the host

| Path | Purpose |
|---|---|
| `~/.hermes/scripts/taverna-greeting-listen.py` | the loopback player/trigger |
| `~/.hermes/scripts/taverna-greeting-ensure.sh` | watchdog: silent if `/ping` succeeds; otherwise attempts restart and prints `RESTARTED` or `DOWN` |
| `~/.hermes/scripts/taverna-greeting-e2e-test.py` | end-to-end test (toggles the lamp) |
| `~/.hermes/media/greeting_voice.wav` | the announcement clip (48 kHz stereo, peak 0.53 FS) |
| `~/.hermes/media/radio.url` | station URL, one line |
| `~/.hermes/media/radio_gain` | radio level in dB, one line (currently `-30`) |
| `~/.hermes/media/greet.secret` | path secret, mode 0600 — never committed |

HA side lives in `/config/configuration.yaml`: `rest_command.taverna_greeting`,
`rest_command.taverna_greeting_stop` and the two automations. Backup of the previous file:
`configuration.yaml.bak-greet-20261119`.

## Documentation clarification — 2026-11-19 (issue #25)

Commit [`929b865`](https://github.com/ViktorIXAI/claryel-autonomous/commit/929b86585b273731f9119fc6af76d3d2c96c6e73) changed the watchdog's normal output contract: a successful `/ping` now exits silently; restart and failure paths emit status. The original README wording above was updated to match that implementation. This is a documentation-only reconciliation, **not** an independent live-host or CI verification. The original wording remains recoverable in Git history.

## Adjusting

* Volume of the music: `echo -34 > ~/.hermes/media/radio_gain` then
  `~/.hermes/scripts/taverna-greeting-ensure.sh` after restarting the listener. Measured ladder:
  `-14` was too loud, `-24` was "half", `-30` is the level the operator kept.
* Speaker-side volume is a physical knob; the software mixer on the board is set to 80 %
  (`amixer -c 0 set Master 80%`, i.e. -12.75 dB).
* Station: overwrite `radio.url`. Only low-bitrate endpoints: 32 kbit/s costs ~41 kbit/s on the
  wire, which is what the operator asked for.
* Cooldown (one greeting per N seconds) and the radio cap: `GREET_COOLDOWN` (300) and
  `GREET_MAX_RADIO_S` (1800).
* Announcement text: rebuild with `espeak-ng -v ru` and `-v it` and concatenate — see
  `docs/taverna-greeting-2026-11-19.md`.

## Measured while streaming

* ffmpeg in the player container: CPU 0.6-3.0 %, memory 19 MiB.
* Container network: 74.3 kB -> 151 kB in 15 s = ~5.1 kB/s = **~41 kbit/s**.
* Lamp OFF at 14:43:17 -> audio containers running afterwards: **0**.
* Greeting automation fired 7 s after the lamp state change (`last_triggered` in HA).

## Watch out

* Restarting the listener orphans the audio container it started; the listener now sweeps
  `taverna-audio` containers on start and on stop, so a stale stream cannot keep playing.
* HA names automation entities after the **alias**, not the `id`, so the entity ids are the
  transliterated aliases: `automation.taverna_italianskoe_privetstvie_i_muzyka_pri_vkliuchenii_sveta`,
  `automation.taverna_obryvat_muzyku_kogda_svet_pogas`.
* Never write a literal `Authorization: Bearer <token>` header into a script file here; the
  tooling redacts that pattern to `***` before it reaches disk, and HA then answers 401. Build
  the string at runtime instead.
