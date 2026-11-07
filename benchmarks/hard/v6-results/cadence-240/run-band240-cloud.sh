#!/bin/bash
# Four-arm cadence stage 3 (owner rule; band240 header: "Grok/ChatGPT arms on the same seeds
# follow in the next cycle"). Matched reps 6,7,8 against contour 0.0.2.40 (q40r6/7/8) and
# bare basalt (answers-basalt.jsonl reps 6,7,8). Transports: codex = ChatGPT subscription CLI
# (xhigh, read-only, prompt via stdin), grok = hermes -z toolsets off, prompt inline (finding S3).
# done-set keyed on (task,rep); existing codex/grok reps 1,3 untouched, fresh rows appended.
set -u
# systemd-run scopes do not inherit the shell PATH; codex and hermes live in ~/.local/bin.
# The first launch of this script (23:40) died FileNotFoundError per task and wrote 34 dead rows
# per arm (purged, kept as *.bad-path.bak). Fail closed here instead of burning seeds on a bad PATH.
export PATH="$HOME/.local/bin:$PATH"
command -v codex >/dev/null && command -v hermes >/dev/null || { echo "codex/hermes missing from PATH" >> ~/parb-v61-contour/band.log; exit 1; }
cd ~/parb-v61-raw-reps || exit 1
date +%s > band-cloud-start.epoch
PARB_RAW_WS=~/parb-v61-raw-reps python3 ~/sah-main/scripts/raw_v6.py codex 6,7,8 >> band-codex.log 2>&1 &
pidc=$!
PARB_RAW_WS=~/parb-v61-raw-reps python3 ~/sah-main/scripts/raw_v6.py grok 6,7,8 >> band-grok.log 2>&1 &
pidg=$!
wait $pidc; rcc=$?
wait $pidg; rcg=$?
date +%s > band-cloud-end.epoch
echo "codex 6,7,8: rc=$rcc rows=$(grep -c '\"rep\": *[678]' answers-codex.jsonl)" >> ~/parb-v61-contour/band.log
echo "grok 6,7,8: rc=$rcg rows=$(grep -c '\"rep\": *[678]' answers-grok.jsonl)" >> ~/parb-v61-contour/band.log
echo "band-cloud done" >> ~/parb-v61-contour/band.log
