#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../harness"

set -a
if [[ -f "$HOME/.hermes/.env" ]]; then
  . "$HOME/.hermes/.env"
fi
set +a

JOB_NAME="tb4-fast5-baseline-$(date +%Y%m%d-%H%M%S)"

exec uv run harbor run \
  --job-name "$JOB_NAME" \
  -p ../dataset/terminal-bench \
  -e docker \
  -m openai/qwen3.8-flash-next-iq3_s \
  --base-url http://[PRIVATE_IP]:8080/v1 \
  --api-key-name STRATA_API_KEY \
  --api-format openai_chat_completions \
  --allow-environment-host [PRIVATE_IP] \
  --allow-agent-host [PRIVATE_IP] \
  --agent terminal_bench_hermes_harness.hermes_verified:HermesBenchmark \
  --ak version=v0.22.6 \
  --ak max_turns=1000 \
  --ak disable_web_search=true \
  --agent-timeout-multiplier 0.375 \
  -i shadow-relay \
  -i fin-saccr-rwa \
  -i risk-scorer-replay \
  -i mp-checkpoint-consolidation \
  -i embedding-drift-monitor \
  -n 1 \
  -k 1 \
  -r 0 \
  -y \
  --jobs-dir ../jobs
