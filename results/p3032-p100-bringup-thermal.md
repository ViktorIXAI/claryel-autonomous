# P3032 with Tesla P100 after GPU-mode switch: bring-up + first thermal envelope

Date: 2026-11-03. Box: P3032 (HP Z220), card: Tesla P100 PCIe 16 GB in
graphics mode (see `results/p100-gpumode-256mb-bar1.md`).

## Bring-up (verified)

* After the firmware mode switch, the stock Z220 BIOS allocated BAR1
  unaided: PCI class `VGA compatible controller`, BAR1 256 MiB at
  `0xc0000000` — inside the sub-4G window. No kernel workarounds needed.
* Driver 580.178.04 probed clean; the earlier NVRM "BAR1 is 0M" error is
  gone and no blacklist remains.
* Standing power policy applied immediately: `-pm 1`, `-pl 150` (weak PSU /
  6-pin cable on record), plus `@reboot` cron line to reapply.
* Steady state idle: 25-34 °C, 26-30 W, ECC enabled, 16384 MiB visible.

## Thermal governor (installed)

`p100-fan-thermal.service` (systemd, always-on):
* reads GPU temp every 15 s, logs CSV (`p100-thermal.csv`);
* fan on P9 header via ACPI `_TZ.FN00._ON/_OFF` (DSDT has only on/off fan
  methods; no PWM/RPM interface exists for this header);
* hysteresis: ON >= 55 °C, OFF <= 40 °C; no-driver fail-safe = fan ON;
* CRIT >= 85 °C: fan forced ON and inference engine killed, event logged.

## Synthetic load test (thermal envelope, 2026-11-03)

Kernel: fp32 matmul 3072^3 in a loop (`nvcc -arch=sm_60`), 90 s and 150 s
passes, power limit 200 W during test then restored to 150 W.

| phase | draw | temp trajectory |
|---|---|---|
| idle before | 26 W | 38-39 °C flat |
| 90 s load, PL 200 | ~100 W | reached 58 °C, governor flipped fan ON at 55 °C |
| 150 s load, PL 150 | 100-113 W | 55 -> 79 °C, still climbing at load end; **SW Thermal Slowdown active**, HW slowdown not triggered |

Verdict: card is fully functional in this box, but the P9-header blower is
the weak link under synthetic worst-case load (~110 W). Real inference on
this model class drew ~53 W on the sister box (P1005 CHG-002), which is a
much easier point for this cooling; the CRIT guard + hysteresis cover the
gap. Open hardware question: whether P9 supplies full 12 V (fan reported as
"barely spinning" by maintainer while idle) — if yes, a ducted 12 V blower
or a P100 with active cooler removes the ceiling entirely.

## Engine build for sm_60 (attempt log)

`strata 0.1.55` avx-floor rebuild targeting sm_60:
* first configure FAILED with the upstream message: `Strata needs an NVIDIA
  GPU of compute capability 7.5 or newer ... A Pascal sm_60 or Volta sm_70
  build is -DSTRATA_EXPERIMENTAL_SM60=ON` (published as finding);
* reconfigured with `-DSTRATA_EXPERIMENTAL_SM60=ON` + `sm_60` +
  `STRATA_ISA_FLOOR=avx` + CUDA 12.6 nvcc; build in progress at publish
  time; results/verdict appended to this file in a follow-up commit.

Artifacts: thermal CSV (80 samples, max 79 °C), sha256/16
`d1af44f78bda17cb`, kept on the workstation and mirrored to the log pin.

Data in this record is safe to publish (no secrets, addresses, local paths).
