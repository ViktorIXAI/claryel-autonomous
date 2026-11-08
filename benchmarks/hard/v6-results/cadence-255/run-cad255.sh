#!/bin/bash
# cadence-255 stages 1+2: four-arm cadence on bank v6.6, contour leg at the adopted
# line 0.0.2.55, reps 52/53/54. Pre-registered in benchmarks/hard/REVIEW-INBOX.md
# at 2026-11-08 ~03:0x CET, BEFORE any row of this script.
# Stage 1: contour 0.0.2.55 (adopted after pair-252) on the idle P2005 Basalt serve.
# Stage 2: bare basalt single-shot on the SAME reps (raw seed 1000+rep), run SERIALLY
#          after stage 1 (never two local arms on one serve), answers in a fresh
#          ~/parb-b66-raw-reps/answers-basalt.jsonl (fresh (task,rep) done-set).
# Cloud legs (codex/grok) run in parallel via run-cad255-cloud.sh.
# Liveness = row COUNT + unit state, never GPU utilization.
set -u
export PATH="$HOME/.local/bin:$PATH"
command -v python3 >/dev/null || { echo "python3 missing"; exit 1; }
cd ~/parb-b66-contour || exit 1
LOG=band255.log
API="http://<LAN_IP>:8080/v1/chat/completions"   # reachable box IP (config host is the 0.0.0.0 bind trap)
for rep in 52 53 54; do
  python3 ~/sah-main/scripts/plan_reps.py bank.json $rep > plan-rep$rep.json 2>>$LOG || exit 1
  cp -f plan-rep$rep.json plan.json
  rid="q55r$rep"
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API="$API" \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
    PARB_GATE_VERSION=0.0.2.55 \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="cadence-255 stage 1: contour 0.0.2.55 (adopted line) on bank v6.6, matched seed rep $rep" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  rc=$?
  date +%s > "${rid}-end.epoch"
  echo "$rid: exit=$rc rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> $LOG
done
mkdir -p ~/parb-b66-raw-reps
cp -f bank.json ~/parb-b66-raw-reps/bank.json
cp -f p2005-profile.json ~/parb-b66-raw-reps/p2005-profile.json
cd ~/parb-b66-raw-reps || exit 1
date +%s > basalt-r525354-start.epoch
PARB_RAW_WS=~/parb-b66-raw-reps PARB_BASALT_CHAT_URL="$API" \
  python3 ~/sah-main/scripts/raw_v6.py basalt 52,53,54 >> band-basalt.log 2>&1
rc=$?
date +%s > basalt-r525354-end.epoch
echo "basalt 52,53,54: rc=$rc rows=$(grep -c '\"rep\": 5[234]' answers-basalt.jsonl 2>/dev/null)" >> ~/parb-b66-contour/band255.log
echo "cad255 stage1+2 done" >> ~/parb-b66-contour/band255.log
