"""Peak/RMS profile of the announcement clip, 0.2 s windows, to see whether the Russian
half is actually present and how it compares with the Italian half."""
import array
import math
import sys
import wave

path = sys.argv[1] if len(sys.argv) > 1 else "/home/viktor/.hermes/media/greeting_voice.wav"
w = wave.open(path)
rate, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
raw = array.array("h")
raw.frombytes(w.readframes(n))
if ch == 2:
    raw = raw[0::2]
dur = n / rate
print("%s: %.2f s @ %d Hz, %d ch, peak full-scale=%.3f" % (path, dur, rate, ch, max(abs(v) for v in raw) / 32768))
step = int(0.2 * rate)
for i in range(0, len(raw), step):
    win = raw[i:i + step]
    if not win:
        break
    peak = max(abs(v) for v in win) / 32768
    rms = math.sqrt(sum(v * v for v in win) / len(win)) / 32768
    bar = "#" * int(peak * 40)
    print("  %5.1f-%5.1f s  peak %6.3f  rms %6.3f  %s" % (i / rate, (i + step) / rate, peak, rms, bar))
