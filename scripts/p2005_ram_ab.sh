#!/usr/bin/env bash
# RAM-tier A/B for the fleet brain: fixed 15.5 GiB VRAM ceiling, varying resident
# expert budget in RAM (20 / 25 / 56 GiB). Absolute tok/s comes from the engine's own
# "done" lines; the SSE bench drives the load and reports TTFT.
cd ~/basalt || exit 1
KEYF=$(ls basalt.key 2>/dev/null)
for B in 20 25 56; do
  python3 - "$B" <<'PY'
import json,sys
p="basalt-config.json"; d=json.load(open(p)); d["engine"]["resident-budget-gib"]=int(sys.argv[1])
json.dump(d,open(p,"w"),indent=2)
PY
  pkill -f "[b]in/basalt"; sleep 3; bash run-serve.sh
  for i in $(seq 1 30); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && break; sleep 10; done
  echo "=== budget=${B}GiB loaded after $((i*10+3))s; state:"
  free -h | sed -n '2,3p'; nvidia-smi --query-gpu=memory.used --format=csv,noheader
  MARK=$(wc -l < basalt-serve.log)
  sleep 15
  echo "--- bench 600/256 x3"; BRAIN_KEY=$(cat "$KEYF") python3 brainbench.py http://127.0.0.1:8080/v1 3 qwen3.8-flash-next-iq3_s-basalt 600 256
  echo "--- bench 600/1024 x2 (sustained peak)"; BRAIN_KEY=$(cat "$KEYF") python3 brainbench.py http://127.0.0.1:8080/v1 2 qwen3.8-flash-next-iq3_s-basalt 600 1024
  echo "--- bench 4000/256 x1 (prefill)"; BRAIN_KEY=$(cat "$KEYF") python3 brainbench.py http://127.0.0.1:8080/v1 1 qwen3.8-flash-next-iq3_s-basalt 4000 256
  sleep 5
  echo "=== engine stats while budget=${B}:"; tail -n +"$((MARK+1))" basalt-serve.log | grep -aE "s[0-9]+ done" | tail -12
done
echo ALL_AB_DONE
