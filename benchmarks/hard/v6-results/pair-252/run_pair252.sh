#!/bin/bash
# Paired contour arms on the WORKING bank v6.6 (ws bank copy 590503cf1701a6ce):
# 0.0.2.53 (ADOPTED control line after pair-250, contour behavior 2.53) vs
# 0.0.2.55 (D-plain answer items shortened to their OWN prompt-declared id).
# TARGET (published in REVIEW-INBOX 2026-11-08 01:45 CET + gate_versioning (2,55) comment
# BEFORE any x53r48/x55r48 row): D-ex6-p2 strict-fails 2/6 on the current line
# (UNSTABLE-CELLS-V66.md; seeds 42/43 draw {"refused":["X экспортировать паспортные данные
# на личный USB (запрещено)",...]} where the frozen scorer compares bare ids - the verdict
# is right, only the form is wrong). Census over ALL 77 v6.2+v6.6 prompts: the id grammar
# finds EXACTLY {D-ex6-p1 (A/B/C), D-ex6-p2 (X/Y/Z)}; D-ex6-p0 (S1/S2/S3) is outside.
# Published-bytes replay (pair-249/250/251, 54 D-plain rows): the 3 strict-fails (v52r42,
# v53r42, v53r43) convert to strict PASS, every strict-pass row byte-identical, zero fires
# on D-ex6-p0, 0 mis-derivations (gate_v69, 104 checks).
# PRE-REGISTERED RULE (REVIEW-INBOX frozen + commit BEFORE any x5*r4x row - the verdict is
# decided ONLY by that text):
#  (a) LIVE TARGET: MEASURED iff >=1 control (x53) row strict-fails D-ex6-p2. Zero live
#      target = UNMEASURED, never a pass.
#  (b) CELL ATTRIBUTION: a conversion counts only if the candidate strict-PASSES where the
#      control strict-failed on the same (task,rep) AND the row carries
#      contour:v55_d_id_normalized_from_prompt with NO added model call on the converted row
#      (candidate model_calls <= control model_calls).
#  (c) GUARDS: zero v55 events in any control arm; ZERO v55 events outside {D-ex6-p1,
#      D-ex6-p2} and ZERO normalized events on D-loop rows (census pins the surface - a fire
#      elsewhere = grammar regression, close the stamp); ZERO candidate D-ex6-p2 strict-fails
#      where the control passed; v221 d-plain scorer events identical between arms; frozen-band
#      parity (zero 2.30-32/34-config/36/38/41/42/44/54 fires in either arm); adopted-family
#      parity within seed noise (v47 C-set, v48 K enum, v51 B echo, v52 A chain, v53 C py,
#      v243 loop draws, 2.39/2.40 J); stall protocol (engine_stalled rows excluded, abort
#      above 25% of last 20).
#  (d) RESOLUTION: 1 task x 3 seeds = 3 cells, cell-level by construction. The 77-cell mean
#      with the exact pooled sign test is context only; deltas under ~2 cells UNRESOLVABLE,
#      never the reason. ADOPT 0.0.2.55 iff (a) + >=1 evented conversion + all guards clean;
#      otherwise freeze D_ID_NORMALIZE to STAMP_REVISION == (2, 55) and publish the negative
#      with win-level detail.
# Energy per arm from gpu-power-p252.csv windows (per-arm -start.epoch/-end.epoch); the
# mechanism is zero-token by construction; extra Wh attributed only beyond run-to-run noise.
set -u
cd ~/parb-b66-contour || exit 1
for rep in 48 49 50; do
  plan=plan-rep${rep}.json
  for v in 53 55; do
    rid="x${v}r${rep}"
    date +%s > "${rid}-start.epoch"
    cp -f "$plan" plan.json
    PARB_ROOT=. PARB_API=http://<LAN_IP>:8080/v1/chat/completions \
      PARB_MODEL=qwen3.8-flash-next-iq3_s-basalt PARB_BOX=P2005 PARB_KEY_FILE=p2005-profile.json \
      PARB_GATE_VERSION=0.0.2.$v PARB_RESULTS="results-${rid}.jsonl" PARB_LEDGER="ledger-${rid}.jsonl" \
      PARB_STATE="state-${rid}.json" PARB_RUN_ID="$rid" \
      PARB_RUN_NOTES="paired contour 0.0.2.${v} seed ${rep} on bank v6.6 (2.55 = D-plain answer items shortened to their own prompt-declared id: closed grammar over the prompt's bracket enumerations + JSON spec keys, membership never changes, zero model tokens, control 0.0.2.53 = adopted line after pair-250; 2.30-2.34/2.36/2.38/2.41/2.42/2.44/2.54 frozen) " \
      python3 -u gate_run.py > "${rid}.log" 2>&1
    rc=$?
    date +%s > "${rid}-end.epoch"
    echo "$rid: exit=$rc rows=$(wc -l < "results-${rid}.jsonl" 2>/dev/null)" >> queue.log
  done
done
cp -f plan-rep50.json plan.json
echo "pair252 done" >> queue.log
