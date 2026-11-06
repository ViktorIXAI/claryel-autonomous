# Where the margin lives: contract-sensitive categories vs open-ended cells

Generator: `scripts/category_split_v6.py` — frozen scorer over published answer bytes, category E taken
from the docker `E-EXEC.json` cache for every arm alike. Contour leg: 0.0.2.29 rep0 on bank v6.1
(`full-229/ledger-c229full.jsonl`). Raw legs: published four-arm rep0 answers. This exists because a
single total hides where a win actually comes from, and the independent review asked exactly that.

```
cells = F/H/K (15) + other single-shot (56)

basalt  FHK   contour 14/15 vs arm  6/15  W08 L00 p=0.008
        other contour 49/56 vs arm 50/56  W03 L04 p=1.000
codex   FHK   contour 14/15 vs arm  1/15  W13 L00 p=0.000
        other contour 49/56 vs arm 49/56  W03 L03 p=1.000
grok    FHK   contour 14/15 vs arm  6/15  W08 L00 p=0.008
        other contour 49/56 vs arm 48/56  W04 L03 p=1.000
```

## Reading

- On the **15 contract-sensitive cells** (F diagnostic JSON, H safety evidence/claims, K exact field
  lines and enums) the contour beats every arm and loses nothing: 14 vs 6 bare basalt (p=0.008),
  14 vs 6 Grok (p=0.008), 14 vs 1 ChatGPT (13 wins / 0 losses, exact one-sided p≈0.0002).
- On the **remaining 56 cells** the contour is at parity, not ahead: 49 vs 50 bare basalt, 49 vs 49
  ChatGPT, 49 vs 48 Grok — every paired test there is p=1.00.
- Defensible claim: **on this bank a 24 GB local contoured model beats ChatGPT, Grok and the same
  uncontoured local weights on contract-sensitive tasks, and ties them on open-ended ones.** Anyone
  writing "beats cloud models at reasoning" is overstating this evidence.
- Mechanism is measured, not assumed: `ABLATION-RAW-FIXERS.md` shows the contour's deterministic
  repairer adds 0 cells to raw answers, and every cloud failure in F/H/K is content-side (missing or
  wrong required fields/enums, e.g. `value:EXCLUDES_TAXES`, `next`, `avoid`), cell by cell in
  `AUDIT-FHK-60.md` with the scorer's own reason strings.
- Design honesty: this bank deliberately rewards exact-contract compliance, which is what the contour
  machinery targets (verify, then re-decide until the contract holds). Whether that transfers to
  open-ended work is answered by the 56-cell parity column: not demonstrated yet.
