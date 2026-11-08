# How map-258 was launched (prose; the real scripts stay untracked)

Serial queue under one `systemd-run --user --collect --unit=parb-map258 bash <absolute
run_map258.sh>` unit started from a cron session (units survive the session; the arms run
inside it). Per leg, in workspace `~/parb-v68full-contour` (bank v6.8 ws copy `361f7bdb24d6ac71`):
`cp plan-repNN.json plan.json`, then `gate_run.py` with `PARB_GATE_VERSION=0.0.2.56`,
`PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt`, `PARB_API=http://<LAN_IP>:8080/v1/chat/completions`
(P2005 Basalt endpoint, idle-checked first: GPU 0%, zero other gate_run on the box),
`PARB_KEY_FILE=<ws>/p2005-profile.json` (auth-checked before launch with `GET /v1/models` — 200,
alias `qwen3.8-flash-next-iq3_s-basalt`), fresh `results/ledger/state/log` names per rid,
`-start.epoch`/`-end.epoch` per arm, exit code + row count appended to `queue.log`. A 3-task
smoke (subset A-ex6-00,C-ex6-00,D-ex6-l0, fresh state) ran first and printed
`release 0.0.2.56, contour behavior 2.56` with real tokens on every row before the full legs.

GPU sampler: a separate `systemd-run --user --collect --unit=parb-m258sampler` unit ran a 2 Hz
loop that ssh'd to the endpoint box (`ssh <user>@<LAN_IP>`, repo-standard key) and appended
`epoch,power_W,util_pct,mem_used_MB,temp_C` to a fresh `gpu-power-m258.csv`; it self-stops on the
`map258 done` queue sentinel (966 samples). Windows per arm via `scripts/gpu_energy.py`.

Harness integrity: workspace harness files byte-identical to repo HEAD `2251649`; the v6.8
workspace was built with `build_hard_v6_ws.py --bank bank-hard-v6.8.json`, whose
`bank-version.json` marker carries `status: working` (the pin set `WS-GENERATED.v68full.sha256`
was refreshed in this commit — the v6.8 promotion had flipped the marker from `provisional` to
`working` without re-pinning it, so a fresh v6.8-full build failed the WS-DRIFT gate on that one
line). The workspace is built with `--write-pins` in the same invocation as the run because the
marker embeds a build-time `built_utc`; every SCORING byte (bank.json, plan, gate_*.py, the
pinned scorer adapters) reproduces identically. First log line of every leg:
`release 0.0.2.56, contour behavior 2.56` (stamp == behavior).
