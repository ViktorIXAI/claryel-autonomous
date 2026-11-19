"""Does the microphone hear the speaker right now? Records both microphones at the same time while
an 880 Hz tone plays out of the speaker, then measures the narrow band level in front of and during
the tone with ffmpeg, so the numbers are ones ffmpeg itself reports.

Card 2 = JieLi USB adapter (the cheap mic, stereo). Card 1 = webcam microphone (mono only: asking
it for 2 channels fails with "Channels count non available").
"""
import os
import re
import subprocess

OUT = os.path.expanduser("~/.hermes/cache/scratch/micnow")
os.makedirs(OUT, exist_ok=True)
TONE_S, TONE_AT, REC_S = 4.0, 4.0, 12

cmd = ["docker", "run", "--rm", "--device", "/dev/snd", "-v", OUT + ":/out", "taverna-audio:latest",
       "sh", "-c",
       "ffmpeg -y -loglevel error -f lavfi -i 'sine=frequency=880:duration=%s' -ar 48000 -ac 2 /tmp/t.wav; "
       "amixer -c 0 set Master 100%% unmute >/dev/null; "
       "arecord -q -r 48000 -c 2 -f S16_LE -d %d -D hw:2,0 /out/rec2.wav & "
       "arecord -q -r 48000 -c 1 -f S16_LE -d %d -D hw:1,0 /out/rec1.wav & "
       "sleep 1; ( sleep %s; aplay -q -D hw:0,0 /tmp/t.wav; echo APLAY_DONE=$? ) & wait"
       % (TONE_S, REC_S, REC_S, TONE_AT)]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
print("container rc=%s %s" % (r.returncode, (r.stdout + r.stderr).strip()[-200:]))


def band_max(path, start, end):
    """max_volume in dB reported by ffmpeg for an 860-900 Hz slice of the recording."""
    out = subprocess.run(["ffmpeg", "-hide_banner", "-ss", str(start), "-t", str(end - start),
                          "-i", path, "-af", "highpass=f=860,lowpass=f=900,volumedetect",
                          "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.search(r"max_volume:\s*(-?[\d.]+) dB", out)
    return m.group(1) + " dB" if m else "n/a"


for path, label in ((os.path.join(OUT, "rec2.wav"), "USB mic (JieLi, card 2)"),
                    (os.path.join(OUT, "rec1.wav"), "webcam mic (card 1)")):
    if not os.path.exists(path):
        print("%-26s no recording" % label)
        continue
    before = band_max(path, 0.5, TONE_AT - 0.5)
    during = band_max(path, TONE_AT + 0.5, TONE_AT + TONE_S - 0.5)
    after = band_max(path, TONE_AT + TONE_S + 0.5, REC_S - 0.5)
    print("%-26s 880 Hz band: before tone %-10s during %-10s after %-10s" % (label, before, during, after))
print("\ntone played %s-%s s out of hw:0,0 at Master 100%%; recording %s s"
      % (TONE_AT, TONE_AT + TONE_S, REC_S))
