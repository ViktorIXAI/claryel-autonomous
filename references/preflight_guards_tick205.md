# PUB preflight guard history — tick 205 (2026-11-16, census v13)

Load this after `references/preflight_guards_tick204.md`. One tick, one class of hole: the table
banded every RATE and no STATE.

## 1. Band every threshold the gate enforces, not only the ones that fire

The gate has carried `mem-available-low` at `MEM_AVAILABLE_MIN_MIB = 2048` since the guard work
began, and the producer has printed `mem_available_mib` and `engine_rss_mib` in every reading.
204 ticks of census published bands for four rate ceilings and never once a headroom band, a
distance to the floor, or an RSS difference — because headroom went into prose beside the verdict
("MemAvailable 20 664 of 61 953, GO") and prose cannot be diffed, scoped or trended. What that hid:
at the 16.11 12:49 cut the live engine generation (pid 438502, 6 draws) was losing **653 MiB/h**
with swap in use flat at 65 MiB, while the generation retired at 10:06 (pid 175316) ran with
16 062-16 839 MiB swapped out and 17 675-21 441 MiB available. A `RESTART: STATE TRANSITION` row
now prints it: swap in use fell 16 774 MiB while MemAvailable fell 12 679 MiB across the same
restart — the two free columns moved in OPPOSITE directions. Rule: when a census adds a rule or
reports a verdict, enumerate the gate's thresholds from the gate source and ask which ones have no
published column. A failure mode that has moved from a rate to a state is invisible to a rate table.

## 2. Related corollary: a rule can stop firing because the substrate vanished, not because it was fixed

The 05:41 (6.91x) and 06:43 (10.69x) swap-ceiling refusals belonged to the old generation; every
window of the new generation prints a swap peak of 0.0 MiB/s with 65 MiB in use. Nothing was
re-armed and no ceiling moved — there was simply nothing left swapped out to page in. Before
crediting a rule for a quiet streak, check whether the quantity the rule watches still exists.

## 3. Impossible fields: report them, exclude them from arithmetic, never average them

`preflight-20261111-0336.txt` carries `engine_rss_mib=58 929 928` against `mem_total_mib=61 953` —
951x the machine, a KiB value inside a MiB column (the same process reads 57 470 MiB two windows
later). Any ratio built on such a delta reads ~1000 % instead of 101 %. Census v13 names the file in
a printed row and drops the value from every delta. Rule: before a numeric field enters a delta,
test it against a physical bound in the same reading (`mem_total_mib`, `swap_total_mib`).

## 4. Trend rows: minimum draw count, explicit label, and do NOT arm from a projection

The v13 trend row needs >=3 consecutive monotone draws to say anything (2 points is a line, not a
trend), >=6 to name a per-hour slope, and its projection cell carries the words
`PROJECTION (not a promise, one generation, n=6)` inside the printed value. A rising series must
print the slope and the interval and say nothing else. Nothing was armed from it: a headroom fall
that ends below the floor is a refusal by the rule already in force, which is exactly the difference
between publishing evidence and making a promise. When the sample is two manual draws 9 minutes
apart, say so — the minutes figure is the one to read, the "how many further readings" figure is
cadence-dependent.

## 5. Attribution: charge the sampled process only for what it demonstrably took

The change-since-first-draw row computes `d_rss / d_avail` and prints `UNATTRIBUTED` unless the
sampled engine's own RSS growth explains >= 80 % of the headroom fall (101 % at the 12:49 cut,
residual 9 MiB). Without that guard every memory story on this line blames the engine by default,
which is unfalsifiable.

## 6. Reporter-only changes: the replay proof is now three times the same shape

Restore the old bytes inside `scripts/` (the census resolves its gate relative to its own dir),
run old and new in **separate symlink directories** over the same corpus at the same
`--as-of <cut> --no-transition`, `sha256sum`-verify the restored blob against
`git rev-parse HEAD:<path>` before running, and diff **parsed (label -> value) pairs, not lines**
(a cell that grew is invisible to a line count). v13 at the 1255 cut: old 100 rows, new 110,
**cells moved 0, rows removed 0, rows added 10**, gate sha16 `dd2f0e4fa0255fa5` identical in both
runs, only the stamp sentence moved. Same result shape as v11 (32 added), v12 (8 changed cells, all
band/denominator). Keep the `--check` identity untouched: a reporter change must keep the window
identity, so old and new run at a cut no committed table was generated at, and `--check` is run
afterwards against the newly generated table.

## 7. Do not honour a carry-over operational note without reading the artifact

The previous run's compacted notes asked for a `gpqa-diamond` codex relaunch ("two transport
timeouts, pending"). The artifact says otherwise: `~/pub-bench/cloud-gpqa-codex.log` ends
`codex done: ok=198 bad=0 wall 3553 s` then `cloud gpqa codex exit=0`, and
`~/pub-bench/gpqa-diamond/pub-codex.jsonl` holds 198/198 rows, published at 174/198 = 87.9 %. The
"pending relaunch" was a memory of the 10:07/11:24/12:04 launch attempts of *other* sets. Launching
it would have been a duplicate leg on a set that already has its cell, on a subscription with no
spare window. Rule: a note about unfinished work is a hypothesis; the arm's log, row count and
published cell are the data. Check the log tail and `git status`/unit list before honouring it.
