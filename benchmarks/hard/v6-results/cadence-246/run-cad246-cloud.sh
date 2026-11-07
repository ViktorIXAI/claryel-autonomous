#!/bin/bash
# cadence-246 stages 3+4: Grok + ChatGPT-codex legs on matched reps 16,17,18 (bank v6.2),
# pre-registered in REVIEW-INBOX 2026-11-07 06:20 CET. Transports identical to band240:
# codex = subscription CLI xhigh read-only, prompt via STDIN; grok = hermes -z toolsets off,
# prompt inline (finding S3). Cloud legs never touch the serve; done-set keyed on (task,rep).
set -u
export PATH="$HOME/.local/bin:$PATH"
LOG=~/parb-v62-contour/band246.log
command -v codex >/dev/null && command -v hermes >/dev/null || { echo "codex/hermes missing from PATH" >> $LOG; exit 1; }
cd ~/parb-v62-raw-reps || exit 1
date +%s > cloud-r161718-start.epoch
PARB_RAW_WS=~/parb-v62-raw-reps python3 ~/sah-main/scripts/raw_v6.py codex 16,17,18 >> band-codex.log 2>&1 &
pidc=$!
PARB_RAW_WS=~/parb-v62-raw-reps python3 ~/sah-main/scripts/raw_v6.py grok 16,17,18 >> band-grok.log 2>&1 &
pidg=$!
wait $pidc; rcc=$?
wait $pidg; rcg=$?
date +%s > cloud-r161718-end.epoch
echo "codex 16,17,18: rc=$rcc rows=$(grep -c '\"rep\": *1[678]' answers-codex.jsonl 2>/dev/null)" >> $LOG
echo "grok 16,17,18: rc=$rcg rows=$(grep -c '\"rep\": *1[678]' answers-grok.jsonl 2>/dev/null)" >> $LOG
echo "cad246 stage3+4 cloud done" >> $LOG
