#!/bin/bash
# cadence-249 stages 3+4: Grok + ChatGPT-codex legs on matched reps 25,26,27 (bank v6.4),
# pre-registered in REVIEW-INBOX 2026-11-07 (same entry as run_cad249.sh). Transports
# identical to cadence-246/band240: codex = subscription CLI xhigh read-only, prompt via
# STDIN; grok = hermes -z toolsets off, prompt inline (finding S3). Cloud legs never touch
# the serve; done-set keyed on (task,rep). PATH must be set explicitly: systemd-run --user
# scopes do not inherit the shell PATH (lesson from the dead codex legs).
set -u
export PATH="$HOME/.local/bin:$PATH"
LOG=~/parb-v64-contour/band249.log
command -v codex >/dev/null && command -v hermes >/dev/null || { echo "codex/hermes missing from PATH" >> $LOG; exit 1; }
cd ~/parb-v64-raw-reps || exit 1
date +%s > cloud-r252627-start.epoch
PARB_RAW_WS=~/parb-v64-raw-reps python3 ~/sah-main/scripts/raw_v6.py codex 25,26,27 >> band-codex.log 2>&1 &
pidc=$!
PARB_RAW_WS=~/parb-v64-raw-reps python3 ~/sah-main/scripts/raw_v6.py grok 25,26,27 >> band-grok.log 2>&1 &
pidg=$!
wait $pidc; rcc=$?
wait $pidg; rcg=$?
date +%s > cloud-r252627-end.epoch
echo "codex 25,26,27: rc=$rcc rows=$(grep -c '\"rep\": *2[567]' answers-codex.jsonl 2>/dev/null)" >> $LOG
echo "grok 25,26,27: rc=$rcg rows=$(grep -c '\"rep\": *2[567]' answers-grok.jsonl 2>/dev/null)" >> $LOG
echo "cad249 stage3+4 cloud done" >> $LOG
