#!/usr/bin/env bash
# Second matrix: does the VRAM ceiling or the RAM ceiling own the lost 200 t/s?
# Arms: (vram-reserve, resident-budget) = (512,56) old config, (512,32), (512,22), (8591,22), (8591,32)
cd ~/basalt
KEYF=basalt.key
arm() {
  VR=$1; RB=$2
  python3 - "$VR" "$RB" <<'PY'
import json,sys
p="basalt-config.json"; d=json.load(open(p))
d["engine"]["vram-reserve-mib"]=int(sys.argv[1]); d["engine"]["resident-budget-gib"]=int(sys.argv[2])
json.dump(d,open(p,"w"),indent=2)
PY
  pkill -f "[b]in/basalt"; sleep 3; bash run-serve.sh
  for i in $(seq 1 40); do curl -s -m 8 http://127.0.0.1:8080/health | grep -q '"loaded": true' && break; sleep 8; done
  echo "=== arm vram-reserve=${VR}MiB budget=${RB}GiB loaded after $((i*8+3))s"
  free -h | sed -n '2p;3p'
  nvidia-smi --query-gpu=memory.used --format=csv,noheader
  for r in 1 2 3; do BRAIN_KEY=$(cat "$KEYF") python3 brainbench.py http://127.0.0.1:8080/v1 1 qwen3.8-flash-next-iq3_s-basalt 600 1024 2>&1 | grep -a '"run"'; done
  grep -a "s1 done" basalt-serve.log | tail -3 | cut -c1-150
  grep -aE "experts on SSD|file-only" basalt-serve.log | tail -2 | cut -c1-150
}
arm 512 56
arm 512 32
arm 512 22
arm 8591 22
arm 8591 32
echo ALL_V2_DONE
