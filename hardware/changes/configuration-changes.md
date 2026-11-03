# Configuration change log

| date | machine | change | evidence | affects |
|---|---|---|---|---|
| `not_recorded` (before 2026-10) | B2003 | one of two 24 GB DDR5-5600 modules removed → single-channel 24 GB | dmidecode 2026-11-01 (slot empty) + bench notes | all B2003 speed numbers (memory-bandwidth-bound prefill) |
| between Oct 12 and Nov 1 | B2003 | engine dir engines-0.1.52 present; prior version `not_recorded` | filesystem | no published delta spans this boundary |
| — | MAC-STUDIO | none recorded | — | — |
| ongoing | P2005 | power governor dynamic (nvidia-powerd 142–175 W) | driver/platform | probe-box absolute speeds vary by policy; paired quality unaffected |
| 2026-11-01 | all | publication edits to *published* code only (PUBLICATION-NOTES.md); rig runs untouched | repo diff | publication reproducibility only |
| 2026-11-02 | P1005 | GPU swap Tesla P100 16 GB → RTX 3060 12 GB (state S2; driver 580→615, engine 0.1.56, gpu-unlock + 187 W) | hardware/changes/P1005.md CHG-001 | all P1005 speed numbers after 2026-11-02 belong to S2, not the S1 records |
| 2026-11-03 | P1005 | GPU swap back RTX 3060 → Tesla P100 (state S3; driver 615→580, unlock inert) | hardware/changes/P1005.md CHG-002 | P1005 returns to the S1 record band; S2 figures stay valid only for S2 |
| 2026-11-03 | B2003 | RTX 3060 returned from P1005 loan; 2nd 24 GB DDR5-5600 DIMM reinstalled → dual-channel 48 GB | hardware/changes/B2003.md CHG-001 + dmidecode 2026-11-03 + results/b2003-dual-ladder-20261103.md | all pre-2026-11-03 B2003 speed numbers are single-channel; 2026-11-03 express ladder shows prefill gap (~400 vs 865–914 tok/s, serve-profile suspected) — **OPEN ISSUE deferred to next test round**; profile-aware re-benchmark required before any B2003 prefill comparison |
