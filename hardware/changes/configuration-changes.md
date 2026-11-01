# Configuration change log

| date | machine | change | evidence | affects |
|---|---|---|---|---|
| `not_recorded` (before 2026-10) | B2003 | one of two 24 GB DDR5-5600 modules removed → single-channel 24 GB | dmidecode 2026-11-01 (slot empty) + bench notes | all B2003 speed numbers (memory-bandwidth-bound prefill) |
| between Oct 12 and Nov 1 | B2003 | engine dir engines-0.1.52 present; prior version `not_recorded` | filesystem | no published delta spans this boundary |
| — | MAC-STUDIO | none recorded | — | — |
| ongoing | P2005 | power governor dynamic (nvidia-powerd 142–175 W) | driver/platform | probe-box absolute speeds vary by policy; paired quality unaffected |
| 2026-11-01 | all | publication edits to *published* code only (PUBLICATION-NOTES.md); rig runs untouched | repo diff | publication reproducibility only |
