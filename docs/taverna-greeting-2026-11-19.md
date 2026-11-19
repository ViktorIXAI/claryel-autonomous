# Taverna greeting audio chain — 2026-11-19

Operator request: when the taverna light comes on (primarily from the motion camera, but from
any source), an Italian voice should say that the guests were caught by a hidden camera, with
quiet calm music afterwards. Later refinements: Russian "Добро пожаловать!" before the Italian
phrase, internet radio instead of synthesised music, low bitrate, and the music level brought
down twice (final `-30` dB relative to full scale, ~1/6 of the original level).

## Audio content

Synthesised music was rejected by the operator ("херовая музыка"), so the bed is now the Radio
Paradise *mellow* stream at **32 kbit/s** (`audio/aac`), chosen after probing endpoints from
this host: Radio Paradise `mellow-32` answered, the SomaFM `-64.mp3` paths returned 404.

The announcement is built with `espeak-ng` inside a throwaway container:

```sh
docker run --rm -v ~/.hermes/media:/work python:3.12-slim sh -c \
  'apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq espeak-ng >/dev/null 2>&1
   espeak-ng -v ru -s 150 -p 45 -w /work/voice_ru.wav "Добро пожаловать!"
   espeak-ng -v it -s 145 -p 30 -w /work/voice_it.wav \
     "Benvenuti! Siete stati ripresi da una telecamera nascosta. Siete stati scoperti."'
```

Then both clips are resampled to 48 kHz stereo with `ffmpeg` and concatenated with a 0.35 s gap,
scaled so the peak sits at 0.53 full scale (the board's mixer is at 80 %, -12.75 dB, and the
speaker's own amplifier is at maximum — the operator sets the final loudness on the speaker).
Result: `~/.hermes/media/greeting_voice.wav`, 8.0 s (1.2 s Russian + 6.4 s Italian).

## Chain and decisions

* Trigger is the **lamp state**, not the camera event, because the greeting must also work when
  the light is switched on manually or by the eWeLink app.
* HA (host networking) calls the loopback listener; the host user is not in the `audio` group,
  so playback happens in the `taverna-audio` container with `--device /dev/snd`.
* Rate limits: one greeting per 300 s, radio capped at 1800 s, and radio always ends when the
  lamp goes off.
* Orphaned audio containers are swept when the listener starts and when it stops a stream — a
  restarted listener had left one ffmpeg playing, which is what the operator noticed as music
  that would not stop.

## Measurements (2026-11-19, real run)

| Thing | Measured |
|---|---|
| Automation fired after lamp ON | 7 s (`last_triggered` 13:42:44 UTC for a 13:42:37 change) |
| Radio player CPU | 0.6-3.0 % of one core, 19 MiB RSS |
| Radio bandwidth | 74.3 kB -> 151 kB in 15 s = 5.1 kB/s = ~41 kbit/s |
| Music stop after lamp OFF | 0 audio containers running 8 s later |
| Level ladder the operator chose | `-14` too loud, `-24` half, `-30` kept |

## Speaker and microphone facts found on the way

* The green jack on the board is **Line Out** (codec pin node 0x14, `Color = Green`); **blue is
  Line In** (node 0x15), so a speaker plugged into blue can never make sound. Jack sensors
  confirm presence: `Line Out Jack = on`, `Rear/Front Mic Jack = off`.
* A 880 Hz tone out of Line Out was captured by the webcam microphone at **-62.5 dBFS with
  clipping** while the USB "JieLi" adapter microphone only heard **-83.2 dBFS** — the speaker is
  loud and clear, the cheap USB microphone is the weak part (speech next to it reaches
  -15 dBFS, so it is usable for close-range voice, not for room listening).
