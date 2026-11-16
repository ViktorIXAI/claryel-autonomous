# PUB preflight guard history — tick 206 (2026-11-16, census v14)

Load this after `references/preflight_guards_tick205.md`. One tick, one class of hole: a rate may be
divided by a measured window, and a **count of readings** is the same kind of division — v13's
headroom projection did the second one with a mean it never published.

## 1. A projection stated in READINGS has a sampling cadence in its denominator — publish the cadence or drop the count

At the 2026-11-16 13:37 cut the headroom trend row read: newest generation pid 438502, 8 consecutive
decreasing draws, **1 889 MiB lost over 210 min = −539.7 MiB/h**, the gate's own
`MEM_AVAILABLE_MIN_MIB = 2048` floor at **≈298 min** past the newest draw, and then v13's own
addition: **`about 9 further readings`**. The minutes are a rate over a measured span and are
quotable. The `9` is 298 divided by the run's **mean cadence 30.0 min** — a quantity the cell never
printed. The seven intervals behind that mean are **28, 39, 35, 51, 9, 16, 32 min**: the same 298
minutes is **5 readings** at this run's slowest interval and **33** at its fastest, so `9` was not a
conservative bound but an assumption that the producer runs on a schedule. It does not: readings are
taken by ticks and reports. This is the producer rule already written on this line — *divide by a
MEASURED window, never a nominal count* (the sampler whose "6 s" loop measured 6.17 s and made every
MiB/s read ~10 % high) — appearing one level further down, inside a cell that had the honesty to
label itself a projection.

Rule: any figure that converts a projected time into a number of future draws must print the interval
count, the min–max range and the mean beside it, must state the count as a band whenever those
intervals are not uniform (`MEM_INTERVAL_FLAT_RATIO = 1.5` decides collapse), and must print **no**
count when no positive interval exists. A zero-length gap (two draws sharing a timestamp, a fixture
with one name) may never reach a denominator.

## 2. Band a quantity only if a twin at uniform spacing collapses it back

The non-vacuity control for this class is not another row, it is the *same eight values* at a uniform
30 min cadence: the row must then print one count (`≈9 further draws, a single count being admissible
at this cadence (7 interval(s), 30-30 min, mean 30.0)`) and must not print a band. Without that twin,
a band is just a template — the check proves the width is arithmetic over the cadence. Write the pair
in the same commit that adds the band, and pin both shapes.

## 3. Name the old number inside the new cell when a published figure is being corrected

v14 keeps `v13 divided the minutes by that mean alone and printed the single number 9, which this
run's interval range refutes by 5.7x` **in the cell**. A corrected statistic whose old value only
exists in git history invites the next tick to re-quote it; the refutation travels with the number.

## 4. A figure that arrives through context compaction is not a measurement

This line quoted `13:11, MemAvailable 3 717 MiB, GO` in chat. There is no `preflight-20261116-1311.txt`
and `grep -l mem_available_mib=3717` over all 173 stored readings returns nothing — the value never
existed in any file. The two real readings of that day's afternoon are 13:05 (4 789 MiB) and 13:37
(4 729 MiB). Tick 205 hit the same class with a phantom pending codex leg. Rule: before quoting a
stored value, re-read the file (or re-run the reporter) in the same session; notes that survived
compaction are a claim about what a previous session intended, not a reading.

## 5. Reporter-only changes still owe the replay proof, parsed as pairs

Old bytes at `CENSUS_STAMP = 13` and new bytes at `14` over the same 173 readings at
`--as-of 20261116-1337 --no-transition`: **110 rows in both, 0 removed, 0 added, exactly 1 cell
moved**, gate sha16 `dd2f0e4fa0255fa5` identical. The line diff alone would have shown +3/−2 and said
nothing about whether a verdict moved; the (label → value) parse is what makes "no rule moved" a
checked claim (tick 204's lesson, applied a fourth time).
