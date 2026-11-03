# P3032 (HP Z220 + Tesla P100): raw-model ladder and PSU reality

Date: 2026-11-03. Status: CLOSED by maintainer decision — the box's
400 W PSU / single 6-pin 12 V line cannot carry this card; further
torture cancelled, machine powered down. Contour stopped at 13/178
records (resume state kept in case the rig ever gets a proper PSU).
Board is not the long-term home of this card (see
results/p3032-p100-bringup-thermal.md).

## Raw model, no harness (context ladder, PL=150 W, clock cap ~1000-1100,
BIOS fans max, prefill chunks 2048)

| prompt tok | prefill cold tok/s | TTFT cold | decode cold tok/s | decode warm tok/s | draft accept |
|---|---|---|---|---|---|
| 1000 | 77.2 | 13.0 s | 30.4 | 30.9 | ~50% |
| 3976 | 207.5 | 19.2 s | 33.8 | 30.8 | ~50% |
| 8231 | 210.1 | 39.2 s | 29.6 | 32.2 | ~50% |
| 16968 | 210.5 | 80.6 s | 32.4 | 30.5 | ~50% |
| 31818 | 230.0 | 138.3 s | 34.6 | 34.0 | ~50% |

Same-box RTX 3060 reference (ladder pass3, uncapped): prefill
75.7/182.4/186.1/187.4/202.8, decode cold 37.1-41.5, warm 39.3-43.5.
P100 verdict: +13% long-context prefill, -15..20% decode, VRAM expert
cache 8.66 GiB resident with 99.1-99.8% hit (PCIe mostly quiet).

Thermals with BIOS fan max are a non-issue: ladder window peak 52 C, no
throttling (contrast with the header-fed blower tests: 82 C + 3x clock
throttle — see thermal report).

## Power supply reality (the actual blocker)

Two hard power-loss events at wall while the GPU stayed <=150 W PL
(nvidia-smi instantaneous samples up to 180 W during prefill ramps):

1. 16:43 CET — first ladder rung 1, GPU 38 C / 36 W at death; thermal
   log ends in null padding, journal has no shutdown records, machine
   answered only Wake-on-LAN (so it had lost power, not hung).
2. ~17:15 CET — during contour (13 records written), same signature.
   PSU latched this time: WOL x8 did not revive it; requires physical
   power-cycle by maintainer.

Diagnosis: 400 W PSU + 6-pin feed cannot absorb P100 + E3-1270v2 +
three fans-at-max transients. This matches the maintainer's original
constraint; the cap alone does not help because the trip is on transient
current, not average draw. Countermeasures applied for the retry:
`nvidia-smi -lgc 255,900` (clock floor/ceiling), prefill chunks 2048,
PL 150 W. If the 900 MHz profile still trips, verdict for this box:
full contour is not runnable on the present PSU — recorded as such.

## Contour (harness v2.4 / contour 2.2, telemetry method 2.3)

Started 17:08 CET, 13/178 records before event 2, resume state kept;
continues after power-cycle at 900 MHz profile. Telemetry file on box:
`telem-p3032p100.jsonl` (collector2). Ladder raw artifacts (log, sampler
CSV, thermal session CSV) attach here once the box is back online.

## Final incident log (CET)

- 16:43 trip #1 (ladder rung 1) — revived by WOL in 2.5 min.
- 17:15 trip #2 (contour, 13 records in) — PSU latched, WOL ineffective.
- 17:3x-17:5x boot-loop: PSU self-recovery + BIOS "power on after AC
  restore" + watchdog engine start at boost = repeated trips every few
  minutes; WOL watchers stopped at 17:5x to end the cycle.
- 17:52 caught boot, keep-up disabled, PL 150 W + clock cap 900 applied,
  engine killed, clean shutdown confirmed.

Maintainer verdict (verbatim intent): insufficient 12 V rail power; the
card is set aside on this platform. Published data from this session:
raw ladder (full), thermal envelope at BIOS fan max, and the PSU trip
signature — all reproducible with the attached method.
