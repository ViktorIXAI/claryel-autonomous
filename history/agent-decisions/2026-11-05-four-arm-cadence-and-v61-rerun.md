# 2026-11-05 — four-arm cadence, and the bank v6.1 re-run

Operator rule (chat, 2026-11-05 23:15 Europe/Rome), in effect:
the task bank keeps being re-specified and clarified, so the comparison against the
un-assisted models has to be re-measured on a cadence — **every five contour stamps** run
the joint four arms: contour / Grok / ChatGPT (codex) / bare basalt without harness. If the
tasks are worded fairly, the raw arms must improve too; if they do not, the bank is the
problem, not the model.

Cadence point: after 0.0.2.25. Measured evidence: 0.0.2.25 = 56/71 (`full-225/`), which is
not a regression, and 0.0.2.28 = 61/71 (`full-228/`) carries 0.0.2.25's code plus 2.26-2.28.
So the contour arm of this four-arm uses **0.0.2.28**, the newest measured non-regressing
stamp; 2.26/2.27 are attributed inside it by ledger events, not by claim.

Scope of this run (bank v6.1, published `benchmarks/hard/bank-hard-v6.json`, sha16
`9ec86dfca4a6f85f`): J-ex6-03 carries its data table again and J-ex6-06 matches its
hand-verified reference. The v6-era external numbers (grok 59/71, codex 49/71, basalt bare
49/71) were measured on the pre-fix prompts, so they stay in `FOUR-ARM-SCOREBOARD.md` as the
v6 row and are **not** comparable cell-by-cell with the v6.1 arms.

Operator GO also unholds the external arms on v6.1 that `BANK-V61.md` had put on hold.

Transport correction taken from our own finding S3 (the v6 grok arm ran through a file
transport that left file tools reachable and leaked a path into one answer): the v6.1 grok
arm runs with **toolsets disabled and the prompt inline**, so the transport cannot touch the
workspace. Codex arm: `codex exec -s read-only`, reasoning xhigh, model gpt-6.1-sol. Bare
basalt: direct HTTP to the local serve, temperature 0.7, seed 1000+rep, no contour, no
fixers, one transport retry, loop-D tasks skipped and scored N/A.

Sequencing: the two external arms started immediately; the two local arms (contour 0.0.2.28
and bare basalt) wait for the contour 0.0.2.29 arm that the other line is running on the
same serve, so this comparison is measured on an otherwise idle endpoint. Contour 0.0.2.28
also owes a repeat on an idle endpoint (its first arm ran under contention, wall 1020 s).
