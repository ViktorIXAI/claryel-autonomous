# P3032 disk swap test — IQ3_S runs entirely from the slow SATA SSD (2026-11-02)

Deliberate hardware-bottle experiment: same box, same engine and serve
profile, same ladder shape as results/p3032-iq3s-context-ladder.md (run gs
salted separately), but the 78 GB model stack (models + native packs + mtp +
expert profile) moved to the **system SATA SSD** (SM200, 238 GB) under
`/opt/strata-slow`, the NVMe data disk (including its 64 GB swap) was
**fully unmounted** for the run, and a temporary 16 GB swapfile lived on the
SATA disk. Watchdog disabled for the window; power state identical to the
contour sweep (factory 187 W ceiling). After the ladder the script restored
the mount, the original swap and the NVMe serve (verified: endpoint live,
RAM guard kept the engine from starting while RAM was still busy).

## Numbers (engine's own accounting, thinking off, t=0.7)

| prompt tok | prefill NVMe tok/s | prefill SATA tok/s | TTFT NVMe | TTFT SATA |
|---|---:|---:|---:|---:|
| ~1k | 75.7 | **17.7** | 13.2 s | 54.6 s |
| ~8k | 186.1 | **55.9** | 44.2 s | 142.8 s |
| ~32k | 202.8 | **64.9** | 156.9 s | 490.2 s |

| prompt tok | warm decode NVMe tok/s | warm decode SATA tok/s |
|---|---:|---:|
| ~1k | 43.5 | **8.7** |
| ~8k | 40.2 | **9.7** |
| ~32k | 39.3 | **11.0** |

Cold generation runs stopped early at 63–84 tokens (temperature lottery) and
rate 3.7–3.9 tok/s; kept raw, not blended.

## Verdict

**Slow disk = machine unusable for this model: 3–4.3x slower prefill and 4x
slower decode.** The model is 78 GB on a 31 GiB-RAM box: everything beyond
the 16 GiB page-locked resident experts is streamed live from the file tier,
and IQ3_S row fetches are small random reads — exactly what a 2012 SATA SSD
is worst at (tens of MB/s effective random vs 300–500 MB/s on the NVMe).
The 16 GB SATA swap was touched up to 2.7 GB (vs never-used NVMe swap in
normal operation). GPU stayed cool (peak 96.6 W, 58 °C) — it spent the run
starving, not working. Conclusion for the fleet dataset: on this class of
box the data disk, not the GPU, sets the ceiling; the NVMe is mandatory
infrastructure, the SATA system disk cannot host the model at acceptable
speeds.

## Failures during orchestration (published per fleet rule)

1. **Orchestrator self-kill**: the first detach script lived under `/home`
   (cwd + fds), so its own `fuser -km /home` SIGKILLed it mid-sequence —
   trap could not run. Diagnosis: cwd/fd held the mount; fixed by running
   from `/` with redirected fds.
2. **Self-inflicted race**: a second script instance was launched while the
   first was still mid-ladder; the second's restore killed the first's
   engine (ladder rows `RemoteDisconnected`). Diagnosis: no single-instance
   guard. Lesson: one detached runner, poll-only supervision.
3. **Path-rewrite miss**: the sanitized slow config rewrote `exe`/`args`
   but left the `data/expert-profile.bin` directory un-copied; engine booted
   from SATA and then refused: `read_expert_profile: cannot open ...`.
   Fixed by copying the 496 KB profile dir; also an rsync nesting bug
   (`engines-avx/engines-0.1.55-avx`) caught by `strata --version`.

## Artifacts

Raw bundle `slowart.tar` (ladder jsonl, engine log, 1 Hz telemetry, serve
log, orchestrator script, master log) kept on the workstation, sha256-16
`ed90e2a0d2a58ce4`; inner file pins: ladder `ce22481ce94396e1`, engine log
`2a2867500be4ef21`, telemetry `4493a8d9c1dd08aa`, serve log
`269771f5249177a8`, orchestrator `09b093d516401ec2`.

Safe to publish: rates, sizes, temperatures only — no secrets, addresses
or account paths (paths normalized to role names in this file).
