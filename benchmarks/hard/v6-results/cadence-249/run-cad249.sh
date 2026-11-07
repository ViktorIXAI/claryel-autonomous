#!/bin/bash
# cadence-249: four-arm cadence on bank v6.4 (first full-pool v6.4 numbers; owner P0
# continuation after the v6.2->v6.4 bank migration). Pre-registered in
# benchmarks/hard/REVIEW-INBOX.md at 2026-11-07 ~14:2x CET, BEFORE any row of this script.
# Stage 1: contour at 0.0.2.49 = release 2.49 tooling, contour BEHAVIOR 2.48 = the adopted
#          line (pair-247); no contour feature registers at 2.49 (gate_v63 pins the matrix).
# Stage 2: bare basalt single-shot on the SAME reps (raw seed 1000+rep), answers in
#          ~/parb-v64-raw-reps/answers-basalt.jsonl (fresh file, fresh (task,rep) done-set).
# Grok + ChatGPT-codex legs on the same reps run in parallel via run_cad249_cloud.sh
# (cloud legs never touch the serve). Liveness = row COUNT + unit state, never GPU utilization.
set -u
export PATH="$HOME/.local/bin:$PATH"
command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
cd ~/parb-v64-contour || exit 1
LOG=band249.log
API="http://<LAN_IP>:8080/v1/chat/completions"   # reachable box IP (config host is the 0.0.0.0 bind trap)
for rep in 25 26 27; do
  python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$LOG || exit 1
  cp -f plan-rep$rep.json plan.json
  rid="q49r$rep"
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API="$API" \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
    PARB_GATE_VERSION=0.0.2.49 \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="cadence-249 stage 1: contour 0.0.2.49 (behavior 2.48, adopted line) on bank v6.4, matched seed rep $rep" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  rc=$?
  date +%s > "${rid}-end.epoch"
  echo "$rid: exit=$rc rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $LOG
done
mkdir -p ~/parb-v64-raw-reps
cp -f bank.json ~/parb-v64-raw-reps/bank.json
cp -f p2005-profile.json ~/parb-v64-raw-reps/p2005-profile.json
cd ~/parb-v64-raw-reps || exit 1
date +%s > basalt-r252627-start.epoch
PARB_RAW_WS=~/parb-v64-raw-reps PARB_BASALT_CHAT_URL="$API" \
  python3 ~/sah-main/scripts/raw_v6.py basalt 25,26,27 >> band-basalt.log 2>&1
rc=$?
date +%s > basalt-r252627-end.epoch
echo "basalt 25,26,27: rc=$rc rows=$(grep -c '\"rep\": 2[567]' answers-basalt.jsonl 2>/dev/null)" >> ~/parb-v64-contour/band249.log
echo "cad249 stage1+2 done" >> ~/parb-v64-contour/band249.log
