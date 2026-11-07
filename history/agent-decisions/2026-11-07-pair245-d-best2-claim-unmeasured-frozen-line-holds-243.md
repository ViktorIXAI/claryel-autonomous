# 2026-11-07 — pair-245: 0.0.2.44 (loop best-of-2 on `false_completion_claim`) UNMEASURED — flag frozen to exactly (2,44), the line holds 0.0.2.43

## Decision

`D_BEST2_CLAIM` is frozen to `CONTOUR_REVISION == (2, 44)`. The contour line stays `0.0.2.43`.
No pair-246 stamp is launched on bank v6.1: the pre-launch measurability gate finds no live
target left on this bank (see Close below). The next launchable step is the queued v6.2 stack
move (workspace + stability map + four-arm cadence), decided per the owner directive of 07.11
(decisions delegated; never stop to ask).

## Evidence

Pre-registered rule (REVIEW-INBOX 2026-11-07 03:58 CET + `run_pair245.sh` header, written before
any `q*` row): MEASURED iff >=1 control loop row carries the claim note AND strict-fails.
Measured: **zero** control rows (18 loop cells, three seeds) drew `false_completion_claim`;
the family's live rate on the line is 0/18 against a published archive base rate of 13/504.
The pair is UNMEASURED — the fourth zero-opportunity pair after 233/238/242 — and UNMEASURED is
never a pass. Live wiring proven anyway: the candidate's own claim draw (D-ex6-l3 seed 2, an
already-passing cell) fired the third offset and adopted a clean retry (fired+win events, claim
note absent from the adopted trajectory). All guards clean: zero loop P->F, zero v244 events
outside loop rows, zero frozen-band events, adopted-2.43 parity (v243 fires only on banned-note
draws in both arms), pool 209/231 vs 212/231 (8W/5L p=0.58, floor noise), loop cost +1 retry
(+6.3% loop ptok), energy 17.72 vs 18.24 Wh. Full tables: `PAIR-245-V61.md`.

## Why frozen, not kept

`contour_at_least(2, 44)` would inherit an UNTESTED trigger into every future arm — the
zero-opportunity pairs (233/238/242/245) are exactly how the adoption rule got poisoned before,
and the pre-registered text decided this outcome before the first row: freeze on non-MEASURED.
The trigger itself is contract-tested (gate_v58 39 checks) and proven live-firing; what is not
proven is conversion, and the family at 0/18 live draws gives the mechanism no surface to prove
it on this bank. Re-chasing it with more seeds repeats the zero-opportunity pattern and is
closed by this record until a bank change makes the family live again (v6.2 watch-list).

## Close: bank v6.1 pair queue is closed at the ceiling (both pools)

The pair-245 control arm mapped the adopted line's 22 remaining strict fails: every one is a
bank defect already fixed in v6.2 (A-ex6-03, C-ex6-02), a frozen-negative class (B-ex6-04,
group-4 H/F), a published unreachable prompt (C-ex6-00/01), a designed refusal (J-ex6-03), or a
banned-family loop cell that already spent its one monotone retry. Launching any candidate
against this set violates the pre-launch measurability gate (three such pairs burned 18 arms of
serve time this series). Decision: close the v6.1 contour pair queue; feed hypotheses only from
a v6.2 stability map.

## Stack state after this decision

- `harness/gate_run.py`: `D_BEST2_CLAIM = CONTOUR_REVISION == (2, 44)` (live smoke: 2.43 OFF,
  2.44 ON, all frozen bands OFF at both).
- `gate_versioning.py` 2.44 entry carries the measured outcome; CURRENT_REVISION stays (2,44).
- gate_v49 51 + gate_v57 37 + gate_v58 39 + versioning + fixers 12/12 PASS on the frozen tree;
  workspace rebuilt + repinned, `verify_manifest.py --v6` PASS, ws bank `f4553aab304f60d7`
  (sha256-16) unchanged, published bank `9ec86dfca4a6f85f` untouched.
- `UNSTABLE-CELLS-V61.md` gets the 04:55 addendum (closure map + v6.2 watch-list);
  `README.md` candidate history gains the pair-245 entry; the queue now reads: v6.2 workspace
  build -> line map -> four-arm cadence -> pre-registered pairs against the v6.2 map.
