# P3032 power envelope A/B — 150 W cap vs factory max (2026-11-02)

Same box, same engine (local 0.1.55 avx-floor), same serve config, same
ladder methodology as results/p3032-iq3s-context-ladder.md (pass 3 = capped
baseline, pass 4 = uncapped). Only the GPU power limit changed: 150 W
operational cap vs 187 W factory maximum (`nvidia-smi -pl`).

**MAINTAINER NOTE: the uncapped state was explicitly SHORT-TERM and is now
REVERSED. The workstation's PSU/power cable cannot sustain the card's peak
draw; 177.4 W was observed at the wall-side rail during the test. The 150 W
cap (live `nvidia-smi -pl 150` + @reboot cron) is restored and is the
standing operational state. Do not remove the cap on this box without
operator hardware changes.**

## Results

| metric (cold, tok/s) | 150 W cap | uncapped (187 W max) | delta |
|---|---|---|---|
| prefill 1k / 4k / 8k / 16k / 30k | 75.7 / 182.4 / 186.1 / 187.4 / 202.8 | 74.7 / 182.5 / 184.9 / 187.4 / 202.4 | ±1 % (noise) |
| decode band (700-tok cold runs) | 37.1–41.5 | 38.0–46.8 | mixed, +0–23 % |
| decode band (700-tok warm runs) | 39.3–43.5 | 45.3–50.8 | **+10…+24 %** |
| GPU power median / peak | 76 / 149.8 W | 77 / 177.4 W | peak +27.6 W |
| GPU temp peak | 66 °C | 69 °C | +3 °C |
| VRAM in use / RAM min free / swap | 11145 MiB / 9.0 GiB / ≤0.5 MiB | 11169 MiB / 8.8 GiB / ≤0.5 MiB | unchanged |

Short-generation runs (model chose `stop` at 60–131 tokens) are excluded
from bands as before; run-by-run rows in the committed jsonl.

## Verdict

**Prefill is completely power-cap independent (CPU/disk bound — identical to
±1 %). Only warm-cache decode gains, ~10–24 %, and it costs +28 W peak and
+3 °C on a box whose power cable is the weak point. Net decision: the gain
is not worth the electrical risk — 150 W stays the permanent cap on P3032.**

## Artifacts

- pass-3 (capped) sampler `29ca83244f5f4da2`, ladder log `ea2d5336679d0596`
- pass-4 (uncapped) sampler `865a033293003a09`, ladder log `d6c6320afd7906da`
- client-side rows: results/p3032-iq3s-power-envelope.jsonl

Safe to publish: power/temperature/rates only; no identifiers.
