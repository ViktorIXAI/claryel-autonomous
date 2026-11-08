# How map-256 was launched (prose; the real scripts stay untracked)

Serial queue under one `systemd-run --user --collect --unit=parb-map256 bash <absolute
run_map256.sh>` unit started from a cron session (units survive the session; the arms run
inside it). Per leg, in workspace `~/parb-b66-contour` (bank v6.6 ws copy `590503cf1701a6ce`):
`cp plan-repNN.json plan.json`, then `gate_run.py` with `PARB_GATE_VERSION=0.0.2.56`,
`PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt`, `PARB_API=http://<LAN_IP>:8080/v1/chat/completions`
(P2005 Basalt endpoint, idle-checked first: GPU 0%, zero other gate_run on the box),
`PARB_KEY_FILE=p2005-profile.json` (auth-checked before launch with `GET /v1/models` — 200,
alias `qwen3.8-flash-next-iq3_s-basalt`), fresh `results/ledger/state/log` names per rid,
`-start.epoch`/`-end.epoch` per arm, exit code + row count appended to `queue.log`.

GPU sampler: a separate `systemd-run --user --collect --unit=parb-m256sampler` unit ran a
2 Hz loop that ssh'd to the endpoint box (`ssh <user>@<LAN_IP>`, repo-standard key) and
appended `epoch,power_W,util_pct,mem_used_MB,temp_C` to a fresh `gpu-power-m256.csv`; empty
reads skipped; stopped immediately at `map256 done` (387 samples). Windows per arm computed
with `scripts/gpu_energy.py <csv> --start <epoch> --end <epoch>`.

Harness integrity: workspace harness files byte-identical to repo HEAD `8ada24a` (diffed
before launch: `gate_versioning.py` and `gate_run.py` identical); the ws `HARNESS_GIT_SHA`
marker was rewritten to the verdict sha because the verdict commit rebuilt the ws pins — run
records therefore attribute to `8ada24a`. First log line of every leg: `release 0.0.2.56,
contour behavior 2.56` (stamp == behavior).
