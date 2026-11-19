"""Rebuild the taverna announcement clip: Russian welcome first, then the Italian line.

The previous clip put a rushed 0.8 s Russian phrase in front of a 6.4 s Italian one, and the
operator upstairs did not hear the Russian at all. This generates both phrases again, normalizes
each one separately (so the short Russian cannot be drowned by the long Italian one) and writes
the concatenated clip at a higher overall level.
"""
import array
import os
import subprocess
import sys
import wave

MEDIA = os.path.expanduser("~/.hermes/media")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(MEDIA, "greeting_voice.wav")
RU_TXT = "Добро пожаловать!"
IT_TXT = "Benvenuti! Siete stati ripresi da una telecamera nascosta. Siete stati scoperti."
RU_TO, IT_TO = 0.92, 0.78          # target peak per phrase, full scale
LEAD_S, GAP_S = 0.30, 0.55         # silence before the Russian, pause between the phrases
RATE = 48000

subprocess.run([
    "docker", "run", "--rm", "-v", MEDIA + ":/work", "python:3.12-slim", "sh", "-c",
    "apt-get update -qq >/dev/null 2>&1; apt-get install -y -qq espeak-ng >/dev/null 2>&1; "
    "espeak-ng -v ru -s 115 -p 50 -a 200 -w /work/_ru.wav %r && "
    "espeak-ng -v it -s 140 -p 35 -a 180 -w /work/_it.wav %r" % (RU_TXT, IT_TXT)], check=True)

for src, dst in (("_ru.wav", "_ru48.wav"), ("_it.wav", "_it48.wav")):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", os.path.join(MEDIA, src),
                    "-ar", str(RATE), "-ac", "2", os.path.join(MEDIA, dst)], check=True)


def load(name):
    w = wave.open(os.path.join(MEDIA, name))
    a = array.array("h")
    a.frombytes(w.readframes(w.getnframes()))
    return a


def scaled(a, target):
    peak = max(abs(v) for v in a) or 1
    k = target * 32768 / peak
    return [max(-32768, min(32767, int(round(v * k)))) for v in a]


ru, it = scaled(load("_ru48.wav"), RU_TO), scaled(load("_it48.wav"), IT_TO)
sil = lambda s: [0] * int(s * RATE) * 2
out = array.array("h", sil(LEAD_S) + ru + sil(GAP_S) + it + sil(0.35))
w = wave.open(OUT, "wb")
w.setnchannels(2)
w.setsampwidth(2)
w.setframerate(RATE)
w.writeframes(out.tobytes())
w.close()
for f in ("_ru.wav", "_it.wav", "_ru48.wav", "_it48.wav"):
    os.remove(os.path.join(MEDIA, f))
print("wrote %s: %.2f s (russian %.2f s, italian %.2f s), peak=%.2f FS"
      % (OUT, len(out) / 2 / RATE, len(ru) / 2 / RATE, len(it) / 2 / RATE,
         max(abs(v) for v in out) / 32768))
