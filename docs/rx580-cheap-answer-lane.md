# The cheap-answer lane: small models, low power cap, short replies

What the power-cap study (`docs/rx580-power-cap-study.md`) is actually for: running small models on
the RX 580 for **short answers at the lowest energy cost**. Tariff 0.25 €/kWh, a "short answer" =
200 generated tokens, card watts measured through the run (not TDP).

## Cost of one short answer

| Model | card cap | card W during run | decode | Wh per 200-token answer | 1000 answers/day | per year at 1000/day |
|---|---|---|---|---|---|---|
| **Qwen2.5-3B Q4_K_M** | **70 W** | 64.8 | 39.5 t/s | **0.091 Wh** (0.0023 €-cent) | 91 Wh/day = 0.023 € | **8.3 €** |
| Qwen2.5-3B Q4_K_M | 120 W | 101.0 | 44.8 t/s | 0.125 Wh | 125 Wh/day = 0.031 € | 11.4 € |
| Nemotron-3-Nano-4B | 70 W | 67.8 | 26.8 t/s | 0.141 Wh | 141 Wh/day = 0.035 € | 12.9 € |
| Nemotron-3.5-Bolt-E4B | 70 W | 65.5 | 20.6 t/s | 0.176 Wh | 176 Wh/day = 0.044 € | 16.1 € |
| our IQ3_S (77 GiB MoE) | 50 W | 49.6 | 6.6 t/s | 0.418 Wh | 418 Wh/day = 0.105 € | 38.2 € |

Lowering the cap from 120 W to 70 W cuts a short answer by **27 %** (0.125 → 0.091 Wh) and costs only
12 % of speed, which at 39 t/s is 5.1 s versus 4.5 s for a 200-token reply — invisible next to model
load and prompt time.

## The line that decides the real budget: idle, not the cap

The card burns **14 W with the model loaded and nothing running** — 336 Wh/day, **0.084 €/day,
30.7 €/year** if the box sits powered 24/7. That is more than three times the cost of a thousand
short answers per day. The crossover is **~3700 short answers per day**: below that traffic level, the
idle draw dominates everything the cap tuning can save.

So at realistic household volumes the ordering of levers is:

1. **Do not leave the lane powered when it is not in use** (worth ~30 €/year — more than every cap
   setting combined).
2. **Cap 70 W for the generation lane** (~3 €/year saved at 1000 answers/day, free at any volume, and
   it also drops fan noise and heat).
3. **Keep answers short** — a 200-token reply at 70 W costs 2.7 Wh/day for 30 answers/day
   (**0.25 €/year**); quadrupling the reply length quadruples the cost, and the cap tuning saves
   nothing proportionally.
4. **Cap 30 W only when the constraint is watts, not money** (UPS, off-grid, a shared circuit): the
   whole card draws 36 W and 3B still gives 19.5 t/s, but cost per token is 13 % worse than at 70 W.

## Recipe for the lane

`power1_cap = 70 W` (`power1_cap_default` restore is one write back), `power_dpm_force_performance_level`
left at `auto` (pinning it to `high` costs a resident 3B ~25 % of decode), model in the 2–5 GiB range
(3B Q4 / Nano-4B Q4) so it is fully VRAM-resident, `-fa off`, generation capped to ~300 tokens. With
that, a short answer costs **0.09 Wh** and a whole day of a hundred of them costs a quarter of a
euro-cent — the lane is effectively free; the box's idle draw is the only real line on the bill.
