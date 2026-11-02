# Copy to config.sh and source it. Everything is optional except PARB_API if
# your endpoint is not http://127.0.0.1:8080.
export PARB_API="http://127.0.0.1:8080/v1/chat/completions"   # any OpenAI-compatible endpoint
export PARB_MODEL="qwen3.8-flash-next-iq3_s"                  # model name your endpoint expects
export PARB_BOX="box1"                                        # free-form machine label
export PARB_GATE_VERSION="0.0.2.4"                            # current contour/tooling release
export PARB_ROOT="$HOME/parb"                                 # run dir (state/results written here)
export PARB_STATE="state-run.json"
export PARB_RESULTS="results-run.jsonl"
export PARB_LEDGER="gate-ledger-run.jsonl"
export PARB_LIMIT="14400"                                     # wall-clock budget, seconds
# Optional: JSON file containing {"api_key": "..."} for protected endpoints.
# export PARB_KEY_FILE="$HOME/endpoint-key.json"
# Optional: 1 Hz resource telemetry. When PARB_TELEM is non-empty, run_gate.sh
# starts telemetry/collector2.py around the gate automatically.
export PARB_TELEM=""                                          # e.g. telemetry-run.jsonl
export PARB_TELEM_INTERVAL="1.0"                              # seconds
# Optional: pin the serving GPU on Linux. Empty means largest-VRAM GPU.
export PARB_GPU_INDEX=""
