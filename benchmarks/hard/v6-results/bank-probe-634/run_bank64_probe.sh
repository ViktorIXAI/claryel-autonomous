#!/bin/bash
# v6.4 probe (rule frozen in REVIEW-INBOX 2026-11-07 12:20 CET before any p64 row): contour
# 0.0.2.48, sp1 seeds 861061/593370/188460 (reps 22/23/24), PARB_SUBSET=B-ex6-04, workspace built
# from bank-hard-v6.4.json (published sha16 85a0cd0dd6fa1fab), serial on the idle P2005 endpoint.
# Fresh 0/3 controls at the identical seeds already exist for v6.2 (p62r22-24) and v6.3 (p63r22-24).
set -u
for rep in 22 23 24; do
  rid="p64r${rep}"
  cd /<LOCAL_PATH> || exit 1
  cp -f "plan-rep${rep}.json" plan.json
  date +%s > "${rid}-start.epoch"
  PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
    PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=<KEYFILE> \
    PARB_GATE_VERSION=0.0.2.48 PARB_SUBSET=B-ex6-04 \
    PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
    PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
    PARB_RUN_NOTES="bank v6.4 probe (v6.3 + penalty_per_week value-form hint, gold bytes identical) contour 0.0.2.48 seed ${rep} on B-ex6-04 only; paired against p62r*/p63r* at identical sp1 seeds" \
    python3 -u gate_run.py > "${rid}.log" 2>&1
  echo "$rid: exit=$? rows=$(wc -l < results-${rid}.jsonl 2>/dev/null)" >> queue.log
done
echo "bank64probe done" >> queue.log
