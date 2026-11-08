#!/bin/bash
# Paired loop-only contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.55 (ADOPTED control line after pair-252, contour behavior 2.55) vs
# 0.0.2.56 (loop best-of-3 selection on the banned_attempted family: one further draw at
# seed+16234 only while the best-after-two-draws still carries the note; strict-better-only
# adoption; own v56_* events; the 2.43 first retry and every frozen family are untouched).
# TARGET (published in REVIEW-INBOX 2026-11-08 08:00 CET + gate_versioning (2,56) comment
# BEFORE any w55r5x/w56r5x row; live_target_check.py on UNSTABLE-CELLS-V66-255.csv answered
# LIVE: D-ex6-l0 fails=2 families=banned_attempted at stamp 0.0.2.55):
# D-ex6-l0 strict-fails 2/6 on the adopted line; the v243 banned retry fires 3/6 and converts
# 1/3 (x55r48 win; x55r50/q55r53 both candidates still carried banned_attempted:SEND_EMAIL).
# PRE-REGISTERED RULE (REVIEW-INBOX frozen BEFORE any arm row - the verdict is decided ONLY by
# that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (w55) row strict-fails D-ex6-l0. Zero live
#      target = UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the
#      control strict-failed (control row carrying banned_attempted) AND the candidate row
#      carries contour:v56_d_best3_banned_fired + fix:v56_d_best3_banned_win.
#  (c) GUARDS: zero v56 events in any control arm; zero v56 fires on rows whose
#      best-after-two-draws has no banned_attempted stem (never 2.11/claim triggers); zero
#      fires outside kind==loop; frozen-band parity (zero 2.30-32/34-config/36/38/41/42/44/54
#      events in either arm); v243 first-draw parity self-consistent per arm; stall protocol
#      (engine_stalled rows excluded, abort above 25% of last 20).
#  (d) RESOLUTION: loop pool 6 tasks x 3 seeds = 18 cells/arm; on-target surface D-ex6-l0 max
#      3 cells -> DIRECTIONAL evidence only (pair-243 n=6 caveat restated). ADOPT 0.0.2.56 iff
#      (a) + >=1 evented conversion + all guards clean + loop-pool W-L >= +2 with zero
#      guard-attributable losses; otherwise FREEZE D_BEST2_BANNED_RETRY2 to STAMP_REVISION ==
#      (2,56) and publish with win-level detail.
# Loop-only pair: 6 of 77 tasks -> run_digest.py fail-closes by design, NO whole-bank percent
# row for pair-256 (documented in the pre-registration).
# Energy per arm from gpu-power-p256.csv windows (per-arm -start.epoch/-end.epoch); the
# mechanism costs <=1 extra loop reroll (~3 model calls) per still-banned row.
set -u
cd <LOCAL_PATH>/parb-b66-contour || exit 1
for rep in 55 56 57; do
  plan=plan-rep${rep}.json
  for v in 55 56; do
    rid="w${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired loop-only contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.56 = loop best-of-3 on banned_attempted: second selection draw at seed+16234 gated on the best-after-two-draws still carrying the note, strict-better-only, own events; control 0.0.2.55 = adopted line after pair-252; 2.30-2.34/2.36/2.38/2.41/2.42/2.44/2.54 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep57.json plan.json
echo "pair256 done" >> queue.log
