#!/bin/bash
# Paired loop-only contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.56 (ADOPTED control line after pair-256) vs 0.0.2.57 (claim-family loop selection
# re-armed under the pair-248 meta-rule: one retry at seed+12289 on first-draw rows whose
# loop-scorer notes carry a false_completion_claim stem, strict-better-only, own v57_*
# events; the 2.56 second draw stays banned-only; frozen 2.44 bytes immutable).
# TARGET (published in REVIEW-INBOX 2026-11-08 09:55 CET + gate_versioning (2,57) comment
# BEFORE any x56r6x/x57r6x row; live_target_check.py on UNSTABLE-CELLS-V66-256.csv answered
# LIVE at 2026-11-08 08:53:17Z: D-ex6-l4 fails=1 families=false_completion_claim at 0.0.2.56):
# D-ex6-l4 strict-fails 1/3 on the line and the claim family hit 3/9 published 2.55/2.56-era
# loop draws, every one strict-failing at content 0.3; no adopted trigger matches the note.
# PRE-REGISTERED RULE (REVIEW-INBOX frozen BEFORE any arm row - the verdict is decided ONLY by
# that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (x56) row carries a false_completion_claim note
#      AND strict-fails. Zero live target = UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the
#      control strict-failed (control row carrying the claim note) AND the candidate row
#      carries contour:v57_d_best2_claim_fired + fix:v57_d_best2_claim_win with the claim note
#      ABSENT from the adopted trajectory.
#  (c) GUARDS: zero v57 events in any control arm; zero v57 events outside kind==loop rows;
#      ZERO candidate loop strict-fails where control strict-passed (else close the stamp);
#      no third draw (seed+16234) on claim-triggered rows; frozen-band parity (zero
#      2.30-32/34-config/36/38/41/42/44/54 events either side); adopted-family parity (v243/
#      v56 draws only on banned notes in BOTH arms, v31 only on its notes, J/B/K/C families
#      identical within seed noise); stall protocol (engine_stalled excluded, abort >25%).
#  (d) RESOLUTION: loop pool 6 tasks x 3 seeds = 18 cells/arm; on-target claim surface max
#      ~3 cells -> DIRECTIONAL evidence only (pair-243 n=6 caveat restated). ADOPT 0.0.2.57
#      iff (a) + >=1 evented conversion + all guards clean + loop-pool W-L >= +2 with zero
#      guard-attributable losses; otherwise FREEZE D_BEST2_CLAIM_V57 to STAMP_REVISION ==
#      (2,57) and publish with win-level detail.
# Loop-only pair: 6 of 77 tasks -> run_digest.py fail-closes by design, NO whole-bank percent
# row for pair-257 (documented in the pre-registration).
set -u
cd <LOCAL_PATH>/parb-b66-contour || exit 1
for rep in 61 62 63; do
  plan=plan-rep${rep}.json
  for v in 56 57; do
    rid="x${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired loop-only contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.57 = claim-family loop selection re-armed per pair-248 meta-rule: one retry at seed+12289 gated on first-draw false_completion_claim notes, strict-better-only, own v57_* events; control 0.0.2.56 = adopted line after pair-256; 2.30-2.34/2.36/2.38/2.41/2.42/2.44/2.54 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep63.json plan.json
echo "pair257 done" >> queue.log
