# What bank v6.1 did to the four arms

Same contour stamp (0.0.2.28) re-run on bank v6.1 against the v6-era arm, plus the three raw arms
on both banks. Numbers across bank hashes are trend comparisons, never cell-for-cell identity.

| arm | v6 bank (`f52acbd1...`) | v6.1 bank (`9ec86dfc...` ws `f4553aab...`) | delta |
|---|---|---|---|
| contour 0.0.2.28 | 61/71 | **61/71** | 0 |
| bare basalt | 49/71 | **56/71** | +7 |
| ChatGPT / codex (xhigh) | 49/71 | **50/71** | +1 |
| Grok 4.7 | 59/71 | **54/71** | -5 |
| loop-D (contour only) | 5/6 | 5/6 | 0 |

The contour re-pair (same stamp, bank v6 -> v6.1) shows the bank fix landing exactly where the
defect was: J 3/7 -> 5/7, the two bank-defective cells `J-ex6-03` and `J-ex6-06` flip to pass;
unrelated noise moved the other way in `A-ex6-07` (field-set resample) and `H-ex6-04`
(`requires_missing:история изменений сервера`). 2 wins / 2 losses / 73 ties, exact sign test p=1.00.

Reading of the operator's test: clearer wording did lift the unassisted models, but unevenly —
the local bare model gained the most (+7, mainly J and B), ChatGPT +1, and Grok lost 5. Grok's
drop cannot be attributed to the bank: a bank clarification is neutral-to-positive for every
model. It is a one-rep draw, and the raw runners did not record which model build answered.

## Measurement-validity gap found here

`raw_v6.py` wrote no model identity into its answer rows (keys: task/rep/cat/answer/finish/
seconds/arm/mode). So any raw-arm score change between bank versions is ambiguous: bank wording,
model update, or sampling. Fixed in this commit: the runner is now published as `scripts/raw_v6.py`
and every row carries `model`, `cli` (transport version) and `bank_sha16`. Re-run the affected arm
once with the new runner to make the Grok line interpretable.

## Standing scoreboard on v6.1 (71 single-shot cells, one rep)

| arm | strict /71 | wins/losses vs contour | p |
|---|---|---|---|
| contour 0.0.2.28 | **61** | - | - |
| bare basalt | 56 | 11/6 | 0.33 |
| Grok 4.7 | 54 | 11/4 | 0.12 |
| ChatGPT / codex | 50 | 15/4 | **0.019** |

Against the strongest raw arm the contour lead is +5 on one rep (not significant); against
ChatGPT it is +11 (p=0.019). The contour arm keeps loop-D 5/6, which no raw arm can attempt in a
single-shot chat. Next cadence point is contour 0.0.2.30 (every 5 stamps), re-run all four arms.
