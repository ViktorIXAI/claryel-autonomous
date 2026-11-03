# Reproducing the experiment

## What you need

* any local chat model behind an **OpenAI-compatible** `/v1/chat/completions`
  (llama.cpp server, vLLM, Ollama, LM Studio, Strata — anything that honors
  `temperature`, `seed`, `max_tokens`, and optional `thinking`/`chat_template_kwargs`)
* Python ≥ 3.9, standard library only
* ~6–24 h wall time for the full frozen plan (178 tasks × 11 categories ×
  fixed rep counts), depending on your decode speed; a smoke subset takes
  minutes.

The published numbers came from an IQ3_S-quantized open-weight Qwen-3.8
model on an RTX 3060 12 GB and on an Apple-Silicon Mac Studio. Any model will
produce *its own* numbers — the harness measurement machinery (paired seeds,
validators, ledgers) is what transfers.

## One series, end to end

```bash
./install.sh
cp config.example.sh config.sh && $EDITOR config.sh   # PARB_API, PARB_MODEL, PARB_BOX, PARB_TELEM
source config.sh
bash run_gate.sh                    # plan built once (plan_hash printed), then frozen
python3 harness/gate_report.py      # category table + failure causes + costs
```

For a full run, leave `PARB_TELEM` non-empty in `config.sh`. `run_gate.sh`
starts the 1 Hz resource collector automatically, runs the gate, then stops the
collector when the gate exits.

Every gate result and ledger row carries an `os` object: distribution, exact
version, Ubuntu codename, Desktop or Server flavor, flavor evidence, kernel and
architecture. Refresh fleet OS facts before comparing a machine after a system
migration:

```bash
python3 scripts/fleet/os_fleet_audit.py
```

The script reads local fleet access data from `~/.hermes/fleet-os.json` or
`PARB_FLEET_OS_CONFIG`. That file remains local-only; commit only sanitized
launch environments and the date-stamped snapshot summary, never access data.

The runner is **resumable**: `state*.json` tracks completed `(task, rep, series)`
positions; Ctrl-C / `harness/stop_series.sh <state-substring>` and re-run to
continue. A wall-clock deadline (`PARB_LIMIT`, default 4 h) and resource
stop-gates (low RAM, GPU >89 °C, endpoint unhealthy) pause/stop cleanly —
"plan exhausted" and "stopped by gate" are recorded in the state file, never
silently.

## Smoke subset first (recommended)

```bash
PARB_SUBSET="A-ea-00-0,B-ea-00-0,D-ea-00-0,J-ea-00-0,K-ea-00-0" \
PARB_STATE=state-smoke.json PARB_RESULTS=results-smoke.jsonl \
PARB_LEDGER=gate-ledger-smoke.jsonl PARB_LIMIT=1000 \
PARB_TELEM=telemetry-smoke.jsonl PARB_TELEM_INTERVAL=1.0 \
  bash run_gate.sh
```

## Pairwise A/B between contour versions (the method behind every number)

1. Finish version A over plan positions; keep `results-vA.jsonl`.
2. Trim `plan.json` to exactly the `(task, rep)` keys A already covered
   (see `plan.json.bak-*` pattern; `experiments/ab/` has the helpers).
3. Launch version B (`PARB_GATE_VERSION=vB`, fresh state/results/ledger names).
4. Compare paired: `python3 experiments/ab/compare_ab.py` and
   `python3 analytics/aggregate.py` — deltas are per `(task, rep)`.
5. Repeat on a second machine if the verdict matters (`PARB_BOX` differs;
   pairing keys are machine-independent; extension seeds come from
   `sha256(f"{task}|{rep}")` so every box draws identical samples).

`PARB_GATE_VERSION` selects the stamped revision inside one codebase.
Canonical values are four-part, such as `0.0.1.9`, `0.0.2.0`, `0.0.2.1` and
`0.0.2.2`; legacy `v1.x`/`v2.x` names are accepted and normalized.
`0.0.2.2` adds targeted F diagnostic grounding. `0.0.2.3` (resource telemetry),
`0.0.2.4` (full-Mac resource verdict), `0.0.2.5` (OS environment records) and
`0.0.2.6` (two-axis version record) changed measurement or reporting only: every
one of them runs contour behavior `0.0.2.2`, and each artifact carries a
`contour_behavior` field that states this, so never infer a contour change from
the stamped revision alone (see `versions/VERSIONS.md`). `0.0.2.7` is a contour
change again: `K_NEGATION` grounds the K tax-negation flag in the task's own
visible text (explicit exclusion sentence means yes, silence about taxes means
no); it is a candidate until a paired run proves it.
`PARB_CHEAP=1` re-enables
the *rejected* cheap-model-repair path for experiments only — beware, it is
rejected for a reason.

## Deep probes (failure classification)

`experiments/probes/probe-plan.json` × `experiments/ab/classify_v19p.py`:
take the worst tasks per category, ×3 reps with rep numbers ≥9001 on an
idle endpoint, then classify:

* **CHRONIC** (all reps < 0.75) → contour blind to the class → structural change
* **LOTTERY** (max−min spread > 0.5) → seed variance → best-of-N, not nudges
* **FIXED** (new version 1.00 where old final was < 0.6) → confirmed contour win

## Aggregates

`analytics/aggregate.py` recomputes `results/summary.json` from raw
`results-*.jsonl` + `gate-ledger-*.jsonl`. The raw archives are **not**
committed (they carry ~40k model outputs); point `PARB_ARTIFACTS` at a
downloaded release archive's `artifacts/` directory to recheck every published
number yourself. `logs/INDEX.md` pins each raw file by SHA-256.
