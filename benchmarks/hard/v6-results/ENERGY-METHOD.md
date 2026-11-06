# Energy measurement method (and what it cannot see)

## What is measured

A systemd user unit samples the inference GPU every ~2 seconds while arms run:

```bash
systemd-run --user --collect --unit=parb-gpu-samp --working-directory=<LOCAL_PATH> bash -c \
'while true; do
   ts=$(date +%s.%N)
   v=$(ssh -o StrictHostKeyChecking=no -i <KEY_FILE> <SSH_USER>@<INFERENCE_HOST> \
        "nvidia-smi --query-gpu=power.draw,utilization.gpu,memory.used,temperature.gpu \
         --format=csv,noheader,nounits" 2>/dev/null)
   [ -n "$v" ] && echo "$ts,$v" >> gpu-power.csv
   sleep 2
 done'
```

`scripts/gpu_energy.py` and `scripts/cost_table_v61.py` integrate that trace with the trapezoid rule
(`sum(power_W x dt) / 3600 = Wh`) over explicit windows: a contour arm's window comes from
`rep3-start.epoch` / `rep3-end.epoch` written by the runner, the raw arm's window from the systemd unit's
`ActiveEnterTimestamp` / `InactiveExitTimestamp`, with the number of tasks inside the window derived from
the run log's own per-task `stop X s` lines.

## What it cannot see (stated, not hidden)

- **Board draw, not wall outlet.** `nvidia-smi power.draw` is the GPU module's power, excluding the
  inference box's CPU, RAM, PSU losses and the benchmark driver host. A metered PDU would close that; it
  is not installed on this box.
- **No CPU package energy.** Intel RAPL domains (`/sys/class/powercap/intel-rapl:0/energy_uj`) are
  root-readable only, and non-interactive sudo is refused on the benchmark host, so package joules are
  not collected here. This is why the local CPU-side cost of the contour driver is not in the table.
- **Cloud arms are not measurable from this machine.** Their energy lives in someone else's datacenter;
  what is reported is wall seconds, model calls and (where the transport reports it) tokens.
- **Sampling jitter.** ssh round-trip puts samples at ~2.5 s spacing rather than 2.0 s; the integrator
  uses actual `dt` between samples and rejects gaps over 30 s, so the integral follows the real clock.
- **Serve idle power is inside the window.** A contour arm's window includes the serve's own idle draw
  between tasks; that is the correct cost of running the arm end-to-end, but it means the figure is not
  "joules per token".

## Why the local-vs-cloud comparison still means something

The local arm's energy is a measured, bounded number for a complete 77-task run on one 24 GB GPU. The
cloud arms' seconds and calls are also measured, and their per-call cost is what the owner pays per
token. Putting the two in one table with different units (measured Wh vs measured seconds/calls) is
honest as long as nobody converts one into the other; nobody here does.
