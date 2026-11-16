#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for `scripts/pub_preflight_census.py` (added 2026-11-14).

The census re-judges every stored endpoint reading with the CURRENT gate and derives the
swap-peak band plus the pre-registered arming counter. Stored readings live OUTSIDE the repo
(the producer command is untracked, like every connection seam on this line), so the census
itself cannot run in CI — THIS test runs it over synthetic readings instead, and it is the only
thing standing between the band numbers and a hand-typed table.

What it pins:

  1. the census takes the gate's RETURN CODE per file (GO / NO-GO / input gap) and the counts it
     prints are the arithmetic of those return codes, never a restatement of a tick note;
  2. the swap-peak band is computed on the **swap-mean rule**, not on the verdict column. The
     fixture set contains a reading that NO-GOs on the GPU-mean rule with a quiet swap window and
     a peak of 0.0: it must land in the PASSING group, so it cannot become the failing-group
     minimum. That is exactly the misreading a hand census makes, and the tool prints the wrong
     denominator (min peak across gate-NO-GO windows) beside the right one so the trap is named;
  3. a reading the gate refuses to judge (an input gap, e.g. a NaN engine_pcpu) is in neither band
     group even when it carries a big parseable peak: it is counted in the coverage census and in
     the excluded count, with zero band credit;
  4. a NaN peak is zero credit: the gate itself answers INPUT GAP on it, so it leaves the band,
     the coverage census marks it, and the arming counter — which counts only gate-GO windows
     carrying a PARSEABLE peak — does not move;
  5. the band is conditional, not echoed: flipping one swap counter in a GO fixture moves that
     file into the failing group and moves BOTH group extremes. (The flip also raises that file's
     peak, because the gate itself answers INPUT GAP when a window peak sits below the window mean
     — measured live on the fixture: peak 5.0 against mean 25.0 is refused as a producer bug, which
     is the right answer and is why a naive flip would test nothing.)
  6. fail-closed census gaps: a missing readings dir, a file whose name is not
     preflight-YYYYMMDD-HHMM.txt, and an --as-of bound in the wrong format all exit 1;
  7. `--check` is byte-exact against the committed table, and editing a stored reading inside the
     window makes it drift — stored readings are immutable evidence;
  8. the ceilings printed in the table are read out of the gate source at run time, so the census
     can never print a number the gate does not enforce, AND each number sits next to the scope it
     governs: the device ceiling is scope-dependent (50.0 for `blk_scope=whole-disk`, 100.0 only for
     readings carrying no scope key). Non-vacuity runs the REAL gate on one device number (60.0)
     three ways - scoped (NO-GO), unscoped (GO), unknown scope value (input gap) - which is the only
     control that separates a correct ceiling table from one that mislabels the number;
  9. the table is deterministic over a frozen `--as-of` window, and that bound really excludes
     later readings;
  10. the engine swap FOOTPRINT census (added 2026-11-14, tick 159): the footprint is a STATE key and
     a huge one changes no verdict (no ceiling is registered yet), a NaN footprint is an input gap,
     the coverage/arming cells count only what they name, the page-cache share divides by the
     reading's own `swap_used_mib`, and stripping the keys from identical fixtures moves no verdict
     and no peak-band cell — the non-retroactivity proof for a key no stored reading carries.
  11. the swap-peak band STATE is computed from the two group extremes, never asserted by a fixed
     sentence (census v2, 2026-11-14 23:13). v1 always printed "Band: nothing between X and Y"; when
     one live GO window carried an 111.4 MiB/s in-window peak against a 107.0 mean-failing minimum,
     the interval it described was empty and the table said nothing about that. SEPARATED, CROSSED
     and NO-DATA must be distinguishable on fixtures, a crossed corpus must NOT print the separated
     sentence, and an empty group prints `n/a`, never `None`.
  12. the FOOTPRINT group separation is computed too, with its sample size printed: SEPARATED,
      OVERLAPPING, INVERTED or NO-DATA. Two medians printed side by side read to a human as a band a
      ceiling could be drawn from, and at n=2/2 (the live coverage) nothing supports one.
  13. a frozen `--as-of` snapshot stays re-derivable after the corpus GROWS (census v3). The committed
      table used to print the corpus-wide count of reading files inside its window-identity sentence,
      so one reading taken after the snapshot made `--check` of untouched bytes report drift (measured
      2026-11-15 01:00: `123 stored readings` -> `124 stored readings`, no verdict moved). The header
      now names only the window count, the corpus count lives on stdout, and an edited reading INSIDE
      the window still reddens the check.
  14. the drift EVIDENCE is complete (tick 166, 2026-11-15). `--check` printed at most 40 diff lines
      with no total and no truncation note; on the real corpus at the 03:08 window that hid 10 of the
      30 changed table lines — the whole engine-footprint section and the band prose — while the exit
      code stayed right. The count is printed before the body, every changed line must appear, and the
      print bound is a named constant far above one table's size.
  15. the FOOTPRINT CEILING DRY-RUN (census v4, added 2026-11-15, tick 174) is computed at every
      reading, because the pre-registered arming rule will one day have to answer "at the lowest
      ceiling that spares every launchable window, how many stored windows actually fire?" — and that
      answer must never be a hand-composed sentence. Measured live at the 08:57 reading: the
      launchable footprint maximum (8 520 MiB) grew above the refused maximum (6 957 MiB), so the
      only admissible ceiling fires on NOTHING. Pinned: the firing case (SEPARATED fixture, ceiling >
      1000 fires on 1 of 1 refused), the inert cases (INVERTED and OVERLAPPING fixtures, 0 refused
      windows fire), the n/a case (no footprint key present, never 0-of-0 arithmetic that would read
      as measured inertness), and the non-vacuity pair: the SAME refused window with the launchable
      footprint moved 1000 -> 20000 flips the state word FIRING-AT-MINIMUM-CEILING ->
      INERT-AT-MINIMUM-CEILING. The dry-run registers no ceiling, gates nothing and changes no
      verdict: it is a census of what a future ceiling WOULD do.
  16. the DAY rule band (census v5, added 2026-11-15, tick 192): the day's GO/refusal swap-ratio
      bands, the refusal MEDIAN, refusals decided by a rule other than swap, the dead zone with its
      EMPTY/POPULATED/NO-DATA state word, the longest consecutive-refusal run, the readings since the
      day's last GO, and the age of the launchable-footprint maximum are printed from the SAME
      per-file gate returncodes the verdict census uses. Reason measured live: those figures existed
      only in tick prose, and prose is re-typed rather than recomputed — two consecutive ticks quoted
      a 4.22x refusal median while the same parser gives 3.985x at the 30th reading and 3.745x at the
      31st. Pinned: the split of the refusal column (a GPU-contention refusal at 0.00x swap is NAMED
      and kept out of the swap band), a run of input gaps never reported as a refusal run, an empty
      GO group printing n/a instead of a nonsense band, the footprint rows printing n/a when no
      footprint key exists, and two non-vacuity controls — a refusal moved INTO the dead zone flips
      EMPTY -> POPULATED, and a GO draw moved above the ceiling moves the median 8.000 -> 4.750 and
      erases the dead-zone bounds.
"""
import difflib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
TOOL = os.path.join(ROOT, "scripts", "pub_preflight_census.py")
GATE = os.path.join(ROOT, "scripts", "pub_preflight.py")
# The table-shape number is READ out of the tool, never typed here. Two earlier revisions pinned
# the literal "…-v8" and went red on every honest shape bump; the shape is now mechanical in the
# tool (its preserved-shape sentence is generated from this constant), so the test must follow the
# constant rather than the news.
_m = re.search(r"^CENSUS_STAMP = (\d+)", open(TOOL, encoding="utf-8").read(), re.M)
STAMP_N = int(_m.group(1)) if _m else 0
STAMP_NAME = ("pub-preflight-census-v%d" % STAMP_N) if _m else "CENSUS STAMP NOT DECLARED"

CHECKS = 0
FAILED = []


def check(cond, label):
    global CHECKS
    CHECKS += 1
    if not cond:
        FAILED.append(label)


# A reading the current gate answers GO on (the 2026-11-14 17:51 live reading, simplified).
HEALTHY = {
    "mem_total_mib": "61953",
    "mem_available_mib": "20278",
    "swap_total_mib": "65535",
    "swap_free_mib": "57507",
    "swap_used_mib": "8028",
    "engine_state": "S",
    "engine_pcpu": "9.6",
    "engine_rss_mib": "57374",
    "gpu_util_pct": "0",
    "gpu_power_w": "27.42",
    "load1": "9.07",
    "health_code": "200",
    "foreign_legs": "0",
    "health_loaded": "true",
    "engine_serve_procs": "1",
    "swap_in_mib_per_s": "0.1",
    "swap_out_mib_per_s": "0.0",
    "swap_total_peak_mib_per_s": "5.0",
    "gpu_util_mean_pct": "0.0",
    "gpu_util_peak_pct": "0",
    "blk_read_mib_per_s": "0.1",
    "blk_top_reader": "basalt",
    "blk_scope": "whole-disk",
}

DAY = "20300101"
F1 = "preflight-%s-0001.txt" % DAY   # GO, quiet swap, parseable peak 5.0
F2 = "preflight-%s-0002.txt" % DAY   # swap-churn NO-GO, peak 300.0
F3 = "preflight-%s-0003.txt" % DAY   # GPU-contention NO-GO, swap quiet, peak 0.0  -> PASSING group
F4 = "preflight-%s-0004.txt" % DAY   # INPUT GAP (NaN engine_pcpu), peak 400.0     -> no band credit
F5 = "preflight-%s-0005.txt" % DAY   # INPUT GAP (NaN peak)                        -> n_nan

FIXTURES = {
    F1: {},
    F2: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
         "swap_total_peak_mib_per_s": "300.0"},
    F3: {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0", "gpu_util_peak_pct": "100",
         "gpu_power_w": "128.0",
         "swap_in_mib_per_s": "0.0", "swap_out_mib_per_s": "0.0",
         "swap_total_peak_mib_per_s": "0.0"},
    F4: {"engine_pcpu": "NaN", "swap_total_peak_mib_per_s": "400.0"},
    F5: {"swap_total_peak_mib_per_s": "NaN"},
}


def write_fixtures(d, fixtures=None):
    for name, over in (fixtures if fixtures is not None else FIXTURES).items():
        vals = dict(HEALTHY)
        vals.update(over)
        # an override value of None deletes the key: how the unscoped/old-scale reading is built
        vals = {k: v for k, v in vals.items() if v is not None}
        with open(os.path.join(d, name), "w", encoding="utf-8") as fh:
            for k, v in vals.items():
                fh.write("%s=%s\n" % (k, v))


def run(args):
    p = subprocess.run([sys.executable, TOOL] + args, cwd=ROOT,
                       capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def cell(md, label):
    m = re.search(r"^\| %s \| (.*?) \|$" % re.escape(label), md, re.M)
    return m.group(1) if m else None


def int_cell(md, label):
    v = cell(md, label)
    if v is None:
        return None
    m = re.match(r"^(-?\d+)", v.strip())
    return int(m.group(1)) if m else None


def main():
    with tempfile.TemporaryDirectory() as tmp:
        write_fixtures(tmp)
        rc, out = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc == 0, "census over fixtures exits 0 (rc=%s: %s)" % (rc, out[:400]))

        # 1. verdict arithmetic (1 GO, 2 NO-GO, 2 input gaps)
        check(int_cell(out, "gate verdict GO") == 1,
              "GO count is 1, got %r" % cell(out, "gate verdict GO"))
        check(int_cell(out, "gate verdict NO-GO") == 2,
              "NO-GO count is 2, got %r" % cell(out, "gate verdict NO-GO"))
        check(int_cell(out, "gate verdict input gap") == 2,
              "input-gap count is 2, got %r" % cell(out, "gate verdict input gap"))

        # 2. the band is on the swap-mean rule, not on the verdict column
        check(int_cell(out, "swap-mean-passing windows with a peak") == 2,
              "the GPU-contention fixture stays in the swap-mean-PASSING group (expected 2), got %r"
              % cell(out, "swap-mean-passing windows with a peak"))
        check(int_cell(out, "swap-mean-failing windows with a peak") == 1,
              "only the swap-churn fixture fails the mean rule (expected 1), got %r"
              % cell(out, "swap-mean-failing windows with a peak"))
        check(cell(out, "highest peak inside a swap-mean-PASSING window") == "5.0 MiB/s",
              "passing-group max peak is 5.0, got %r"
              % cell(out, "highest peak inside a swap-mean-PASSING window"))
        check(cell(out, "lowest peak inside a swap-mean-FAILING window") == "300.0 MiB/s",
              "failing-group min peak is 300.0, got %r"
              % cell(out, "lowest peak inside a swap-mean-FAILING window"))
        check("lowest peak in a gate-`NO-GO` window is 0.0 MiB/s" in out,
              "the trap denominator (min peak across gate-NO-GO windows = 0.0) is printed explicitly")

        # 3+4. coverage census: carried / NaN / parseable, and the input-gap peak excluded
        check(cell(out, "readings carrying the swap-peak key") == "5 (NaN 1, parseable 4)",
              "coverage cell names carried / NaN / parseable, got %r"
              % cell(out, "readings carrying the swap-peak key"))
        bandset = cell(out, "...of those, gate-JUDGED readings with a parseable peak (the band's set)")
        check(bool(bandset) and bandset.startswith("3 (the other 1 sit in readings the gate refuses"),
              "band set is 3 and the input-gap 400.0 peak is named as excluded, got %r" % bandset)
        m = re.search(r"\| arming counter \(launchable windows carrying the peak\) \| (\d+) of (\d+) \|", out)
        check(bool(m), "arming counter cell present")
        if m:
            check(m.group(1) == "1",
                  "arming counter counts only GO windows with a PARSEABLE peak, got %s" % m.group(1))
            check(int(m.group(2)) >= 2, "arming threshold printed and non-trivial, got %s" % m.group(2))

        # 5. non-vacuity: one flipped swap counter moves the verdict AND the band
        flipped = dict(FIXTURES)
        flipped[F1] = {"swap_in_mib_per_s": "25.0", "swap_total_peak_mib_per_s": "30.0"}
        with tempfile.TemporaryDirectory() as tmp2:
            write_fixtures(tmp2, flipped)
            rc2, out2 = run(["--dir", tmp2, "--as-of", "%s-0005" % DAY])
            check(rc2 == 0, "flipped census exits 0")
            check(int_cell(out2, "gate verdict GO") == 0,
                  "the flipped fixture is NO-GO now, got %r" % cell(out2, "gate verdict GO"))
            check(cell(out2, "lowest peak inside a swap-mean-FAILING window") == "30.0 MiB/s",
                  "the failing-group minimum follows the flipped file (30.0), got %r"
                  % cell(out2, "lowest peak inside a swap-mean-FAILING window"))
            check(cell(out2, "highest peak inside a swap-mean-PASSING window") == "0.0 MiB/s",
                  "the passing-group maximum follows the flip too (0.0), got %r"
                  % cell(out2, "highest peak inside a swap-mean-PASSING window"))

        # 6. fail-closed census gaps
        rc3, _ = run(["--dir", os.path.join(tmp, "no-such-dir")])
        check(rc3 == 1, "missing readings dir exits 1, got %s" % rc3)
        with open(os.path.join(tmp, "preflight-bogus.txt"), "w", encoding="utf-8") as fh:
            fh.write("mem_total_mib=1\n")
        rc4, out4 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc4 == 1, "an unreadable reading name exits 1, got %s" % rc4)
        check("preflight-bogus.txt" in out4, "the name gap names the file")
        os.remove(os.path.join(tmp, "preflight-bogus.txt"))
        rc5, _ = run(["--dir", tmp, "--as-of", "not-a-stamp"])
        check(rc5 == 1, "a malformed --as-of exits 1, got %s" % rc5)

        # 7. --check is byte-exact; a stored reading edited inside the window drifts
        md_path = os.path.join(tmp, "CENSUS.md")
        rc6, _ = run(["--dir", tmp, "--as-of", "%s-0005" % DAY, "--markdown", md_path])
        check(rc6 == 0 and os.path.exists(md_path), "--markdown writes the table")
        rc7, out7 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY, "--check", md_path])
        check(rc7 == 0, "--check matches a freshly written table, got %s: %s" % (rc7, out7[:200]))
        with tempfile.TemporaryDirectory() as tmp3:
            for name in FIXTURES:
                shutil.copyfile(os.path.join(tmp, name), os.path.join(tmp3, name))
            with open(os.path.join(tmp3, F2), "a", encoding="utf-8") as fh:
                # the gate keeps the LAST token per key, so this rewrites F2's whole swap window:
                # mean 160.0 -> 0.2, i.e. the file moves NO-GO -> GO and its 300.0 peak moves
                # groups. A census that only counted files (instead of re-running the gate) would
                # print the old table and call it verified.
                fh.write("swap_in_mib_per_s=0.2\nswap_out_mib_per_s=0.0\n")
            rc8, out8 = run(["--dir", tmp3, "--as-of", "%s-0005" % DAY, "--check", md_path])
            check(rc8 == 1, "editing a stored reading inside the window drifts --check, got %s" % rc8)
            check("CENSUS DRIFT" in out8, "the drift mode names itself")

        # 8. ceilings come out of the gate source, so the table cannot disagree with the rule
        gate_src = open(GATE, encoding="utf-8").read()
        for const in ("SWAP_RATE_MAX_MIB_S", "GPU_UTIL_MAX_MEAN_PCT",
                      "BLK_READ_MAX_MIB_S", "BLK_READ_MAX_MIB_S_WHOLE"):
            m = re.search(r"^%s\s*=\s*([0-9.]+)" % const, gate_src, re.M)
            check(bool(m), "the gate defines %s" % const)
            if m:
                check("`%s = %s`" % (const, m.group(1)) in out,
                      "the census prints the gate's own %s = %s" % (const, m.group(1)))
        # 8b. the DEVICE ceiling is scope-dependent, and printing the number is not enough: the
        #     first version of this table printed only the 100.0 and labelled it "whole-disk
        #     scope", which contradicted its own verdict column (the gate refused a whole-disk
        #     56.2 MiB/s reading). Each number must sit next to the scope it governs.
        flat = " ".join(out.split())
        check("BLK_READ_MAX_MIB_S_WHOLE = 50.0` applies to every reading carrying "
              "`blk_scope=whole-disk" in flat,
              "the whole-disk ceiling is printed WITH its scope")
        check("BLK_READ_MAX_MIB_S = 100.0` applies only to readings with NO scope key" in flat,
              "the old inflated-scale ceiling is printed WITH its scope")
        check("unknown scope" in flat, "an unknown scope value is named as its own class")
        with tempfile.TemporaryDirectory() as tmp2:
            rows = {
                "preflight-%s-0001.txt" % DAY: {"blk_read_mib_per_s": "60.0"},
                "preflight-%s-0002.txt" % DAY: {"blk_read_mib_per_s": "60.0",
                                                "blk_scope": None},
                "preflight-%s-0003.txt" % DAY: {"blk_read_mib_per_s": "60.0",
                                                "blk_scope": "diskstats-sum"},
            }
            write_fixtures(tmp2, rows)
            rc2a, out2a = run(["--dir", tmp2, "--as-of", "%s-0003" % DAY])
            check(rc2a == 0, "census over the scope-control fixtures exits 0 (rc=%s)" % rc2a)
            check(int_cell(out2a, "gate verdict NO-GO") == 1,
                  "the same device number 60.0 IS refused when blk_scope=whole-disk "
                  "(ceiling 50.0), got NO-GO=%r" % cell(out2a, "gate verdict NO-GO"))
            check(int_cell(out2a, "gate verdict GO") == 1,
                  "the same 60.0 passes with NO scope key (ceiling 100.0) - the two scales "
                  "give different verdicts, so one printed number cannot cover both")
            check(int_cell(out2a, "gate verdict input gap") == 1,
                  "an unrecognised blk_scope value is never judged by borrowing a ceiling")
            sc = cell(out2a, "device scope of the readings in this window") or ""
            check(sc.startswith("1 whole-disk (`50.0` ceiling) / 1 unscoped (`100.0` ceiling) "
                                "/ 1 unknown scope"),
                  "the census counts readings per device scale, got %r" % sc)

        # 9. determinism over a frozen window, and the bound really windows
        rc9, out9 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        rc10, out10 = run(["--dir", tmp, "--as-of", "%s-0005" % DAY])
        check(rc9 == 0 and out9 == out10, "two runs over the same window are byte-identical")
        rc11, out11 = run(["--dir", tmp, "--as-of", "%s-0004" % DAY])
        check(rc11 == 0, "an earlier --as-of bound still exits 0")
        if rc11 == 0:
            check(int_cell(out11, "gate verdict input gap") == 1,
                  "the bound excludes the 0005 reading (its NaN peak), got %r"
                  % cell(out11, "gate verdict input gap"))

        # 10. the engine swap FOOTPRINT census (added 2026-11-14, tick 159): a STATE key beside the
        # rate rules, because a 6 s rate cannot see a state. Measured on the box the same evening:
        # three back-to-back 5 s windows took 320 MiB / 0 / 0 of swap-in while the engine's VmSwap
        # grew 5.22 -> 5.72 GiB and 35 359 of 35 361 major faults belonged to that one pid. What this
        # case pins: (a) a huge footprint changes NO verdict (no ceiling is registered — the same
        # pre-armed rule as the peak, 30 launchable windows carrying the statistic), (b) a NaN
        # footprint is an input gap (the /proc EAGAIN class that already owns engine_pcpu), (c) the
        # coverage and arming cells count what they name, (d) the page-cache share is computed from
        # the used column, not from a hand-typed number, and (e) adding the keys to every fixture
        # moves NO verdict and NO peak-band cell, which is the non-retroactivity proof for a key the
        # 118 stored readings never carried.
        G1 = "preflight-%s-0011.txt" % DAY   # GO with an absurd footprint: reported, never gated
        G2 = "preflight-%s-0012.txt" % DAY   # swap-churn NO-GO carrying a footprint
        G3 = "preflight-%s-0013.txt" % DAY   # INPUT GAP: NaN footprint
        G4 = "preflight-%s-0014.txt" % DAY   # GO with a modest footprint
        FP_FIX = {
            G1: {"engine_vmswap_mib": "30000", "swap_cached_mib": "500"},
            G2: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                 "swap_total_peak_mib_per_s": "300.0",
                 "engine_vmswap_mib": "12000", "swap_cached_mib": "8000"},
            G3: {"engine_vmswap_mib": "NaN", "swap_cached_mib": "500",
                 # the NaN peak keeps this file an input gap in the key-stripped control too, so
                 # the (e) comparison below compares like with like
                 "swap_total_peak_mib_per_s": "NaN"},
            G4: {"engine_vmswap_mib": "6000", "swap_cached_mib": "200"},
        }
        NOFP_FIX = {k: {kk: vv for kk, vv in v.items()
                        if kk not in ("engine_vmswap_mib", "swap_cached_mib")}
                    for k, v in FP_FIX.items()}
        d3 = tempfile.mkdtemp(prefix="pub-census-fp-")
        try:
            write_fixtures(d3, FP_FIX)
            rc12, out12 = run(["--dir", d3, "--as-of", "%s-0014" % DAY])
            check(rc12 == 0, "the footprint census runs green, got %r" % out12[-400:])
            check(int_cell(out12, "gate verdict GO") == 2,
                  "a 30 GiB engine footprint must NOT flip the verdict (no footprint ceiling "
                  "exists), got %r" % cell(out12, "gate verdict GO"))
            check(int_cell(out12, "gate verdict NO-GO") == 1,
                  "the swap-churn reading still NO-GOs, got %r" % cell(out12, "gate verdict NO-GO"))
            check(int_cell(out12, "gate verdict input gap") == 1,
                  "a NaN engine footprint is an input gap, never healthy, got %r"
                  % cell(out12, "gate verdict input gap"))
            fc = cell(out12, "readings carrying `engine_vmswap_mib`") or ""
            check(fc == "4 (NaN 1, parseable 3)",
                  "the footprint coverage cell counts key-present, NaN and parseable separately, "
                  "got %r" % fc)
            fgo = cell(out12, "footprint on gate-GO windows (launchable)") or ""
            check(fgo == "2 (median 18000 MiB, max 30000 MiB)",
                  "the footprint arming census counts only launchable windows and reports the "
                  "median of the two (18000 is the median of 6000/30000, never their mean), got %r"
                  % fgo)
            fnogo = cell(out12, "footprint on gate-NO-GO windows") or ""
            check(fnogo == "1 (median 12000 MiB, min 12000 MiB)",
                  "the NO-GO footprint group is reported separately, got %r" % fnogo)
            sh = cell(out12, "page-cache share of swap in use (`swap_cached_mib` / used)") or ""
            check(sh.startswith("4 readings, median 6.2 percent, max 99.7 percent"),
                  "the page-cache share divides by the used column of the SAME reading "
                  "(8000/8028 = 99.7 percent, 500/8028 = 6.2 percent), got %r" % sh)
            armb = cell(out12, "footprint arming counter (launchable windows carrying it)") or ""
            check(armb == "2 of 30", "the footprint has its own arming counter, got %r" % armb)
            # (e) non-retroactivity: same fixtures, keys stripped — verdicts and the whole peak band
            # must be byte-identical, only the footprint cells may differ.
            d4 = tempfile.mkdtemp(prefix="pub-census-nofp-")
            try:
                write_fixtures(d4, NOFP_FIX)
                rc13, out13 = run(["--dir", d4, "--as-of", "%s-0014" % DAY])
                check(rc13 == 0, "the footprint-free control run is green, got %r" % out13[-300:])
                for lab in ("gate verdict GO", "gate verdict NO-GO", "gate verdict input gap",
                            "readings carrying the swap-peak key",
                            "swap-mean-passing windows with a peak",
                            "swap-mean-failing windows with a peak",
                            "highest peak inside a swap-mean-PASSING window",
                            "lowest peak inside a swap-mean-FAILING window",
                            "arming counter (launchable windows carrying the peak)"):
                    check(cell(out12, lab) == cell(out13, lab),
                          "adding the footprint keys must not move %r: %r vs %r"
                          % (lab, cell(out12, lab), cell(out13, lab)))
                check(cell(out13, "readings carrying `engine_vmswap_mib`")
                      == "0 (NaN 0, parseable 0)",
                      "a corpus with no footprint key reports zero coverage honestly, not a "
                      "healthy-looking blank")
            finally:
                shutil.rmtree(d4, ignore_errors=True)
        finally:
            shutil.rmtree(d3, ignore_errors=True)

        # 11. band STATE is computed, never asserted (measured 2026-11-14 23:13). v1 of the census
        #     printed "Band: nothing between <pass_max> and <fail_min>" unconditionally. One live GO
        #     window then carried an in-window swap peak of 111.4 MiB/s while the lowest
        #     mean-failing peak is 107.0: the two groups overlap, that interval is empty, and the
        #     generated table kept describing it as if it existed — the same defect class as the
        #     scope-mislabelled device ceiling (tick 155). Three states must be distinguishable from
        #     the fixtures, and the crossed corpus must NOT print the separated sentence.
        base_state = cell(out, "swap-peak band state (computed, never asserted)") or ""
        check(base_state.startswith("SEPARATED — no gate-judged window has a peak between 5.0 and "
                                    "300.0 MiB/s"),
              "the base fixture set (launchable max 5.0, mean-fail min 300.0) is SEPARATED, got %r"
              % base_state)
        check("so a ceiling placed in that gap fires only" in " ".join(out.split()),
              "the separated corpus prints the separated CONCLUSION, so that prose branch is live "
              "code and not only the crossed one")
        crossed = dict(FIXTURES)
        crossed[F1] = {"swap_total_peak_mib_per_s": "500.0"}   # GO window, peak above fail_min
        with tempfile.TemporaryDirectory() as tmpx:
            write_fixtures(tmpx, crossed)
            rcx, outx = run(["--dir", tmpx, "--as-of", "%s-0005" % DAY])
            check(rcx == 0, "the crossed-band census run exits 0, got %s" % rcx)
            xs = cell(outx, "swap-peak band state (computed, never asserted)") or ""
            check(xs.startswith("CROSSED — the highest launchable peak 500.0 MiB/s"),
                  "one GO window with a 500.0 peak over a 300.0 mean-fail minimum must read "
                  "CROSSED, got %r" % xs)
            flatx = " ".join(outx.split())
            check("the groups overlap" in flatx,
                  "the crossed state says what a crossed band means for a ceiling")
            check(not re.search(r"Band: nothing between [0-9]", outx),
                  "a crossed corpus must NOT print a numeric 'Band: nothing between X and Y' "
                  "sentence (the v1 defect)")
            check("so a ceiling placed in that gap fires only" not in flatx,
                  "the separated-state conclusion must not be printed for a crossed band")
        # no-data: a corpus whose mean-failing group is empty has no interval to classify at all
        nodata = {k: v for k, v in FIXTURES.items() if k in (F1, F3, F5)}
        with tempfile.TemporaryDirectory() as tmpy:
            write_fixtures(tmpy, nodata)
            rcn, outn = run(["--dir", tmpy, "--as-of", "%s-0005" % DAY])
            check(rcn == 0, "the no-band census run exits 0, got %s" % rcn)
            ns = cell(outn, "swap-peak band state (computed, never asserted)") or ""
            check(ns.startswith("NO-DATA"),
                  "an empty mean-failing group is NO-DATA, not a separation, got %r" % ns)
            check(cell(outn, "lowest peak inside a swap-mean-FAILING window") == "n/a MiB/s",
                  "the failing-group minimum prints n/a, never None, got %r"
                  % cell(outn, "lowest peak inside a swap-mean-FAILING window"))
        # the band state is a property of the swap window, not of the footprint keys
        check(cell(out12, "swap-peak band state (computed, never asserted)")
              == cell(out13, "swap-peak band state (computed, never asserted)"),
              "adding the footprint keys must not move the band state")

        # 12. footprint group separation, also computed. The footprint is a STATE and no ceiling is
        # registered for it, so the risk here is the opposite of the peak risk: two medians printed
        # side by side read as a band to a human. The cell must name the class AND the sample size.
        fs = cell(out12, "footprint group separation (computed, never asserted)") or ""
        check(fs.startswith("OVERLAPPING (launchable 2 window(s) 6000-30000 MiB, refused 1 "
                            "window(s) 12000-12000 MiB; n=2/1"),
              "the footprint groups here overlap (6000-30000 launchable vs 12000 refused) and the "
              "cell must say so with its sample size, got %r" % fs)
        SEP_FIX = {
            "preflight-%s-0021.txt" % DAY: {"engine_vmswap_mib": "1000", "swap_cached_mib": "200"},
            "preflight-%s-0022.txt" % DAY: {"swap_in_mib_per_s": "120.0",
                                            "swap_out_mib_per_s": "40.0",
                                            "swap_total_peak_mib_per_s": "300.0",
                                            "engine_vmswap_mib": "12000", "swap_cached_mib": "8000"},
        }
        with tempfile.TemporaryDirectory() as tmpz:
            write_fixtures(tmpz, SEP_FIX)
            rcs, outs = run(["--dir", tmpz, "--as-of", "%s-0022" % DAY])
            check(rcs == 0, "the separated-footprint census exits 0, got %s" % rcs)
            ss = cell(outs, "footprint group separation (computed, never asserted)") or ""
            check(ss.startswith("SEPARATED (launchable 1 window(s) 1000-1000 MiB, refused 1 "
                                "window(s) 12000-12000 MiB; n=1/1"),
                  "a launchable footprint strictly below the refused one must read SEPARATED, "
                  "got %r" % ss)
            # 12b. the ceiling dry-run on the SAME fixture: a separated corpus is the one case where
            # the pre-registered ceiling (above every launchable footprint) actually fires.
            ds = cell(outs, "footprint ceiling dry-run (computed; it arms NOTHING)") or ""
            check(ds.startswith("ceiling > 1000 MiB fires on 0 of 1 launchable and 1 of 1 refused "
                                "stored windows"),
                  "a separated corpus must report the minimum admissible ceiling AND the refused "
                  "window it fires on, got %r" % ds)
            check(cell(outs, "footprint ceiling state (computed)") == "FIRING-AT-MINIMUM-CEILING",
                  "a ceiling that fires on a refused window while sparing every launchable one is "
                  "FIRING-AT-MINIMUM-CEILING, got %r"
                  % cell(outs, "footprint ceiling state (computed)"))
        INV_FIX = {
            "preflight-%s-0021.txt" % DAY: {"engine_vmswap_mib": "20000", "swap_cached_mib": "200"},
            "preflight-%s-0022.txt" % DAY: {"swap_in_mib_per_s": "120.0",
                                            "swap_out_mib_per_s": "40.0",
                                            "swap_total_peak_mib_per_s": "300.0",
                                            "engine_vmswap_mib": "12000", "swap_cached_mib": "8000"},
        }
        with tempfile.TemporaryDirectory() as tmpw:
            write_fixtures(tmpw, INV_FIX)
            rci, outi = run(["--dir", tmpw, "--as-of", "%s-0022" % DAY])
            check(rci == 0, "the inverted-footprint census exits 0, got %s" % rci)
            isi = cell(outi, "footprint group separation (computed, never asserted)") or ""
            check(isi.startswith("INVERTED (launchable 1 window(s) 20000-20000 MiB, refused 1 "
                                 "window(s) 12000-12000 MiB; n=1/1"),
                  "a launchable footprint strictly ABOVE the refused one must read INVERTED, "
                  "never a band a ceiling could be drawn from, got %r" % isi)
            # 12c. the dry-run must MOVE with the footprint keys on a fixture whose verdicts,
            # separation class and swap windows are otherwise identical to the SEPARATED run above:
            # same refused window (12000), launchable footprint moved 1000 -> 20000, and the state
            # word flips FIRING -> INERT. That pair is the non-vacuity control for the new cells.
            di = cell(outi, "footprint ceiling dry-run (computed; it arms NOTHING)") or ""
            check(di.startswith("ceiling > 20000 MiB fires on 0 of 1 launchable and 0 of 1 refused "
                                "stored windows"),
                  "an inverted corpus must report a ceiling that fires on NOTHING, got %r" % di)
            check(cell(outi, "footprint ceiling state (computed)") == "INERT-AT-MINIMUM-CEILING",
                  "the minimum admissible ceiling firing on no stored window is "
                  "INERT-AT-MINIMUM-CEILING, got %r"
                  % cell(outi, "footprint ceiling state (computed)"))
            check(cell(outs, "footprint ceiling state (computed)")
                  != cell(outi, "footprint ceiling state (computed)"),
                  "the dry-run state cell must be a property of the footprint groups, not a fixed "
                  "sentence: SEPARATED reads FIRING and INVERTED reads INERT on the same refused "
                  "window")
        # the live-shape case (launchable 6000/30000 straddling a refused 12000): overlapping groups
        # are INERT too, because the ceiling is set by the launchable MAXIMUM.
        dlive = cell(out12, "footprint ceiling dry-run (computed; it arms NOTHING)") or ""
        check(dlive.startswith("ceiling > 30000 MiB fires on 0 of 2 launchable and 0 of 1 refused"),
              "an overlapping corpus whose launchable maximum exceeds the refused one must read "
              "as firing on nothing, got %r" % dlive)
        check(cell(out12, "footprint ceiling state (computed)") == "INERT-AT-MINIMUM-CEILING",
              "the launchable-side maximum sets the candidate ceiling, so this shape is inert, got %r"
              % cell(out12, "footprint ceiling state (computed)"))
        # a corpus with no footprint key at all must print n/a, never 0/0 arithmetic
        dnone = cell(out13, "footprint ceiling dry-run (computed; it arms NOTHING)") or ""
        check(dnone.startswith("n/a"),
              "no footprint coverage has no candidate ceiling: n/a, never 0-of-0 arithmetic, got %r"
              % dnone)
        check(cell(out13, "footprint ceiling state (computed)") == "NO-DATA",
              "the dry-run state of a footprint-free corpus is NO-DATA, got %r"
              % cell(out13, "footprint ceiling state (computed)"))
        # a corpus with no footprint key at all must not invent a class
        fs_none = cell(out13, "footprint group separation (computed, never asserted)") or ""
        check(fs_none.startswith("NO-DATA"),
              "no footprint coverage reports NO-DATA, not a separation")

        # 13. a frozen `--as-of` snapshot must stay re-derivable after the CORPUS grows
        #     (census v3, measured 2026-11-15 01:00 on the real bytes). v1/v2 printed the
        #     corpus-wide count of `preflight-*.txt` files inside the window-identity sentence
        #     ("N stored readings, M inside the window"). Taking one reading AFTER a committed
        #     window moved N, so `--check` of an untouched snapshot reported drift: at the
        #     committed window `as-of 2026-11-14 23:47` the line went from `123 stored readings`
        #     to `124 stored readings` while the window count, every verdict and every band cell
        #     stayed identical. A guard that reddens on its own calendar is a guard that stops
        #     being believed, and the tool's own usage note promised that "a committed snapshot is
        #     reproducible while the readings are retained". What this case pins: the header names
        #     ONLY the window count, the corpus count survives on stdout (operator context), and
        #     the immutability rule still bites — an edited stored reading INSIDE the window must
        #     redden the check.
        d5 = tempfile.mkdtemp(prefix="pub-census-frozen-")
        try:
            write_fixtures(d5)                                  # F1..F5, all inside the window
            tbl = os.path.join(d5, "TABLE.md")
            rcw, outw = run(["--dir", d5, "--as-of", "%s-0004" % DAY, "--markdown", tbl])
            check(rcw == 0, "writing a snapshot at a frozen window exits 0, got %r" % outw[-300:])
            rcc, outc = run(["--dir", d5, "--as-of", "%s-0004" % DAY, "--check", tbl])
            check(rcc == 0, "the fresh snapshot checks clean, got %r" % outc[-300:])
            # one reading taken AFTER the frozen bound: outside the window, so the table may not move
            write_fixtures(d5, {"preflight-%s-0006.txt" % DAY: {}})
            rcg, outg = run(["--dir", d5, "--as-of", "%s-0004" % DAY, "--check", tbl])
            check(rcg == 0,
                  "a reading taken after the frozen window must NOT make an untouched snapshot "
                  "drift (the v1/v2 corpus-count defect), got rc=%s %r" % (rcg, outg[-500:]))
            head_w = [l for l in open(tbl, encoding="utf-8").read().splitlines()
                      if l.startswith("Census stamp:")]
            check(len(head_w) == 1 and "4 readings inside the window" in head_w[0],
                  "the header names the WINDOW count and nothing else, got %r" % head_w[:1])
            check("stored readings," not in (head_w[0] if head_w else ""),
                  "the header must print no corpus-wide file count, got %r" % head_w[:1])
            check("6 preflight-*.txt files retained in the corpus" in outg,
                  "stdout still reports the corpus size and labels it as NOT window identity, "
                  "got %r" % outg[:300])
            # tamper control: editing a stored reading INSIDE the frozen window still reddens —
            # stored readings are immutable evidence and this fix must not have weakened that
            write_fixtures(d5, {F2: {}})                         # NO-GO churn -> healthy GO
            rce, oute = run(["--dir", d5, "--as-of", "%s-0004" % DAY, "--check", tbl])
            check(rce == 1 and "CENSUS DRIFT" in oute,
                  "an edited reading inside the window must still drift the check, got rc=%s %r"
                  % (rce, oute[-300:]))
        finally:
            shutil.rmtree(d5, ignore_errors=True)

    # 14. tick 166 (2026-11-15): the `--check` drift EVIDENCE must be complete, not a silent slice.
    #     The print was `list(unified_diff(...))[:40]` with no count and no truncation note. Measured
    #     on the REAL corpus at the 2026-11-15 03:08 window: the drift was 63 diff lines / 30 changed
    #     table lines, and the cap hid the last 10 changed lines — every `engine_vmswap_mib` footprint
    #     row plus the band prose sentence. The exit code stayed correct (1), so the damage is
    #     evidence only, and it is this line's own class: a tick attributing a drift from this output
    #     names 20 of 30 moved cells and the whole footprint section silently disappears. The fixture
    #     below reproduces the class hermetically (43 changed lines, well past the old 40-line cap) and
    #     pins: the total line printed BEFORE the body (so `| head` still carries the truth), every
    #     changed line present in stdout, and a cap that may only be hit far above this table's size
    #     and must then say so.
    cap_m = re.search(r"^DIFF_PRINT_MAX\s*=\s*(\d+)", open(TOOL, encoding="utf-8").read(), re.M)
    check(cap_m is not None,
          "the census names its own print bound DIFF_PRINT_MAX — a bare slice is the defect")
    DIFF_MAX = int(cap_m.group(1)) if cap_m else 0
    with tempfile.TemporaryDirectory() as d6:
        write_fixtures(d6, {F1: {}, F3: {}})
        tbl_small = os.path.join(d6, "CENSUS.small.md")
        rcs, outs = run(["--dir", d6, "--as-of", "%s-0003" % DAY, "--markdown", tbl_small])
        check(rcs == 0, "small fixture table written (rc=%s: %s)" % (rcs, outs[:200]))
        # grow the corpus: the two input gaps, the churn NO-GO, and two footprint-carrying readings
        write_fixtures(d6)
        for hh, over in (("0006", {"engine_vmswap_mib": "3000", "swap_cached_mib": "1000"}),
                         ("0007", {"engine_vmswap_mib": "9000", "swap_cached_mib": "5000",
                                   "swap_used_mib": "9000"})):
            vals = dict(HEALTHY)
            vals.update(over)
            with open(os.path.join(d6, "preflight-%s-%s.txt" % (DAY, hh)), "w",
                      encoding="utf-8") as fh:
                for k, v in vals.items():
                    fh.write("%s=%s\n" % (k, v))
        tbl_big = os.path.join(d6, "CENSUS.big.md")
        rcb, outb = run(["--dir", d6, "--as-of", "%s-0007" % DAY, "--markdown", tbl_big])
        check(rcb == 0, "grown fixture table written (rc=%s: %s)" % (rcb, outb[:200]))
        dl = list(difflib.unified_diff(open(tbl_small, encoding="utf-8").read().splitlines(),
                                       open(tbl_big, encoding="utf-8").read().splitlines(),
                                       "committed", "recomputed", lineterm=""))
        changed = [l for l in dl if l[:1] in "+-" and l[:3] not in ("+++", "---")]
        # non-vacuity: a 40-line window over this drift MUST hide lines, or the case tests nothing
        check(len(dl) > 40,
              "this fixture drift is bigger than the old silent 40-line cap (got %d lines), "
              "otherwise the truncation case proves nothing" % len(dl))
        rcd, outd = run(["--dir", d6, "--as-of", "%s-0007" % DAY, "--check", tbl_small])
        check(rcd == 1, "a drifted table still reddens --check (rc=%s)" % rcd)
        lines = outd.splitlines()
        cnt = [l for l in lines if l.startswith("DRIFT LINES:")]
        check(len(cnt) == 1, "the drift output carries exactly one DRIFT LINES count line, got %r"
              % cnt[:2])
        if cnt:
            want = ("%d total, %d changed table lines, %d printed, %d not printed"
                    % (len(dl), len(changed), min(len(dl), DIFF_MAX),
                       max(0, len(dl) - DIFF_MAX)))
            check(want in cnt[0],
                  "the count line states the WHOLE drift (%r), got %r" % (want, cnt[0]))
            check(lines.index(cnt[0]) < min([i for i, l in enumerate(lines)
                                             if l.startswith(("+++", "---"))] or [len(lines)]),
                  "the count line is printed BEFORE the diff body, so a pipe to `head` keeps it")
            missing = [l for l in changed if l not in lines]
            check(not missing,
                  "every changed table line of the drift is printed (%d hidden: %r)"
                  % (len(missing), missing[:2]))
        if len(dl) <= DIFF_MAX:
            check("the print stopped at" not in outd,
                  "no truncation note when the whole body fits under the cap")

    # 15. tick 172 (2026-11-15 07:14): the window TRANSITION must be computed, not hand-attributed.
    #     Every census note since tick 145 has asserted, in prose, which reading aged out of the
    #     24 h launchable window and what that did to the count. The table never carried that
    #     attribution, so nothing could contradict it. On the real corpus it was wrong: the published
    #     note for the window `as-of 2026-11-15 06:37` claims launchable "22 -> 23 (this reading
    #     inside; nothing aged out this window)", while the tool's own tables for the two consecutive
    #     windows say 22 -> 22 and one GO did age out (`preflight-20261114-0614.txt`, gate rc 0) —
    #     one entering GO minus one leaving GO nets zero, the exact shape the sentence cannot express.
    #     This case pins `--prev-as-of`: it names the aged-out and newly-entered readings with their
    #     gate rc and a launchable marker, states the delta as arithmetic, fails closed on a malformed
    #     or not-earlier bound, and writes NOTHING into the committed table (byte-identical with or
    #     without the flag). The fixture reproduces the net-zero trap hermetically: a naive "+1"
    #     claim about the entering GO is contradicted by the printed arithmetic.
    NEXT = "preflight-20300102-0006.txt"          # next-day healthy GO: enters the later window
    with tempfile.TemporaryDirectory() as d7:
        write_fixtures(d7, dict(FIXTURES, **{NEXT: {}}))   # F2 NO-GO / F3 NO-GO / F4 F5 gaps kept
        rc0, out0 = run(["--dir", d7, "--as-of", "20300102-0006",
                         "--prev-as-of", "%s-2359" % DAY])
        check(rc0 == 0, "--prev-as-of transition exits 0 (rc=%s: %s)" % (rc0, out0[:300]))
        tl = out0.splitlines()
        blk = [l for l in tl if "WINDOW TRANSITION" in l]
        check(len(blk) == 1, "stdout carries exactly one WINDOW TRANSITION block, got %r" % blk[:2])
        aged_block = [l for l in tl if F1 in l or F2 in l or F3 in l or NEXT in l]
        check(any(F1 in l and "rc 0" in l and "launchable" in l for l in aged_block),
              "the aged-out GO is named with rc 0 AND the launchable marker, got %r" % aged_block[:3])
        check(any(NEXT in l and "rc 0" in l and "launchable" in l for l in aged_block),
              "the entering GO is named with rc 0 AND the launchable marker, got %r" % aged_block[:3])
        ar = [l for l in tl if l.strip().startswith("launchable delta:")]
        check(len(ar) == 1 and ar[0].strip() ==
              "launchable delta: 1 -> 1 = +1 entering GO - 1 aged-out GO",
              "the launchable delta is stated as its own arithmetic and nets ZERO here (a prose "
              "'+1 for this reading' would be the tick-171 defect), got %r" % ar[:1])
        # the two windows' own tables agree with the arithmetic: the count never moved
        ta = os.path.join(d7, "T.prev.md")
        tb = os.path.join(d7, "T.now.md")
        rcp, outp = run(["--dir", d7, "--as-of", "%s-2359" % DAY, "--markdown", ta])
        rcn, outn = run(["--dir", d7, "--as-of", "20300102-0006", "--markdown", tb])
        check(rcp == 0 and rcn == 0, "both window tables written (rc=%s/%s)" % (rcp, rcn))
        check(int_cell(open(ta, encoding="utf-8").read(),
                       "launchable (GO) windows in the last 24 h") == 1
              and int_cell(open(tb, encoding="utf-8").read(),
                           "launchable (GO) windows in the last 24 h") == 1,
              "the launchable cell really is 1 in both windows, so the transition arithmetic is "
              "the whole move and no count changed")
        # a second transition with NO entering reading: three files age out, only one is launchable
        rc1, out1 = run(["--dir", d7, "--as-of", "20300102-0003",
                         "--prev-as-of", "%s-2359" % DAY])
        check(rc1 == 0, "a transition with no entering reading still answers (rc=%s: %s)"
              % (rc1, out1[:200]))
        l1 = out1.splitlines()
        check(any(l.strip() == "aged out of the window (3):" for l in l1),
              "the aged-out header counts all three files, got %r"
              % [l for l in l1 if "aged out" in l][:2])
        check(all(any(n in l and "rc " in l for l in l1) for n in (F1, F2, F3)),
              "every aged-out reading is named with its gate rc, got %r"
              % [l for l in l1 if ".txt" in l][:4])
        check(any(F1 in l and "launchable" in l for l in l1)
              and not any((n in l and "launchable" in l) for l in l1 for n in (F2, F3)),
              "only the GO among the aged files carries the launchable marker")
        ar1 = [l for l in l1 if l.strip().startswith("launchable delta:")]
        check(len(ar1) == 1 and ar1[0].strip() ==
              "launchable delta: 1 -> 0 = +0 entering GO - 1 aged-out GO",
              "a NO-GO aging out changes no launchable count and the arithmetic says so, got %r"
              % ar1[:1])
        # fail-closed bounds, and no byte may enter the committed table because of this flag
        rcb, outb2 = run(["--dir", d7, "--as-of", "20300102-0006", "--prev-as-of", "nonsense"])
        check(rcb == 1 and "--prev-as-of must be YYYYMMDD-HHMM" in outb2,
              "a malformed --prev-as-of is an input gap naming the flag, got rc=%s %r"
              % (rcb, outb2[:200]))
        rcl, outl = run(["--dir", d7, "--as-of", "20300102-0006", "--prev-as-of", "20300102-0006"])
        check(rcl == 1 and "not earlier than --as-of" in outl,
              "a --prev-as-of that is not earlier fails closed, got rc=%s %r" % (rcl, outl[:200]))
        m_plain = os.path.join(d7, "T.plain.md")
        m_flag = os.path.join(d7, "T.flag.md")
        rcA, _ = run(["--dir", d7, "--as-of", "20300102-0006", "--markdown", m_plain])
        rcB, _ = run(["--dir", d7, "--as-of", "20300102-0006", "--prev-as-of", "%s-2359" % DAY,
                      "--markdown", m_flag])
        check(rcA == 0 and rcB == 0
              and open(m_plain, encoding="utf-8").read() == open(m_flag, encoding="utf-8").read(),
              "the generated table is BYTE-IDENTICAL with and without --prev-as-of")
        check("WINDOW TRANSITION" not in open(m_flag, encoding="utf-8").read(),
              "the transition block is stdout evidence only and never joins a committed table")
        # the attribution must be the DEFAULT, not something a later tick can forget to ask for
        rcD, outD = run(["--dir", d7, "--as-of", "20300102-0006"])
        dline = [l for l in outD.splitlines() if "prev window" in l]
        check(rcD == 0 and "WINDOW TRANSITION" in outD
              and "[derived: previous stored reading]" in outD
              and any("as-of 2030-01-01 00:05 [derived" in l for l in dline),
              "flagless, the census derives the previous window bound from the previous stored "
              "reading and says so, got %r" % dline[:1])
        d_ar = [l for l in outD.splitlines() if l.strip().startswith("launchable delta:")]
        check(d_ar == ar,
              "the derived bound and the operator-supplied bound state the same arithmetic "
              "(%r vs %r)" % (d_ar[:1], ar[:1]))
        rcN, outN = run(["--dir", d7, "--as-of", "20300102-0006", "--no-transition"])
        check(rcN == 0 and "WINDOW TRANSITION" not in outN and "launchable delta:" not in outN,
              "--no-transition silences the block and changes nothing else (rc=%s)" % rcN)

    # 16. tick 192 (2026-11-15): the DAY rule band. The refusal band, the refusal median, the
    # GO-to-refusal dead zone and the streaks existed only as tick sentences, and a sentence is
    # not recomputed: two consecutive ticks quoted a 4.22x median that this tool's own arithmetic
    # gives as 3.985x at the 30th reading and 3.745x at the 31st. These cells now come from the
    # same per-file gate returncodes as the verdict column, so they are pinned like any other.
    d8 = tempfile.mkdtemp(prefix="pubcensus-day-")
    try:
        write_fixtures(d8)
        rcd, outd = run(["--dir", d8, "--as-of", "%s-0005" % DAY])
        hdr = [l for l in outd.splitlines() if l.startswith("Census stamp:")]
        check(rcd == 0 and len(hdr) == 1 and STAMP_NAME in hdr[0],
              "the census stamps itself with the declared shape, got rc=%s %r" % (rcd, hdr[:1]))
        # F1 GO at 0.005x, F2 swap refusal at 8.0x, F3 GPU refusal at 0.0x, F4/F5 input gaps
        check((cell(outd, "day launchable (GO) swap draws") or "").startswith("1 (band 0.01-0.01"),
              "one GO draw with quiet swap, got %r"
              % cell(outd, "day launchable (GO) swap draws"))
        check(cell(outd, "day refusals at or above the swap-mean ceiling")
              == "1 (band 8.00-8.00 x, **median 8.000 x recomputed at this cut**)",
              "the swap-refusal band and median are the mean-rule refusals only, got %r"
              % cell(outd, "day refusals at or above the swap-mean ceiling"))
        c_other = cell(outd, "day refusals decided by a rule OTHER than swap (window below ceiling)")
        check(c_other == "1: %s at 0.00 x" % F3,
              "the GPU-contention refusal is named and kept OUT of the swap band, got %r" % c_other)
        c_zone = cell(outd, "day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary)")
        check(c_zone == "0.01-8.00 x — EMPTY (0 windows inside)",
              "the dead zone is printed with a computed state word, got %r" % c_zone)
        c_run = cell(outd, "longest consecutive NO-GO run inside the day")
        check(c_run == "2 readings (any-verdict non-GO run: 4)",
              "an input-gap run must not be reported as a refusal run, got %r" % c_run)
        check(cell(outd, "readings since the day's last gate-GO") == "4 (last GO 00:01)",
              "readings since the last GO, got %r"
              % cell(outd, "readings since the day's last gate-GO"))
        check(cell(outd, "launchable footprint maximum of the day and its age")
              == "n/a MiB set at n/a, n/a reading(s) ago"
              and cell(outd, "trailing consecutive day windows with footprint above that maximum")
              == "0",
              "a corpus with no footprint key prints n/a and 0, never a fabricated ceiling")
        # tamper A: a refusal whose swap window sits INSIDE the zone flips the state word
        write_fixtures(d8, {F3: {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0",
                                 "gpu_util_peak_pct": "100", "gpu_power_w": "128.0",
                                 "swap_in_mib_per_s": "2.0", "swap_out_mib_per_s": "0.0",
                                 "swap_total_peak_mib_per_s": "3.0"}})
        rcz, outz = run(["--dir", d8, "--as-of", "%s-0005" % DAY])
        c_z2 = cell(outz, "day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary)")
        check(rcz == 0 and c_z2 == "0.01-8.00 x — POPULATED (1 windows inside)",
              "the EMPTY state word is data-dependent, not boilerplate, got %r" % c_z2)
        # tamper B: the GO draw becomes a swap refusal — median must move, the zone must not
        # invent bounds, and the streak/since-GO cells must follow
        write_fixtures(d8, {F1: {"swap_in_mib_per_s": "30.0", "swap_out_mib_per_s": "0.0",
                                 "swap_total_peak_mib_per_s": "90.0"}})
        rcy, outy = run(["--dir", d8, "--as-of", "%s-0005" % DAY])
        c_y = cell(outy, "day refusals at or above the swap-mean ceiling")
        check(rcy == 0 and c_y == "2 (band 1.50-8.00 x, **median 4.750 x recomputed at this cut**)",
              "the median is recomputed from the current cut, not carried, got %r" % c_y)
        check((cell(outy, "day launchable (GO) swap draws") or "").startswith("0 (band n/a-n/a"),
              "an empty GO group prints n/a rather than a nonsense band, got %r"
              % cell(outy, "day launchable (GO) swap draws"))
        check("NO-DATA" in (cell(outy, "day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary)")
                            or ""),
              "a day with no GO draws has no dead zone to state, got %r"
              % cell(outy, "day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, not the rule boundary)"))
        check(cell(outy, "longest consecutive NO-GO run inside the day")
              == "3 readings (any-verdict non-GO run: 5)"
              and cell(outy, "readings since the day's last gate-GO")
              == "n/a — no GO of this day",
              "streaks and the since-GO counter follow the verdicts, got %r / %r"
              % (cell(outy, "longest consecutive NO-GO run inside the day"),
                 cell(outy, "readings since the day's last gate-GO")))
        # the footprint age rows: a launchable window sets the ceiling, everything after it is above
        write_fixtures(d8, {F1: {"engine_vmswap_mib": "1000"},
                            F2: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                                 "swap_total_peak_mib_per_s": "300.0",
                                 "engine_vmswap_mib": "12000"},
                            F3: {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0",
                                 "gpu_util_peak_pct": "100", "gpu_power_w": "128.0",
                                 "swap_in_mib_per_s": "0.0", "swap_out_mib_per_s": "0.0",
                                 "swap_total_peak_mib_per_s": "0.0",
                                 "engine_vmswap_mib": "12000"},
                            F4: {"engine_pcpu": "NaN", "swap_total_peak_mib_per_s": "400.0",
                                 "engine_vmswap_mib": "12000"},
                            F5: {"swap_total_peak_mib_per_s": "NaN",
                                 "engine_vmswap_mib": "12000"}})
        rcf, outf = run(["--dir", d8, "--as-of", "%s-0005" % DAY])
        c_fp = cell(outf, "launchable footprint maximum of the day and its age")
        c_tr = cell(outf, "trailing consecutive day windows with footprint above that maximum")
        check(rcf == 0 and c_fp == "1000 MiB set at 00:01, 4 reading(s) ago" and c_tr == "4",
              "the launchable-footprint ceiling ages in public and every window above it is "
              "counted, got %r / %r" % (c_fp, c_tr))
    finally:
        shutil.rmtree(d8, ignore_errors=True)

    # 17. tick 193 (2026-11-16): the day table resets at midnight, so a streak that started on the
    # previous evening disappears from every day-scoped cell. Measured live at the first reading of
    # 2026-11-16: the day cells printed a run of 1 and `n/a — no GO of this day` while the box had
    # refused four readings in a row across midnight and its last GO was 162 minutes back. The
    # window-scoped continuity rows carry the streak, and the divergence gets a state word.
    d9 = tempfile.mkdtemp(prefix="pubcensus-night-")
    NIGHT = {  # GO at 23:40, then refusals at 23:50, 00:01 and 00:05 — three across midnight
        "preflight-20300101-2340.txt": {},
        "preflight-20300101-2350.txt": {"swap_in_mib_per_s": "120.0",
                                        "swap_out_mib_per_s": "40.0",
                                        "swap_total_peak_mib_per_s": "300.0"},
        "preflight-20300102-0001.txt": {"swap_in_mib_per_s": "60.0",
                                        "swap_out_mib_per_s": "0.0",
                                        "swap_total_peak_mib_per_s": "80.0"},
        "preflight-20300102-0005.txt": {"swap_in_mib_per_s": "90.0",
                                        "swap_out_mib_per_s": "0.0",
                                        "swap_total_peak_mib_per_s": "120.0"},
    }
    try:
        write_fixtures(d9, NIGHT)
        rcn, outn = run(["--dir", d9, "--as-of", "20300102-0005"])
        check(rcn == 0, "the midnight fixture census exits 0 (rc=%s: %s)" % (rcn, outn[-300:]))
        # the day table alone would report a young day: 3 readings, all NO-GO, run of 3
        check(cell(outn, "readings of the as-of day") == "2 (0 GO / 2 NO-GO / 0 gap)"
              and cell(outn, "longest consecutive NO-GO run inside the day")
              == "2 readings (any-verdict non-GO run: 2)"
              and cell(outn, "readings since the day's last gate-GO") == "n/a — no GO of this day",
              "the DAY cells see only the new day, which is what the window rows must correct, "
              "got %r / %r / %r" % (cell(outn, "readings of the as-of day"),
                                    cell(outn, "longest consecutive NO-GO run inside the day"),
                                    cell(outn, "readings since the day's last gate-GO")))
        check(cell(outn, "trailing consecutive NO-GO run ending at the newest reading "
                         "(last 24 h, crosses the day boundary)")
              == "3 readings (any-verdict non-GO run: 3)",
              "the window row carries the refusal streak across midnight, got %r"
              % cell(outn, "trailing consecutive NO-GO run ending at the newest reading "
                           "(last 24 h, crosses the day boundary)"))
        check(cell(outn, "readings since the last gate-GO (last 24 h, any day)")
              == "3 (last GO preflight-20300101-2340.txt at 2030-01-01 23:40, 25 min before "
                 "as-of)",
              "the window since-GO row names the GO and ages it, got %r"
              % cell(outn, "readings since the last gate-GO (last 24 h, any day)"))
        check(cell(outn, "window run vs day run (computed, never asserted)")
              == "MIDNIGHT RESET — the current refusal run starts on an earlier day: window 3 "
                 "reading(s) vs day 2",
              "the scope divergence is stated as a computed state word, got %r"
              % cell(outn, "window run vs day run (computed, never asserted)"))
        # non-vacuity A: a GO at the newest reading leaves no run to carry at all
        night_a = dict(NIGHT)
        night_a["preflight-20300102-0005.txt"] = {}
        write_fixtures(d9, night_a)
        rca, outa = run(["--dir", d9, "--as-of", "20300102-0005"])
        check(rca == 0 and cell(outa, "trailing consecutive NO-GO run ending at the newest reading "
                                      "(last 24 h, crosses the day boundary)")
              == "0 readings (any-verdict non-GO run: 0)",
              "a trailing GO means no refusal run, got %r"
              % cell(outa, "trailing consecutive NO-GO run ending at the newest reading "
                           "(last 24 h, crosses the day boundary)"))
        check(cell(outa, "window run vs day run (computed, never asserted)")
              == "NO TRAILING REFUSAL RUN (the newest reading is a gate GO; any-verdict non-GO run "
                 "0 reading(s))",
              "the state word follows the verdict stream, it is not a fixed midnight claim, got %r"
              % cell(outa, "window run vs day run (computed, never asserted)"))
        # non-vacuity B: the same streak fully inside the new day reads MATCHED, not RESET
        night_b = dict(NIGHT)
        del night_b["preflight-20300101-2350.txt"]
        write_fixtures(d9, night_b)
        for gone in ("preflight-20300101-2350.txt",):
            p = os.path.join(d9, gone)
            if os.path.exists(p):
                os.remove(p)
        rcb, outb = run(["--dir", d9, "--as-of", "20300102-0005"])
        check(rcb == 0 and cell(outb, "trailing consecutive NO-GO run ending at the newest reading "
                                      "(last 24 h, crosses the day boundary)")
              == "2 readings (any-verdict non-GO run: 2)"
              and cell(outb, "window run vs day run (computed, never asserted)")
              == "MATCHED (the current refusal run starts inside the as-of day)",
              "a run that starts inside the day must not claim a midnight reset, got %r / %r"
              % (cell(outb, "trailing consecutive NO-GO run ending at the newest reading "
                            "(last 24 h, crosses the day boundary)"),
                 cell(outb, "window run vs day run (computed, never asserted)")))
        # non-vacuity C: an input gap at the newest position is a cut sample, not a refusal
        night_c = dict(NIGHT)
        night_c["preflight-20300102-0005.txt"] = {"engine_pcpu": "NaN"}
        write_fixtures(d9, night_c)
        rcc2, outc2 = run(["--dir", d9, "--as-of", "20300102-0005"])
        check(rcc2 == 0 and cell(outc2, "trailing consecutive NO-GO run ending at the newest "
                                        "reading (last 24 h, crosses the day boundary)")
              == "0 readings (any-verdict non-GO run: 3)",
              "an input gap breaks the refusal run but stays a non-GO reading, got %r"
              % cell(outc2, "trailing consecutive NO-GO run ending at the newest reading "
                            "(last 24 h, crosses the day boundary)"))
        check(cell(outc2, "window run vs day run (computed, never asserted)")
              == "NO TRAILING REFUSAL RUN (the newest reading is an input gap; any-verdict non-GO "
                 "run 3 reading(s))",
              "the state word names the input gap rather than inventing a refusal streak, got %r"
              % cell(outc2, "window run vs day run (computed, never asserted)"))
        # --check on a snapshot of the midnight set must be stable (the rows are generated, not typed)
        tbl9 = os.path.join(d9, "CEN.md")
        write_fixtures(d9, NIGHT)
        rcw9, outw9 = run(["--dir", d9, "--as-of", "20300102-0005", "--markdown", tbl9])
        check(rcw9 == 0, "writing the midnight snapshot exits 0, got %r" % outw9[-300:])
        rcv9, outv9 = run(["--dir", d9, "--as-of", "20300102-0005", "--check", tbl9])
        check(rcv9 == 0, "the midnight snapshot checks clean, got %r" % outv9[-300:])
        text9 = open(tbl9, encoding="utf-8").read()
        check(text9.count("| window run vs day run (computed, never asserted) |") == 1,
              "the continuity block appears exactly once in the committed table")
    finally:
        shutil.rmtree(d9, ignore_errors=True)

    # 18. tick 195 (2026-11-16): the rule band existed at ONE scope only. The dead zone between the
    # highest launchable swap draw and the lowest swap-rule refusal is a property of the row set it
    # is measured over, and every tick sentence that said "the dead zone" quoted the calendar-day
    # row set as if it were the rule. These rows are computed from the same `day_band` arithmetic
    # over three row sets, with a state word that says what the scopes disagree about.
    d10 = tempfile.mkdtemp(prefix="pubcensus-scope-")
    SCOPE = {
        "preflight-20300101-2340.txt": {},                                   # GO, 0.005 x
        "preflight-20300101-2350.txt": {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                                        "swap_total_peak_mib_per_s": "300.0"},   # NO-GO, 8.00 x
        "preflight-20300102-0001.txt": {"swap_in_mib_per_s": "60.0", "swap_out_mib_per_s": "0.0",
                                        "swap_total_peak_mib_per_s": "80.0"},    # NO-GO, 3.00 x
        "preflight-20300102-0005.txt": {"swap_in_mib_per_s": "90.0", "swap_out_mib_per_s": "0.0",
                                        "swap_total_peak_mib_per_s": "120.0"},   # NO-GO, 4.50 x
    }
    GPU_MID = {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0", "gpu_util_peak_pct": "100",
               "gpu_power_w": "128.0", "swap_in_mib_per_s": "10.0", "swap_out_mib_per_s": "0.0",
               "swap_total_peak_mib_per_s": "12.0"}      # NO-GO by the GPU rule at 0.50 x

    def run_fx(fx, as_of="20300102-0005"):
        """Fresh directory per control: `write_fixtures` never deletes, so controls that share a
        directory silently inherit each other's readings."""
        d = tempfile.mkdtemp(prefix="pubcensus-fx-")
        try:
            write_fixtures(d, fx)
            return run(["--dir", d, "--as-of", as_of])
        finally:
            shutil.rmtree(d, ignore_errors=True)

    try:
        write_fixtures(d10, SCOPE)
        rcs, outs = run(["--dir", d10, "--as-of", "20300102-0005"])
        hdrs = [l for l in outs.splitlines() if l.startswith("Census stamp:")]
        check(rcs == 0 and len(hdrs) == 1 and STAMP_NAME in hdrs[0],
              "the census stamps itself with the declared shape at every cut, got rc=%s %r"
              % (rcs, hdrs[:1]))
        c_den = cell(outs, "readings this scope can band at all (verdict GO or NO-GO AND a "
                           "parseable `swap_in + swap_out` window)")
        check(c_den == "DAY `20300102` 2 of 2, last 24 h 4 of 4, whole corpus 4 of 4",
              "the band denominator is printed per scope, so a corpus band cannot be read as a "
              "statement about the whole archive, got %r" % c_den)
        check(cell(outs, "launchable (GO) swap draws, whole corpus")
              == "1, band 0.01-0.01 x the 20.0 mean ceiling",
              "the corpus GO band is the corpus row set, got %r"
              % cell(outs, "launchable (GO) swap draws, whole corpus"))
        check(cell(outs, "swap-rule refusals (window at/above that ceiling), last 24 h")
              == "3, band 3.00-8.00 x, **median 4.500 x recomputed at this cut**",
              "the window refusal band and median are computed for the window row set, got %r"
              % cell(outs, "swap-rule refusals (window at/above that ceiling), last 24 h"))
        cz_day = cell(outs, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), DAY `20300102`")
        cz_win = cell(outs, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), last 24 h")
        check(cz_day == "NO ZONE at this scope (no launchable draw or no swap-rule refusal with a "
                        "parseable window)",
              "the as-of day has no launchable draw, so it cannot state a dead zone at all, got %r"
              % cz_day)
        check(cz_win == "EMPTY (0 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)",
              "the window scope states the zone the day scope cannot, got %r" % cz_win)
        c_state = cell(outs, "launchable-column gap scope state (computed, never asserted)")
        check(c_state.startswith("PARTLY UNMEASURABLE — a zone exists only at last 24 h, whole "
                                 "corpus") and "no zone at DAY `20300102`" in c_state,
              "a scope with no zone is named, not silently averaged away, got %r" % c_state)
        # non-vacuity A: one launchable draw ON the as-of day makes all three scopes agree
        scope_a = dict(SCOPE)
        scope_a["preflight-20300102-0003.txt"] = {}
        rca, outa = run_fx(scope_a)
        check(rca == 0 and cell(outa, "launchable-column gap scope state (computed, never asserted)")
              .startswith("IDENTICAL AT ALL THREE SCOPES (bounds 0.01-3.00 x, width 2.995 x "
                          "(59.9 MiB/s), EMPTY (0 inside))"),
              "the scope state follows the row sets; a single GO on the as-of day collapses the "
              "divergence, got %r"
              % cell(outa, "launchable-column gap scope state (computed, never asserted)"))
        # non-vacuity B: a GPU-rule refusal at 0.50 x sits INSIDE the zone, but only for the wider
        # row sets — same bounds, different occupancy, which is the difference between a boundary
        # the rule has never been tested against and one it has.
        scope_b = dict(scope_a)
        scope_b["preflight-20300101-2355.txt"] = GPU_MID
        rcb, outb = run_fx(scope_b)
        c_sb = cell(outb, "launchable-column gap scope state (computed, never asserted)")
        check(rcb == 0 and c_sb.startswith("SAME BOUNDS, DIFFERENT OCCUPANCY")
              and cell(outb, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), DAY `20300102`")
              == "EMPTY (0 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)"
              and cell(outb, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), last 24 h")
              == "POPULATED (1 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)",
              "the day scope calls the zone empty while the window scope has a reading inside it, "
              "got %r / %r / %r" % (c_sb, cell(outb, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), DAY `20300102`"),
                                    cell(outb, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), last 24 h")))
        check(cell(outb, "refusals decided by a rule OTHER than swap (window below the ceiling)")
              == "DAY `20300102` 0, last 24 h 1, whole corpus 1",
              "the 0.50 x GPU refusal is counted outside the swap band at every scope that sees "
              "it, got %r"
              % cell(outb, "refusals decided by a rule OTHER than swap (window below the ceiling)"))
        # non-vacuity C: a SECOND launchable draw, higher, on the PREVIOUS day moves the window and
        # corpus GO bound but not the day's, so the widths differ and the state word names both
        scope_c = dict(scope_a)
        scope_c["preflight-20300101-2355.txt"] = {"swap_in_mib_per_s": "15.0",
                                                  "swap_out_mib_per_s": "0.0",
                                                  "swap_total_peak_mib_per_s": "40.0"}
        rcc, outc = run_fx(scope_c)
        c_sc = cell(outc, "launchable-column gap scope state (computed, never asserted)")
        check(rcc == 0 and c_sc.startswith("SCOPE-DEPENDENT — the DAY `20300102` dead zone is "
                                           "2.995 x (59.9 MiB/s) wide and the last 24 h one 2.250 x "
                                           "(45.0 MiB/s)"),
              "differing widths name both scopes and the factor, got %r" % c_sc)
        check(cell(outc, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), whole corpus")
              == "EMPTY (0 windows inside), bounds 0.75-3.00 x, width 2.250 x (45.0 MiB/s)",
              "the corpus GO bound follows the previous day's draw, got %r"
              % cell(outc, "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), whole corpus"))
        # non-vacuity D: with no launchable draw anywhere, no scope may state a zone
        scope_d = {k: v for k, v in SCOPE.items() if k != "preflight-20300101-2340.txt"}
        rcd2, outd2 = run_fx(scope_d)
        check(rcd2 == 0 and cell(outd2, "launchable-column gap scope state (computed, never asserted)")
              .startswith("NO DEAD ZONE AT ANY SCOPE")
              and all(cell(outd2, lbl).startswith("NO ZONE at this scope")
                      for lbl in ("launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), DAY `20300102`", "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), last 24 h",
                                  "launchable-column gap (GO max to refusal min; VERDICT-scoped, not the rule boundary), whole corpus")),
              "no scope invents a dead zone out of a refusal column alone, got %r"
              % cell(outd2, "launchable-column gap scope state (computed, never asserted)"))
        # the block is generated, so a snapshot of it must check clean and appear exactly once
        tbl10 = os.path.join(d10, "CEN.md")
        write_fixtures(d10, SCOPE)
        rcw10, outw10 = run(["--dir", d10, "--as-of", "20300102-0005", "--markdown", tbl10])
        check(rcw10 == 0, "writing the scope-band snapshot exits 0, got %r" % outw10[-300:])
        rcv10, outv10 = run(["--dir", d10, "--as-of", "20300102-0005", "--check", tbl10])
        check(rcv10 == 0, "the scope-band snapshot checks clean, got %r" % outv10[-300:])
        text10 = open(tbl10, encoding="utf-8").read()
        check(text10.count("| launchable-column gap scope state (computed, never asserted) |") == 1
              and text10.count("| rule band at three scopes (added 2026-11-16, tick 195) |") == 1
              and text10.count("| rule-boundary scope state (computed, never asserted) |") == 1
              and text10.count("| swap-rule decision boundary, ") == 3,
              "the three-scope block appears exactly once in a committed table")
    finally:
        shutil.rmtree(d10, ignore_errors=True)

    # ---- census v8 (2026-11-16 02:55, tick 196): the rule's OWN boundary vs the launchable gap -
    # One printed row bounded an interval on the gate VERDICT and got quoted as the swap rule's
    # resolution. On the real corpus the two quantities differ: `preflight-20261116-0214.txt`
    # carries swap 0.0 in + 18.8 out = 0.94 x of the 20.0 MiB/s ceiling, which the swap rule
    # ACCEPTED (the reading was refused instead by the device, state-D and GPU-mean rules). That
    # one draw raises the rule's accepted bound from the GO maximum 0.905 x to 0.94 x and is also
    # the reading v7 counted as `POPULATED (1 windows inside)` — an accepted draw used as evidence
    # that the band is unmeasured. These fixtures reproduce that shape mechanically.
    BOUND = {
        "preflight-%s-0001.txt" % DAY: {},                      # GO, swap 0.1 = 0.005 x
        "preflight-%s-0002.txt" % DAY: {                        # GPU contention refuses; the
            "gpu_util_pct": "100", "gpu_util_mean_pct": "97.0", # SWAP rule accepts 0.0+18.8=0.94 x
            "gpu_util_peak_pct": "100", "gpu_power_w": "128.0",
            "swap_in_mib_per_s": "0.0", "swap_out_mib_per_s": "18.8",
            "swap_total_peak_mib_per_s": "18.8"},
        "preflight-%s-0003.txt" % DAY: {                        # the swap rule refuses 21.2=1.06 x
            "swap_in_mib_per_s": "21.2", "swap_out_mib_per_s": "0.0",
            "swap_total_peak_mib_per_s": "60.0"},
        "preflight-%s-0004.txt" % DAY: {                        # INPUT GAP: never judged, and its
            "engine_pcpu": "NaN",                               # 0.0+20.4 = 1.02 x lies in the band
            "swap_in_mib_per_s": "0.0", "swap_out_mib_per_s": "20.4",
            "swap_total_peak_mib_per_s": "20.4"},
    }
    BND = "day swap-rule decision boundary (accepted max to refusal min)"
    d11 = tempfile.mkdtemp(prefix="pubcensus-bound-")
    try:
        write_fixtures(d11, BOUND)
        rcb, outb = run(["--dir", d11, "--as-of", "%s-0005" % DAY])
        check(rcb == 0, "the boundary fixtures exit 0, got rc=%s %r" % (rcb, outb[-300:]))
        c_acc = cell(outb, "day swap-rule ACCEPTED draws (any verdict — the rule's own "
                           "denominator)")
        check((c_acc or "").startswith("2 (band 0.01-0.94 x)"),
              "the accepted denominator counts rule passes whatever the verdict said, got %r"
              % c_acc)
        c_bnd = cell(outb, BND)
        check(c_bnd and "accepted up to 0.94 x, refused from 1.06 x, unresolved band 0.120 x "
                        "(2.4 MiB/s) — EMPTY BY CONSTRUCTION (0 judged draws inside)" in c_bnd
              and ("preflight-%s-0004.txt at 1.02 x" % DAY) in c_bnd,
              "the rule boundary rides on the rule's own decision and names the unjudged draw "
              "inside separately, got %r" % c_bnd)
        # the non-vacuity control that proves the split is real: on the SAME bytes the
        # verdict-scoped row still says POPULATED, so the old word survives only where its
        # denominator is honest.
        c_gap = cell(outb, "day launchable-column gap (GO max to lowest refusal; VERDICT-scoped, "
                           "not the rule boundary)")
        check(c_gap and "0.01-1.06 x — POPULATED (1 windows inside)" in c_gap,
              "the verdict-scoped gap keeps its POPULATED word on the same bytes, got %r" % c_gap)
        c_bs = cell(outb, "rule-boundary scope state (computed, never asserted)")
        check((c_bs or "").startswith("IDENTICAL AT ALL THREE SCOPES"),
              "one single-day row set states one rule boundary at all three scopes, got %r" % c_bs)
        # control A: push fixture 2's window AT the ceiling (0.5+21.5 = 22.0 = 1.10 x). The rule
        # now refuses it, so the accepted bound must fall back to the GO draw — proof the bound is
        # computed from rule decisions and not copied from the verdict column.
        ba = dict(BOUND)
        ba["preflight-%s-0002.txt" % DAY] = dict(
            BOUND["preflight-%s-0002.txt" % DAY],
            swap_in_mib_per_s="0.5", swap_out_mib_per_s="21.5",
            swap_total_peak_mib_per_s="30.0")
        d12 = tempfile.mkdtemp(prefix="pubcensus-boundA-")
        try:
            write_fixtures(d12, ba)
            rcba, outba = run(["--dir", d12, "--as-of", "%s-0005" % DAY])
            c_ba = cell(outba, BND)
            check(rcba == 0 and c_ba and "accepted up to 0.01 x, refused from 1.06 x, unresolved "
                                         "band 1.055 x (21.1 MiB/s)" in c_ba,
                  "a draw at the ceiling drags the rule's accepted bound down (control A), got %r"
                  % c_ba)
        finally:
            shutil.rmtree(d12, ignore_errors=True)
        # control B: delete the unjudged reading. The bounds must not move and the gap naming must
        # vanish — proof the naming is computed per reading, not a fixed suffix.
        bb = {k: v for k, v in BOUND.items() if not k.endswith("-0004.txt")}
        d13 = tempfile.mkdtemp(prefix="pubcensus-boundB-")
        try:
            write_fixtures(d13, bb)
            rcbb, outbb = run(["--dir", d13, "--as-of", "%s-0005" % DAY])
            c_bb = cell(outbb, BND)
            check(rcbb == 0 and c_bb and "input-gap readings inside: none" in c_bb
                  and "accepted up to 0.94 x" in c_bb,
                  "deleting the unjudged reading deletes the naming but not the bounds (control B),"
                  " got %r" % c_bb)
        finally:
            shutil.rmtree(d13, ignore_errors=True)
        # control C: the boundary is scope-dependent too. A second day carries an accepted draw at
        # 0.98 x and a refusal at 1.30 x; the day/24 h scopes then hold a 0.320 x band while the
        # corpus holds 0.98-1.06 x = 0.080 x, and the state word must name both.
        bc = dict(BOUND)
        bc["preflight-20300102-0001.txt"] = dict(
            BOUND["preflight-%s-0002.txt" % DAY],
            swap_in_mib_per_s="1.0", swap_out_mib_per_s="18.6",
            swap_total_peak_mib_per_s="20.0")     # 19.6 = 0.98 x, GPU refuses (peak >= window sum
                                                  # or the gate calls the reading an input gap)
        bc["preflight-20300102-0002.txt"] = {                       # 26.0 = 1.30 x, swap refuses
            "swap_in_mib_per_s": "26.0", "swap_out_mib_per_s": "0.0",
            "swap_total_peak_mib_per_s": "60.0"}
        d14 = tempfile.mkdtemp(prefix="pubcensus-boundC-")
        try:
            write_fixtures(d14, bc)
            rcbc, outbc = run(["--dir", d14, "--as-of", "20300102-0005"])
            c_day = cell(outbc, "swap-rule decision boundary, DAY `20300102`")
            c_cor = cell(outbc, "swap-rule decision boundary, whole corpus")
            c_bc = cell(outbc, "rule-boundary scope state (computed, never asserted)")
            check(rcbc == 0 and c_day and "accepted up to 0.98 x, refused from 1.30 x, unresolved "
                                          "band 0.320 x (6.4 MiB/s)" in c_day
                  and c_cor and "accepted up to 0.98 x, refused from 1.06 x, unresolved band "
                                "0.080 x (1.6 MiB/s)" in c_cor,
                  "the rule boundary narrows when the row set widens, got %r / %r" % (c_day, c_cor))
            check((c_bc or "").startswith("SCOPE-DEPENDENT — the rule's unresolved band is "
                                          "0.320 x (6.4 MiB/s) wide")
                  and "misstates the rule's resolution by up to 4.0x" in (c_bc or ""),
                  "the rule-boundary scope state names both widths and the misstatement factor, "
                  "got %r" % c_bc)
        finally:
            shutil.rmtree(d14, ignore_errors=True)
    finally:
        shutil.rmtree(d11, ignore_errors=True)

    # ---- census v9 (2026-11-16 03:47, tick 197): WHICH gate rule refused ----------------------
    # Every tick before this one attributed refusals in prose ("the 02:14 reading died on the
    # device, state-D and GPU-mean rules") and nothing computed it. The block must (a) count each
    # rule out of the gate's OWN reason lines, (b) print a zero row for a rule that never fires
    # instead of dropping it, (c) agree with the census's own ratio-derived swap-refusal set,
    # (d) move when the row set (scope) moves, (e) exit 1 when the gate's refusal vocabulary no
    # longer matches the rule table, and (f) exit 4 naming files on a reason it cannot map.
    v9f = {
        "preflight-%s-0101.txt" % DAY: {},                                        # GO
        "preflight-%s-0102.txt" % DAY: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                                        "swap_total_peak_mib_per_s": "300.0"},    # swap-rate (sole)
        "preflight-%s-0103.txt" % DAY: {"blk_read_mib_per_s": "60.0"},            # device-read
        "preflight-%s-0104.txt" % DAY: {"gpu_util_pct": "100", "gpu_util_mean_pct": "97.0",
                                        "gpu_util_peak_pct": "100"},              # gpu-busy
        "preflight-%s-0105.txt" % DAY: {"engine_state": "D"},                     # engine-state-D
        "preflight-%s-0106.txt" % DAY: {"swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                                        "swap_total_peak_mib_per_s": "300.0",
                                        "gpu_util_pct": "100", "gpu_util_mean_pct": "97.0",
                                        "gpu_util_peak_pct": "100"},              # swap+gpu (multi)
        "preflight-%s-0107.txt" % DAY: {"health_code": "503"},                    # health-code
        "preflight-%s-0108.txt" % DAY: {"health_loaded": "false"},                # health-loaded
        "preflight-%s-0109.txt" % DAY: {"engine_serve_procs": "0"},               # serve procs
        "preflight-%s-0110.txt" % DAY: {"swap_free_mib": "100", "swap_used_mib": "65435"},
        "preflight-%s-0111.txt" % DAY: {"mem_available_mib": "100"},              # mem-available
        "preflight-%s-0112.txt" % DAY: {"foreign_legs": "1"},                     # foreign-legs
        "preflight-%s-0113.txt" % DAY: {"engine_pcpu": "620.0"},                  # idle-spin
    }
    d15 = tempfile.mkdtemp(prefix="pubcensus-rules-")
    try:
        write_fixtures(d15, v9f)
        rc15, out15 = run(["--dir", d15, "--no-transition"])

        def rule_cell(rid):
            return next((l for l in out15.splitlines()
                         if l.startswith("| rule fired:") and ("`%s`" % rid) in l), "")

        check(rc15 == 0,
              "the refusal-rule census runs clean on a fixture set with one refusal per rule "
              "(rc=%s)" % rc15)
        # (a) every rule counted from the gate's own reason lines, at all three scopes
        for rid, want in (("swap-rate", "2 fired, 1 sole"), ("device-read", "1 fired, 1 sole"),
                          ("gpu-busy", "2 fired, 1 sole"), ("engine-state-D", "1 fired, 1 sole"),
                          ("health-code-not-200", "1 fired, 1 sole"),
                          ("health-loaded-false", "1 fired, 1 sole"),
                          ("engine-process-absent", "1 fired, 1 sole"),
                          ("swap-free-low", "1 fired, 1 sole"),
                          ("mem-available-low", "1 fired, 1 sole"),
                          ("foreign-legs", "1 fired, 1 sole"), ("idle-spin", "1 fired, 1 sole")):
            c = rule_cell(rid) or ""
            check(c.count(want) == 3,
                  "rule %s counts %r at all three scopes, got %r" % (rid, want, c))
        # (b) a rule that never fires prints a zero row: a dropped row and a zero row read alike
        d15b = tempfile.mkdtemp(prefix="pubcensus-rules-none-")
        try:
            write_fixtures(d15b, {"preflight-%s-0101.txt" % DAY: {},
                                  "preflight-%s-0102.txt" % DAY: {"engine_state": "D"}})
            rcb, outb = run(["--dir", d15b, "--no-transition"])
            zero = [l for l in outb.splitlines()
                    if l.startswith("| rule fired:") and "`idle-spin`" in l]
            check(rcb == 0 and len(zero) == 1 and "0 fired" in zero[0]
                  and all(("0 fired" in l or "`engine-state-D`" in l)
                          for l in outb.splitlines() if l.startswith("| rule fired:")),
                  "a rule that never fires still gets its row and prints 0 fired, got rc=%s %r"
                  % (rcb, zero))
        finally:
            shutil.rmtree(d15b, ignore_errors=True)
        check(len([l for l in out15.splitlines() if l.startswith("| rule fired:")]) == 11,
              "the table carries one row per refusal rule (11), got %d"
              % len([l for l in out15.splitlines() if l.startswith("| rule fired:")]))
        # multi vs sole
        ms = [l for l in out15.splitlines() if l.startswith("| refusals where TWO OR MORE")]
        so = [l for l in out15.splitlines() if l.startswith("| refusals decided by exactly ONE")]
        check(ms and ms[0].count(": 1") == 3 and so and so[0].count(": 11") == 3,
              "one multi-rule refusal (swap+GPU) and eleven single-rule refusals, got %r / %r"
              % (ms, so))
        # (c) the two independent derivations of the swap-refusal set agree on this fixture set
        xc = [l for l in out15.splitlines() if l.startswith("| rule cross-check")]
        check(xc and xc[0].count("AGREES (2 = 2)") == 3,
              "the ratio-derived and reason-derived swap-refusal sets agree (2 = 2) at all three "
              "scopes, got %r" % xc)
        # the fail-closed cells say 0 when nothing is wrong
        fc = [l for l in out15.splitlines()
              if "cannot attribute" in l or "could not be parsed" in l]
        check(len(fc) == 2 and all(l.count(": 0") == 3 for l in fc),
              "the two fail-closed rows print 0 on a clean corpus, got %r" % fc)
        # (d) the counts move with the row set: at the 0105 cut the multi-rule refusal is outside
        rc15c, out15c = run(["--dir", d15, "--as-of", "%s-0105" % DAY, "--no-transition"])
        swap_c = [l for l in out15c.splitlines()
                  if l.startswith("| rule fired:") and "`swap-rate`" in l]
        multi_c = [l for l in out15c.splitlines() if l.startswith("| refusals where TWO OR MORE")]
        check(rc15c == 0 and swap_c and swap_c[0].count("1 fired, 1 sole") == 3
              and multi_c and multi_c[0].count(": 0") == 3,
              "the rule counts are scope-scoped: the 0105 cut holds one swap-rate refusal and no "
              "multi-rule refusal, got rc=%s %r / %r" % (rc15c, swap_c, multi_c))
        # gap classes are named by the gate's own phrase, not invented here
        gc = [l for l in out15.splitlines() if l.startswith("| input-gap")]
        check(gc and "0" in gc[0], "the gap-class row states its scopes, got %r" % gc)

        # (g) census v10 (tick 201): the state rule re-derived from the readings, its own
        # missing-key denominator, and the device-quiet complement with its denominator.
        sxc = [l for l in out15.splitlines() if l.startswith("| state-rule cross-check")]
        check(len(sxc) == 1 and sxc[0].count("AGREES (1 = 1)") == 3,
              "the engine-state-D set derived from the readings' own key equals the gate's reason "
              "set (1 = 1) at all three scopes, got %r" % sxc)
        sm = [l for l in out15.splitlines()
              if l.startswith("| readings with no `engine_state` key")]
        check(len(sm) == 1 and sm[0].count(": 0 of 13 readings") == 3,
              "the state cross-check prints its own missing-key denominator (0 of 13 here), got %r"
              % sm)
        dq = [l for l in out15.splitlines() if l.startswith("| state-D refusals on a device")]
        check(len(dq) == 1 and dq[0].count("1 of 1 state-D refusals carry a device window "
                                           "(1 named by the gate)") == 3,
              "the one state-D refusal sits on a quiet device (0.1 MiB/s at whole-disk scope) and "
              "the row names its denominator at all three scopes, got %r" % dq)
        # the state-D refusal taken WITHOUT a device window must print no denominator rather than
        # join a smaller band silently — that is how a corpus figure starts describing only the
        # sampler era (tick 195's denominator rule applied to the new row).
        d15d = tempfile.mkdtemp(prefix="pubcensus-state-nodev-")
        try:
            write_fixtures(d15d, {"preflight-%s-0101.txt" % DAY: {},
                                  "preflight-%s-0102.txt" % DAY: {
                                      "engine_state": "D", "blk_read_mib_per_s": None,
                                      "blk_scope": None, "blk_top_reader": None}})
            rcd, outd = run(["--dir", d15d, "--no-transition"])
            dqd = [l for l in outd.splitlines() if l.startswith("| state-D refusals on a device")]
            sxd = [l for l in outd.splitlines() if l.startswith("| state-rule cross-check")]
            check(rcd == 0 and len(dqd) == 1
                  and dqd[0].count("no denominator — none of the 1 state-D refusals carries a "
                                   "device window") == 3
                  and sxd and sxd[0].count("AGREES (1 = 1)") == 3,
                  "a state-D refusal with no device window prints 'no denominator' and still "
                  "cross-checks, got rc=%s %r" % (rcd, dqd))
        finally:
            shutil.rmtree(d15d, ignore_errors=True)
        # the gate's state test is a SUBSTRING test (`Dl` fires). An equality test here would call
        # that refusal an unexplained rule firing, so the derived set must follow the same test.
        d15e = tempfile.mkdtemp(prefix="pubcensus-state-dl-")
        try:
            write_fixtures(d15e, {"preflight-%s-0101.txt" % DAY: {},
                                  "preflight-%s-0102.txt" % DAY: {"engine_state": "Dl"}})
            rce, oute = run(["--dir", d15e, "--no-transition"])
            sxe = [l for l in oute.splitlines() if l.startswith("| state-rule cross-check")]
            rule_e = [l for l in oute.splitlines()
                      if l.startswith("| rule fired:") and "`engine-state-D`" in l]
            check(rce == 0 and sxe and sxe[0].count("AGREES (1 = 1)") == 3
                  and rule_e and rule_e[0].count("1 fired, 1 sole") == 3,
                  "a `Dl` state counts as uninterruptible I/O exactly as the gate counts it and "
                  "both derivations still agree, got rc=%s %r / %r" % (rce, sxe, rule_e))
        finally:
            shutil.rmtree(d15e, ignore_errors=True)
    finally:
        shutil.rmtree(d15, ignore_errors=True)

    # (e)/(f) the non-vacuity controls, on a scratch scripts/ pair (the census resolves its gate
    # relative to its own directory, so both files travel together — tick 195's mechanism used on
    # purpose here). Mangle the GATE copy only; the tool copy is the real one.
    def scratch_pair(tag, mangle=None):
        d = tempfile.mkdtemp(prefix="pubcensus-guard-" + tag + "-")
        sd = os.path.join(d, "scripts")
        os.makedirs(sd)
        shutil.copy(TOOL, os.path.join(sd, os.path.basename(TOOL)))
        gsrc = open(GATE, encoding="utf-8").read()
        if mangle:
            for old, new in mangle:
                assert old in gsrc, "mangle anchor %r missing from the gate" % old
                gsrc = gsrc.replace(old, new, 1)
        with open(os.path.join(sd, "pub_preflight.py"), "w", encoding="utf-8") as fh:
            fh.write(gsrc)
        return d, sd

    dfix = tempfile.mkdtemp(prefix="pubcensus-guard-fixtures-")
    write_fixtures(dfix, {"preflight-%s-0101.txt" % DAY: {},
                          "preflight-%s-0104.txt" % DAY: {"gpu_util_pct": "100",
                                                          "gpu_util_mean_pct": "97.0",
                                                          "gpu_util_peak_pct": "100"}})
    try:
        # control: an UNMANGLED copy pair still runs, so (e)/(f) below cannot be the scratch
        # mechanism failing rather than the guard firing.
        d0, s0 = scratch_pair("clean")
        try:
            r0 = subprocess.run([sys.executable, os.path.join(s0, "pub_preflight_census.py"),
                                 "--dir", dfix, "--no-transition"], cwd=d0,
                                capture_output=True, text=True)
            check(r0.returncode == 0,
                  "an unmodified scratch copy of tool+gate still runs the census (rc=%s) — the "
                  "guard controls below are not the scratch mechanism failing: %s"
                  % (r0.returncode, (r0.stdout + r0.stderr)[:200]))
        finally:
            shutil.rmtree(d0, ignore_errors=True)
        # (e1) a renamed refusal reason: the anchor is gone, the census refuses to count rules
        d1, s1 = scratch_pair("rename", [("the shared brain was busy in the sample window",
                                          "the shared brain was BUSY in the sample window")])
        try:
            r1 = subprocess.run([sys.executable, os.path.join(s1, "pub_preflight_census.py"),
                                 "--dir", dfix, "--no-transition"], cwd=d1,
                                capture_output=True, text=True)
            o1 = r1.stdout + r1.stderr
            check(r1.returncode == 1 and "no longer matches the gate source" in o1
                  and "gpu-busy" in o1,
                  "a renamed gate refusal reason reddens the census before it counts anything "
                  "(rc=%s) %r" % (r1.returncode, o1[:220]))
        finally:
            shutil.rmtree(d1, ignore_errors=True)
        # (e2) a NEW refusal site the table has never heard of, every anchor still present
        d2, s2 = scratch_pair("site", [("    if int(vals[\"foreign_legs\"]) > 0:",
                                        "    reasons.append(\"a brand new refusal the census has "
                                        "never counted\")\n    if int(vals[\"foreign_legs\"]) > 0:")])
        try:
            r2 = subprocess.run([sys.executable, os.path.join(s2, "pub_preflight_census.py"),
                                 "--dir", dfix, "--no-transition"], cwd=d2,
                                capture_output=True, text=True)
            o2 = r2.stdout + r2.stderr
            check(r2.returncode == 1 and "builds 13 refusal reasons" in o2 and "knows 12" in o2,
                  "an added refusal site reddens the census even though no anchor moved (rc=%s) %r"
                  % (r2.returncode, o2[:220]))
        finally:
            shutil.rmtree(d2, ignore_errors=True)
        # (f) an UNMAPPABLE reason with the anchors kept (a comment carries the old phrase): the
        # census still runs, but it names the file and exits 4 instead of printing a rule count.
        d3, s3 = scratch_pair("unattr", [
            ("the shared brain was busy in the sample window",
             "brain busy, reworded by a gate edit \" + \"in the sample window"),
            ("    spin_blind = False",
             "    # the shared brain was busy  (this comment keeps the census anchor present so the "
             "guard "
             + chr(10) + "    # passes; the attribution below must still fail closed)"
             + chr(10) + "    spin_blind = False")])
        try:
            r3 = subprocess.run([sys.executable, os.path.join(s3, "pub_preflight_census.py"),
                                 "--dir", dfix, "--no-transition"], cwd=d3,
                                capture_output=True, text=True)
            o3 = r3.stdout + r3.stderr
            check(r3.returncode == 4 and "cannot attribute" in o3
                  and "preflight-%s-0104.txt" % DAY in o3,
                  "an unattributable refusal reason names its file and exits 4 (rc=%s) %r"
                  % (r3.returncode, o3[:260]))
        finally:
            shutil.rmtree(d3, ignore_errors=True)

        # (g1)/(g2) census v10 non-vacuity: the state cross-check must fire in BOTH directions.
        # Both manglings keep the gate's refusal-site count intact (the `reasons.append(` line
        # stays), so what reddens the census is the set comparison, not the rule-table guard.
        # (g1) the rule fires on a state the readings do not report as D (reason-only).
        dg1, sg1 = scratch_pair("state-reason", [
            ('    if "D" in vals["engine_state"]:',
             '    if "D" in vals["engine_state"] or "S" in vals["engine_state"]:')])
        try:
            rg1 = subprocess.run([sys.executable, os.path.join(sg1, "pub_preflight_census.py"),
                                  "--dir", dfix, "--no-transition"], cwd=dg1,
                                 capture_output=True, text=True)
            og1 = rg1.stdout + rg1.stderr
            check(rg1.returncode == 4
                  and "engine-state-D derived/refusal-reason sets disagree" in og1
                  and "DISAGREES" in og1 and "reason-only" in og1
                  and ("preflight-%s-0104.txt" % DAY) in og1,
                  "a state rule firing on a reading whose own key says S names the file and exits 4 "
                  "(rc=%s) %r" % (rg1.returncode, og1[:300]))
        finally:
            shutil.rmtree(dg1, ignore_errors=True)
        # (g2) the rule cannot fire at all while a D-carrying reading is still refused by another
        # rule (derived-only): the reading's own key says D, the gate says nothing about state.
        dfix2 = tempfile.mkdtemp(prefix="pubcensus-guard-stateoff-fx-")
        write_fixtures(dfix2, {"preflight-%s-0101.txt" % DAY: {},
                               "preflight-%s-0110.txt" % DAY: {
                                   "engine_state": "D",
                                   "swap_in_mib_per_s": "120.0", "swap_out_mib_per_s": "40.0",
                                   "swap_total_peak_mib_per_s": "300.0"}})
        dg2, sg2 = scratch_pair("state-off", [('    if "D" in vals["engine_state"]:',
                                               '    if "Z" in vals["engine_state"]:')])
        try:
            rg2 = subprocess.run([sys.executable, os.path.join(sg2, "pub_preflight_census.py"),
                                  "--dir", dfix2, "--no-transition"], cwd=dg2,
                                 capture_output=True, text=True)
            og2 = rg2.stdout + rg2.stderr
            check(rg2.returncode == 4
                  and "engine-state-D derived/refusal-reason sets disagree" in og2
                  and "DISAGREES" in og2 and "derived-only" in og2
                  and ("preflight-%s-0110.txt" % DAY) in og2,
                  "a state rule that cannot fire while the reading says D names the file and exits 4 "
                  "(rc=%s) %r" % (rg2.returncode, og2[:300]))
        finally:
            shutil.rmtree(dg2, ignore_errors=True)
            shutil.rmtree(dfix2, ignore_errors=True)
    finally:
        shutil.rmtree(dfix, ignore_errors=True)

    # ---- the preserved-shape sentence is GENERATED (tick 197: the typed one was two stamps short)
    src9 = open(TOOL, encoding="utf-8").read()
    mstamp = re.search(r"^CENSUS_STAMP = (\d+)", src9, re.M)
    check(mstamp is not None, "the census names its table shape as a single CENSUS_STAMP constant")
    stamp_n = int(mstamp.group(1)) if mstamp else 0
    spec9 = importlib.util.spec_from_file_location("pub_preflight_census_v9", TOOL)
    mod9 = importlib.util.module_from_spec(spec9)
    spec9.loader.exec_module(mod9)
    s_now = mod9.preserved_stamp_sentence(stamp_n)
    s_ahead = mod9.preserved_stamp_sentence(stamp_n + 3)
    check(all(("v%d" % i) in s_now for i in range(1, stamp_n))
          and ("v%d" % stamp_n) not in s_now.split("as written")[0],
          "the generated sentence covers v1..v%d for the current stamp, got %r" % (stamp_n - 1, s_now))
    check(all(("v%d" % i) in s_ahead for i in range(1, stamp_n + 3)),
          "the same sentence still covers every earlier shape three stamps from now, got %r" % s_ahead)
    check(re.search(r'^\s*L\.append\("v1, v2, v3, v4, v5 and v6', src9, re.M) is None,
          "no L.append prints the hand-typed enumeration that stopped at v6 (the phrase may appear "
          "in a comment naming the bug; printing it is what this forbids)")
    d16 = tempfile.mkdtemp(prefix="pubcensus-shape-")
    try:
        write_fixtures(d16)
        rc16, out16 = run(["--dir", d16, "--no-transition"])
        hdr16 = [l for l in out16.splitlines() if l.startswith("Census stamp:")]
        check(rc16 == 0 and len(hdr16) == 1
              and ("pub-preflight-census-v%d" % stamp_n) in hdr16[0]
              and s_now in hdr16[0],
              "the header stamps itself with the constant AND carries the generated preserved "
              "sentence, got rc=%s %r" % (rc16, hdr16[:1]))
    finally:
        shutil.rmtree(d16, ignore_errors=True)

    # ---- census v11 (2026-11-16): EVERY gate rule re-derived from the stored columns, plus the
    # engine generation that produced each pooled statistic ------------------------------------
    # Why this exists: the published refusal table named rules from the gate's reason STRING, which
    # says which rule the gate says fired but never which KEY and which CONSTANT produced it. On
    # 2026-11-14 the device ceiling moved (100.0 inflated -> 50.0 whole-disk) without changing the
    # SHAPE of any refusal line, so a table that only reads reason text cannot see that class at all.
    check(re.search(r"^CENSUS_STAMP = (1[1-9]|[2-9][0-9])$", src9, re.M) is not None,
          "the census stamp is at least 11: the rule derivations and the generation block added "
          "published rows, and any shape change must move the stamp rather than reuse the old one")
    for const in ("SWAP_FREE_MIN_MIB", "MEM_AVAILABLE_MIN_MIB", "IDLE_SPIN_PCPU", "BOOL_FALSE"):
        check(re.search(r"for key in \([^)]*%s" % const, src9, re.M | re.S) is not None,
              "gate_constants reads %s out of the GATE source — a derivation that hardcodes 200 or "
              "300 keeps printing AGREES after the gate moves the number" % const)
    check(re.search(r"def rule_label\(", src9) is not None,
          "rule ids are translated by one function rather than typed into a published label")
    check(mod9.gate_constants().get("SWAP_FREE_MIN_MIB") is not None
          and mod9.gate_constants().get("MEM_AVAILABLE_MIN_MIB") is not None
          and mod9.gate_constants().get("IDLE_SPIN_PCPU") is not None,
          "gate_constants returns the three thresholds the per-rule derivations compare against")
    check("false" in mod9.gate_constants()["BOOL_FALSE"]
          and "true" in mod9.gate_constants()["BOOL_TRUE"],
          "the boolean vocabulary is the GATE's own, so a flag spelled differently in the two tools "
          "becomes a loud census failure instead of a rule silently never firing")

    # ---- census v12 (2026-11-16, tick 204): footprint COVERAGE vs INFORMATION ------------------
    # Why: the arming counter counts launchable windows CARRYING `engine_vmswap_mib`, and a window
    # reading 0 MiB carries it. On live bytes the newest generation answered 0 in every window it
    # produced, so the counter was buying coverage while the statistic that sets a footprint ceiling
    # was never observed on the live process. Coverage and information now have separate cells.
    check(stamp_n >= 12,
          "census v12 moved the stamp: the footprint block publishes the non-zero/zero split and an "
          "informative-coverage state word (stamp reads %d)" % stamp_n)
    check(re.search(r"def footprint_info_text\(", src9) is not None,
          "the coverage-vs-information verdict is a function, not prose beside the counter")
    for key in ("go_nonzero", "go_zero", "nogo_nonzero", "nogo_zero", "fp_go_nz", "fp_no_nz"):
        check(key in src9, "footprint coverage is counted by %s out of the stored column, not "
                           "inferred from the maximum" % key)

    # the coverage guard runs BOTH ways: a gate rule with no derivation, and a derivation with no
    # gate rule, are both published fiction
    probs11 = mod9.refusal_rule_guard()
    check(probs11 == [], "the rule table and the derivations cover the gate source at current "
                         "bytes, got %r" % (probs11,))
    keep_derived = list(mod9.DERIVED_RULES)
    try:
        mod9.DERIVED_RULES = [r for r in keep_derived if r != "swap-free-low"]
        probs11b = mod9.refusal_rule_guard()
        check(any("no derivation in the census" in p for p in probs11b),
              "dropping one rule's derivation must redden the census (the guard is two-way), got %r"
              % (probs11b,))
        mod9.DERIVED_RULES = keep_derived + ["rule-the-gate-does-not-have"]
        probs11c = mod9.refusal_rule_guard()
        check(any("does not know" in p for p in probs11c),
              "a derivation for a rule the gate no longer has must redden the census, got %r"
              % (probs11c,))
    finally:
        mod9.DERIVED_RULES = keep_derived
    check(set(mod9.DERIVED_RULES) | set(mod9.ALREADY_DERIVED_RULES)
          == {r for r, _k, _a, _s in mod9.REFUSAL_RULES},
          "every rule in the gate table has a published derivation at this stamp — the day a gate "
          "edit adds a refusal site, the coverage guard stops the census until it joins")

    # the predicates themselves, off-corpus: each must fire on its own columns and refuse to fire
    # when its premise is missing, with the gate's live constants (never literals here)
    consts11 = mod9.gate_constants()
    base_rf = dict(health_code=200.0, loaded="true", serve_procs=1.0, swap_free=57507.0,
                   mem_avail=20278.0, blk=0.1, pcpu=9.6, gpu_inst=0.0, gpu_mean=0.0, foreign=0.0)

    def fired11(over, scope="whole-disk"):
        rf = dict(base_rf)
        rf.update(over)
        return mod9.derived_rule_set(rf, scope, consts11)[0]

    check("device-read" in fired11({"blk": 60.0}),
          "60 MiB/s on a whole-disk reading fires the device rule against the gate's 50.0 ceiling")
    check("device-read" not in fired11({"blk": 60.0}, scope="unmarked"),
          "the same number on an UNMARKED (pre-scope) reading is judged by the old 100.0 ceiling — "
          "the scale fix must not retroactively refuse published bytes")
    check("device-read" in fired11({"blk": 110.0}, scope="unmarked"),
          "an unmarked reading still fires above the old 100.0 ceiling")
    check("idle-spin" in fired11({"pcpu": 400.0}),
          "high engine CPU with a 0%% window mean fires the idle-spin rule")
    check("idle-spin" not in fired11({"pcpu": 400.0, "gpu_mean": 55.0}),
          "the idle-spin premise is the WINDOW mean, so a zero instantaneous sample inside a busy "
          "window must not fire (measured live 2026-11-14 21:50)")
    check(fired11({"gpu_mean": float(consts11["GPU_UTIL_MAX_MEAN_PCT"])}) == {"gpu-busy"},
          "the GPU-busy comparison uses the gate's ceiling as printed, boundary included")
    check("swap-free-low" in fired11({"swap_free": consts11["SWAP_FREE_MIN_MIB"] - 1})
          and "swap-free-low" not in fired11({"swap_free": consts11["SWAP_FREE_MIN_MIB"]}),
          "the swap-free floor is strict-inequality at the gate's own constant")
    check("mem-available-low" in fired11({"mem_avail": consts11["MEM_AVAILABLE_MIN_MIB"] - 1}),
          "the memory floor is derived from the gate constant, not from a restated number")
    check(fired11({"foreign": 1.0}) == {"foreign-legs"},
          "one foreign leg on the endpoint is a refusal the census can derive")
    check(fired11({"loaded": "false"}) == {"health-loaded-false"}
          and fired11({"loaded": "true"}) == set(),
          "the loaded flag is read with the gate's vocabulary in both directions")
    check(fired11({"serve_procs": 0.0}) == {"engine-process-absent"}
          and fired11({"health_code": 503.0}) == {"health-code-not-200"},
          "the process and health rules derive from their own keys")
    rf11 = dict(base_rf)
    rf11["mem_avail"] = None
    check("mem-available-low" not in mod9.derived_rule_set(rf11, "whole-disk", consts11)[0]
          and "mem-available-low" in mod9.derived_rule_set(rf11, "whole-disk", consts11)[1],
          "a missing key is NOT an innocent non-firing: the rule lands in the not-evaluable set so "
          "the published cell shows the shrunken denominator")

    # end to end: one refusal per rule, each named by the gate's OWN reason line. The derivation and
    # the reason set must agree on all nine, and an unattributable reason would exit 4 instead.
    d11 = tempfile.mkdtemp(prefix="pubcensus-v11-")
    try:
        per_rule = {
            "preflight-20300101-0101.txt": {"health_code": "503"},
            "preflight-20300101-0102.txt": {"health_loaded": "false"},
            "preflight-20300101-0103.txt": {"engine_serve_procs": "0"},
            # swap_free_mib and mem_available_mib are INT keys in the gate's parse: "8.0" is an
            # unreadable number there and the reading answers an input gap, not a refusal. And the
            # swap columns must still cross-foot (used + free == total within 64 MiB) or the gate
            # refuses to judge the reading at all — the producer column mix-up guard. An integer
            # literal with a consistent pair is what the producer emits.
            "preflight-20300101-0104.txt": {"swap_free_mib": "8", "swap_used_mib": "65527"},
            "preflight-20300101-0105.txt": {"mem_available_mib": "100"},
            "preflight-20300101-0106.txt": {"blk_read_mib_per_s": "60.0"},
            "preflight-20300101-0107.txt": {"engine_pcpu": "400.0"},
            "preflight-20300101-0108.txt": {"gpu_util_mean_pct": "97.0", "gpu_util_peak_pct": "100"},
            "preflight-20300101-0109.txt": {"foreign_legs": "2"},
        }
        write_fixtures(d11, per_rule)
        rc11, out11 = run(["--dir", d11, "--no-transition", "--as-of", "20300101-1200"])
        agree = [l for l in out11.splitlines()
                 if l.startswith("| rule re-derived from the reading's own columns")]
        check(rc11 == 0 and len(agree) == 9,
              "the nine derived rule cells print for a corpus with one refusal per rule "
              "(rc=%s cells=%d) %r" % (rc11, len(agree), out11[-500:]))
        check(all(": AGREES (" in l for l in agree),
              "with the gate's own reason lines the derivations must AGREE rule by rule, got %r"
              % [l.split(" | ")[-1][:120] for l in agree if ": AGREES (" not in l])
        check(sum(1 for l in agree if ": AGREES (1 = 1;" in l) == 9,
              "one refusal per rule means nine cells each with exactly one firing on both sides; a "
              "cell at (0 = 0) in this fixture set means the rule never fired and the cross-check "
              "proved nothing about it, got %r"
              % [l.split(" | ")[-1][:60] for l in agree if ": AGREES (1 = 1;" not in l])
        check(all("0 of 9 attributed refusals cannot be evaluated" in l for l in agree),
              "each cell names its not-evaluable count so an AGREES over a shrunken denominator is "
              "never read as full agreement, got %r"
              % [l.split(" | ")[-1][:120] for l in agree
                 if "0 of 9 attributed" not in l])
        check("of 11 (v9 swap band, v10 engine state, v11 the other 9)" in out11,
              "the coverage row counts the rules re-derived and names the families that got here "
              "when, got %r" % [l for l in out11.splitlines() if "the other 9" in l][:1])
    finally:
        shutil.rmtree(d11, ignore_errors=True)

    # engine generation: the producer names the pid it sampled in a COMMENT line and the gate's
    # parser skips comments, so a footprint maximum from a retired process used to look like a
    # property of the endpoint. Three states, all computed: STALE, CURRENT, no denominator.
    def with_pid_comment(path, pid):
        """Prepend the producer's engine-pid comment to a fixture.

        Written as a helper because the obvious one-liner is a trap:
        `open(p, "w").write("# ...\\n" + open(p).read())` truncates the file BEFORE the read runs, so
        the fixture ends up empty and the gate answers an input gap about a corpus with no keys — a
        fixture bug that reads exactly like a tool bug.
        """
        body = open(path, encoding="utf-8").read()
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# engine pid=%s\n" % pid + body)

    d12 = tempfile.mkdtemp(prefix="pubcensus-gen-")
    try:
        # `engine_vmswap_mib` is the footprint key the dry-run ceiling is drawn from, so the
        # generation fixtures must carry it: without it the row answers `no denominator`, which is
        # the honest answer for the real pre-2026-11-14 corpus and a useless fixture.
        write_fixtures(d12, {"preflight-20300101-0201.txt": {"engine_vmswap_mib": "9000"}})
        with_pid_comment(os.path.join(d12, "preflight-20300101-0201.txt"), "1000")
        write_fixtures(d12, {"preflight-20300101-0202.txt": {"engine_vmswap_mib": "3000"}})
        with_pid_comment(os.path.join(d12, "preflight-20300101-0202.txt"), "2000")
        write_fixtures(d12, {"preflight-20300101-0203.txt": {"engine_vmswap_mib": "3100"}})
        rc12, out12 = run(["--dir", d12, "--no-transition", "--as-of", "20300101-1200"])
        gl = [l for l in out12.splitlines() if "engine generations sampled in this scope" in l]
        sl = [l for l in out12.splitlines() if "dry-run ceiling's binding value" in l]
        check(rc12 == 0 and len(gl) == 1 and "2 generations over 2 readings" in gl[0],
              "the block counts distinct sampled pids before listing them (rc=%s) %r"
              % (rc12, gl[:1]))
        check("1 of 3 readings" in "".join(gl + [l for l in out12.splitlines()
                                                 if "carries no engine pid" in l]),
              "the reading with no pid comment is counted as unattributable, not folded into a "
              "generation, got %r" % [l for l in out12.splitlines() if "no engine pid" in l][:1])
        check(sl and "GENERATION-STALE" in sl[0] and "pid 1000" in sl[0] and "pid 2000" in sl[0],
              "the footprint maximum belongs to a pid the newest reading no longer samples, and the "
              "row must say so rather than publish the number bare: %r" % (sl[:1],))
        check("launchable windows and refused windows on the same engine generation" in out12,
              "the table prints whether the launchable and refused statistics describe one process")
    finally:
        shutil.rmtree(d12, ignore_errors=True)
    d13 = tempfile.mkdtemp(prefix="pubcensus-gen-cur-")
    try:
        for hh in ("0301", "0302"):
            path = os.path.join(d13, "preflight-20300101-%s.txt" % hh)
            write_fixtures(d13, {os.path.basename(path): {"engine_vmswap_mib": "9000"}})
            with_pid_comment(path, "1000")
        rc13, out13 = run(["--dir", d13, "--no-transition", "--as-of", "20300101-1200"])
        check(rc13 == 0 and "CURRENT (the newest reading in this scope sampled the same pid)" in out13,
              "one live generation reads CURRENT, so the stale word is computed and not a fixed "
              "sentence (rc=%s)" % rc13)
    finally:
        shutil.rmtree(d13, ignore_errors=True)
    d14 = tempfile.mkdtemp(prefix="pubcensus-gen-none-")
    try:
        write_fixtures(d14, {"preflight-20300101-0401.txt": {}})
        rc14, out14 = run(["--dir", d14, "--no-transition", "--as-of", "20300101-1200"])
        check(rc14 == 0
              and "no denominator, no reading in this scope carries an engine pid" in out14,
              "a corpus with no producer comment prints no denominator, never 0 generations "
              "(rc=%s)" % rc14)
    finally:
        shutil.rmtree(d14, ignore_errors=True)

    # coverage vs INFORMATION in the footprint arming counter (census v12, 2026-11-16, tick 204): a
    # window that answers `engine_vmswap_mib=0` carries the key and feeds the counter, but it cannot
    # set a ceiling. Three states, all computed, and a zero draw must STAY in the coverage count —
    # dropping it would be the opposite bug (an armed rule that never saw the statistic).
    d15 = tempfile.mkdtemp(prefix="pubcensus-fpinfo-zero-")
    try:
        for hh in ("0501", "0502"):
            path = os.path.join(d15, "preflight-20300101-%s.txt" % hh)
            write_fixtures(d15, {os.path.basename(path): {"engine_vmswap_mib": "0"}})
            with_pid_comment(path, "5000")
        rc15, out15 = run(["--dir", d15, "--no-transition", "--as-of", "20300101-1200"])
        split = [l for l in out15.splitlines() if "of those launchable draws: non-zero footprint" in l]
        rsplit = [l for l in out15.splitlines() if "same split on the refused side" in l]
        state = [l for l in out15.splitlines() if "informative-coverage state" in l]
        genrow = [l for l in out15.splitlines() if "ever recorded a footprint above 0 MiB" in l]
        arm = [l for l in out15.splitlines() if "footprint arming counter" in l]
        check(rc15 == 0 and len(split) == 1 and "0 non-zero / 2 zero" in split[0],
              "the arming counter prints its coverage split, got rc=%s %r" % (rc15, split[:1]))
        check(len(rsplit) == 1 and "0 non-zero / 0 zero" in rsplit[0],
              "the refused side prints its own split instead of inheriting the launchable one: %r"
              % (rsplit[:1],))
        check(state and "ALL-ZERO" in state[0] and "> 0 MiB" in state[0],
              "an all-zero launchable group must not read as a measured ceiling: %r" % (state[:1],))
        check(genrow and "ZERO-FOOTPRINT GENERATION" in genrow[0],
              "a newest generation that only ever answers 0 MiB is named as an unexercised failure "
              "mode: %r" % (genrow[:1],))
        check(int_cell("\n".join(arm), "footprint arming counter (launchable windows carrying it)")
              == 2, "the two zero draws still count as coverage — the fix splits cells, it does not "
                    "delete measurements, got %r" % (arm[:1],))
    finally:
        shutil.rmtree(d15, ignore_errors=True)
    d16 = tempfile.mkdtemp(prefix="pubcensus-fpinfo-dom-")
    try:
        for hh, v in (("0601", "0"), ("0602", "0"), ("0603", "9000")):
            path = os.path.join(d16, "preflight-20300101-%s.txt" % hh)
            write_fixtures(d16, {os.path.basename(path): {"engine_vmswap_mib": v}})
            with_pid_comment(path, "6000")
        rc16, out16 = run(["--dir", d16, "--no-transition", "--as-of", "20300101-1200"])
        st16 = [l for l in out16.splitlines() if "informative-coverage state" in l]
        gen16 = [l for l in out16.splitlines() if "ever recorded a footprint above 0 MiB" in l]
        check(rc16 == 0 and st16 and "ZERO-DRAW-DOMINATED" in st16[0]
              and "1 informative draw" in st16[0] and "9000 MiB" in st16[0],
              "a launchable group dominated by zeros states that the ceiling rests on one draw: %r"
              % (st16[:1],))
        check(gen16 and "ZERO-FOOTPRINT" not in gen16[0] and "is exercised" in gen16[0],
              "a generation that HAS swapped somewhere must not carry the unexercised word: %r"
              % (gen16[:1],))
    finally:
        shutil.rmtree(d16, ignore_errors=True)
    d17 = tempfile.mkdtemp(prefix="pubcensus-fpinfo-inf-")
    try:
        for hh, v in (("0701", "0"), ("0702", "9000")):
            path = os.path.join(d17, "preflight-20300101-%s.txt" % hh)
            write_fixtures(d17, {os.path.basename(path): {"engine_vmswap_mib": v}})
            with_pid_comment(path, "7000")
        rc17, out17 = run(["--dir", d17, "--no-transition", "--as-of", "20300101-1200"])
        st17 = [l for l in out17.splitlines() if "informative-coverage state" in l]
        det17 = [l for l in out17.splitlines() if "non-zero footprint draws" in l]
        check(rc17 == 0 and st17 and "INFORMATIVE" in st17[0]
              and "ZERO-DRAW" not in st17[0] and "ALL-ZERO" not in st17[0],
              "half-informative coverage reads INFORMATIVE, not a warning: %r" % (st17[:1],))
        check(det17 and "non-zero footprint draws 1 of 2 launchable / 0 of 0 refused" in det17[0],
              "the per-generation detail prints the informative/coverage pair, got %r" % (det17[:1],))
    finally:
        shutil.rmtree(d17, ignore_errors=True)

    # ---- census v13 (2026-11-16, tick 205): the two FREE columns ------------------------------
    # Why: every rule this table banded was a RATE over one 6 s window, while the gate's one
    # threshold in force that is a STATE — `MEM_AVAILABLE_MIN_MIB`, rule `mem-available-low` — was
    # never quoted with a distance to it, and `engine_rss_mib` was never differenced at all. On live
    # bytes at the 16.11 12:40 cut the live generation had five consecutive decreasing MemAvailable
    # draws (6618 → 4938 MiB, 658.8 MiB/h) with swap-in-use flat at 65 MiB, while the generation
    # before the restart held 16-17 GiB of swap in use and 17-21 GiB of headroom: the two free
    # columns moved in OPPOSITE directions across that restart, which is also why the morning's
    # page-in storms stopped. A table that bands only rates cannot see that transition at all.
    check(stamp_n >= 13,
          "census v13 moved the stamp: MemAvailable / swap-in-use / engine-RSS are published as a "
          "per-generation state with a computed trend (stamp reads %d)" % stamp_n)
    check(re.search(r"def memory_headroom_text\(", src9) is not None,
          "the headroom block is a function over the same scopes, not prose beside the table")

    TREND_LABEL = ("headroom trend of the newest generation, and what it projects against that floor")
    ATTR_LABEL = ("how much of the newest generation's headroom change its own RSS change explains")
    FLIP_LABEL = ("do the two free columns move in OPPOSITE directions when the engine generation "
                  "changes?")
    FLOOR_LABEL = "the newest reading's headroom against that floor"
    CLOSE_LABEL = "closest approach to that floor in this scope"
    TRAJ_LABEL = ("MemAvailable / swap-in-use / engine-RSS trajectory per engine generation "
                  "(the free columns belong to a process, not to the box)")
    BAD_LABEL = ("readings whose `engine_rss_mib` exceeds the box's own `mem_total_mib` "
                 "(an impossible field value: reported, named, and never used in arithmetic)")

    def with_mem(path, pid, avail=None, rss=None, used=None):
        """Fixture rewritten with explicit free-column values plus the producer's pid comment."""
        keep = []
        for ln in open(path, encoding="utf-8").read().splitlines():
            if ln.split("=", 1)[0] in ("mem_available_mib", "engine_rss_mib", "swap_used_mib"):
                continue
            keep.append(ln)
        for k, v in (("mem_available_mib", avail), ("engine_rss_mib", rss), ("swap_used_mib", used)):
            if v is not None:
                keep.append("%s=%s" % (k, v))
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("# engine pid=%s\n" % pid + "\n".join(keep) + "\n")

    def parsed_row(md, label):
        """The printed value of one label, parsed as a PAIR (v12's lesson: a cell whose text grew is
        invisible to a line count, and every cell in this block is long)."""
        for ln in md.splitlines():
            m = re.match(r"^\| (.*?) \| (.*?) \|$", ln)
            if m and m.group(1) == label:
                return m.group(2)
        return ""

    d18 = tempfile.mkdtemp(prefix="pubcensus-headroom-")
    try:
        def memrun(tag, spec):
            """spec: list of (pid, mem_available_mib, engine_rss_mib, swap_used_mib)."""
            d18x = os.path.join(d18, tag)
            os.mkdir(d18x)
            for i, (pid, av, rss, used) in enumerate(spec):
                name = "preflight-%s-03%02d.txt" % (DAY, i)
                write_fixtures(d18x, {name: {}})
                with_mem(os.path.join(d18x, name), pid, av, rss, used)
            rc18, out18 = run(["--dir", d18x, "--as-of", "%s-0400" % DAY, "--no-transition"])
            check(rc18 == 0, "headroom fixtures exit 0 (%s: rc=%s)" % (tag, rc18))
            return out18

        # (a) monotone fall, attributed to the sampled process, with its projection
        out18 = memrun("a", [("7000", 6618, 52711, 65), ("7000", 6200, 53100, 65),
                             ("7000", 5800, 53500, 65), ("7000", 5400, 54000, 65),
                             ("7000", 4938, 54401, 65)])
        t18 = parsed_row(out18, TREND_LABEL)
        check("PROJECTION" in t18 and "not a promise" in t18,
              "a five-draw monotone fall prints a projection AND the word projection in the same "
              "cell, got %r" % t18[:200])
        a18 = parsed_row(out18, ATTR_LABEL)
        check("ATTRIBUTED TO THE SAMPLED ENGINE" in a18 and "UNATTRIBUTED" not in a18,
              "a headroom fall matched by engine-RSS growth is attributed to the sampled engine, "
              "got %r" % a18[:220])
        c18 = parsed_row(out18, CLOSE_LABEL)
        check("THE MINIMUM IS THE NEWEST DRAW" in c18,
              "the scope minimum sitting on the newest draw is called falling, not resting, "
              "got %r" % c18[:200])
        tr18 = parsed_row(out18, TRAJ_LABEL)
        check("monotonically down over the last 5 draw(s)" in tr18,
              "the trajectory row states the trailing monotone run, which is what a headroom "
              "decision follows, got %r" % tr18[:260])

        # (b) NON-VACUITY of the projection: the same block on a rising series must not project
        out19 = memrun("b", [("7000", 4938, 54401, 65), ("7000", 5400, 54000, 65),
                             ("7000", 5800, 53500, 65), ("7000", 6200, 53100, 65),
                             ("7000", 6618, 52711, 65)])
        t19 = parsed_row(out19, TREND_LABEL)
        check("PROJECTION" not in t19 and "NOT DECREASING" in t19,
              "the same cell on a rising series says NOT DECREASING and projects nothing — the "
              "projection is arithmetic over the printed draws, not a template, got %r" % t19[:200])
        check("no attribution owed" in parsed_row(out19, ATTR_LABEL),
              "headroom that did not fall owes no attribution instead of printing a 0%% ratio, "
              "got %r" % parsed_row(out19, ATTR_LABEL)[:220])

        # (c) a fall the sampled engine does NOT explain is named UNATTRIBUTED
        out20 = memrun("c", [("7000", 20000, 57374, 8028), ("7000", 16000, 57374, 8028),
                             ("7000", 12000, 57374, 8028), ("7000", 9000, 57374, 8028)])
        a20 = parsed_row(out20, ATTR_LABEL)
        check("UNATTRIBUTED" in a20 and "does not sample" in a20,
              "11 GiB of headroom gone with an engine RSS that never moved is called UNATTRIBUTED: "
              "the block refuses to charge the sampled process for memory it did not take, got %r"
              % a20[:240])

        # (d) below the floor: the census quotes the GATE's constant and the gate's own verdict
        out21 = memrun("d", [("7000", 3000, 57374, 8028), ("7000", 1900, 57374, 8028)])
        fl21 = parsed_row(out21, FLOOR_LABEL)
        floor13 = mod9.gate_constants()["MEM_AVAILABLE_MIN_MIB"]
        check("BELOW the floor" in fl21 and str(int(floor13)) in fl21,
              "a 1900 MiB reading against the gate's own %s MiB floor prints BELOW the floor naming "
              "the gate's constant, not a census literal, got %r" % (floor13, fl21[:240]))
        check("this reading's verdict: NO-GO" in fl21,
              "the same cell carries the verdict the gate actually gave for that reading, got %r"
              % fl21[:300])
        fired21 = parsed_row(out21, "rule fired: `mem-available-low`")
        check(fired21.startswith("DAY `20300101`: 1 fired") or "mem-available-low` (gate reason" in out21,
              "the rule-fire table agrees with the headroom block about which rule tripped (row=%r)"
              % fired21[:160])

        # (e) the regime flip: swap empties AND headroom falls across a restart
        out22 = memrun("e", [("8000", 19297, 56654, 16839), ("8000", 18900, 56700, 16800),
                             ("9000", 6618, 52711, 65), ("9000", 6100, 53000, 65)])
        fp22 = parsed_row(out22, FLIP_LABEL)
        check("REGIME FLIP" in fp22 and "swap in use fell" in fp22 and "MemAvailable fell" in fp22,
              "across a restart where swap emptied while headroom fell the cell names BOTH "
              "directions in one sentence — the transition the rate rules go blind to, got %r"
              % fp22[:300])
        tr22 = parsed_row(out22, TRAJ_LABEL)
        check("pid 8000" in tr22 and "pid 9000" in tr22,
              "both generations of the flip corpus appear in the trajectory row, got %r" % tr22[:240])

        # (f) NON-VACUITY of the flip row: one generation gives NO denominator, not "no flip"
        out23 = memrun("f", [("8000", 19297, 56654, 16839), ("8000", 18900, 56700, 16800)])
        fp23 = parsed_row(out23, FLIP_LABEL)
        check("no denominator" in fp23 and "REGIME FLIP" not in fp23,
              "one generation prints NO denominator for the flip row rather than 'no flip observed', "
              "which would read as evidence that flips do not happen, got %r" % fp23[:200])

        # (g) an impossible field value is named and excluded, never averaged
        out24 = memrun("g", [("7000", 6618, 58929928, 65), ("7000", 4938, 54401, 65)])
        bd24 = parsed_row(out24, BAD_LABEL)
        check("preflight-20300101-0300.txt" in bd24 and "58929928" in bd24,
              "an engine RSS larger than the machine names the file and the value instead of letting "
              "it enter a ratio, got %r" % bd24[:240])
        check("no denominator" in parsed_row(out24, ATTR_LABEL),
              "with the impossible draw excluded the attribution row holds 1 usable draw and says NO "
              "DENOMINATOR rather than dividing by a KiB value inside a MiB column, got %r"
              % parsed_row(out24, ATTR_LABEL)[:220])

        # (h) two points are not a trend, even a steep one
        out25 = memrun("h", [("7000", 6618, 52711, 65), ("7000", 4938, 54401, 65)])
        t25 = parsed_row(out25, TREND_LABEL)
        check("TOO FEW MONOTONE DRAWS" in t25 and "PROJECTION" not in t25,
              "two decreasing draws refuse to project — the resolution rule applied to headroom, "
              "got %r" % t25[:220])

        # (i) census v14: a projection counted in READINGS is divided by a SAMPLING CADENCE, so
        # that cadence owes a denominator. Fixture reproduces the live 2026-11-16 13:37 draw set:
        # eight decreasing draws losing 1 889 MiB over 210 min at intervals 28/39/35/51/9/16/32.
        def memrun_timed(tag, spec, minutes, as_of):
            """Same fixture writer, but each draw gets an explicit minute offset from 03:00."""
            d18x = os.path.join(d18, tag)
            os.mkdir(d18x)
            for off, (pid, av, rss, used) in zip(minutes, spec):
                hh, mm = divmod(3 * 60 + off, 60)
                name = "preflight-%s-%02d%02d.txt" % (DAY, hh, mm)
                write_fixtures(d18x, {name: {}})
                with_mem(os.path.join(d18x, name), pid, av, rss, used)
            rc18, out18 = run(["--dir", d18x, "--as-of", "%s-%02d%02d" % (DAY, *divmod(3 * 60 + as_of, 60)),
                               "--no-transition"])
            check(rc18 == 0, "timed headroom fixtures exit 0 (%s: rc=%s)" % (tag, rc18))
            return out18

        fall = [("7000", 6618, 52711, 65), ("7000", 6200, 53100, 65),
                ("7000", 5800, 53500, 65), ("7000", 5400, 54000, 65),
                ("7000", 5000, 54300, 65), ("7000", 4938, 54401, 65),
                ("7000", 4860, 54500, 65), ("7000", 4729, 54597, 65)]
        out26 = memrun_timed("i", fall, [0, 28, 67, 102, 153, 162, 178, 210], 215)
        t26 = parsed_row(out26, TREND_LABEL)
        check("PROJECTION" in t26 and "in READINGS 5-33 further draws" in t26,
              "a monotone fall sampled at 9-51 min intervals states its reading count as the "
              "BAND those intervals support (298 min / 51 = 5, / 9 = 33), got %r" % t26[:300])
        check("7 interval(s), 9-51 min, mean 30.0" in t26,
              "the band cell prints its own denominator: interval count, min-max and the mean the "
              "mean-only version divided by, got %r" % t26[:300])
        check("printed the single number 9" in t26 and "refutes by 5.7x" in t26,
              "the row names the number the mean-only conversion printed rather than silently "
              "replacing it, got %r" % t26[:300])

        # (j) NON-VACUITY: identical values at a UNIFORM cadence must collapse back to one count.
        # Same eight draws, same 1 889 MiB over 210 min — only the intervals change — so the band
        # above is provably arithmetic over the cadence and not a template the row always prints.
        out27 = memrun_timed("j", fall, [0, 30, 60, 90, 120, 150, 180, 210], 215)
        t27 = parsed_row(out27, TREND_LABEL)
        check("in READINGS ≈9 further draws" in t27
              and "a single count being admissible at this cadence" in t27
              and "because the run's own intervals span" not in t27,
              "the same values at a uniform 30 min cadence print ONE count (298 // 30 = 9, exactly "
              "the number v13 printed here) instead of a band, got %r" % t27[:300])
        check("7 interval(s), 30-30 min, mean 30.0" in t27,
              "even the collapsed count names its interval denominator, got %r" % t27[:260])

        # (k) the zero-interval guard: two draws sharing a timestamp must never reach a
        # denominator. File names cannot collide, so the branch is unreachable by fixture; the
        # helper that feeds it is pinned directly instead of left as decorative code.
        check(mod9._positive_intervals([]) == [],
              "_positive_intervals over zero rows is an empty list, never a crash")

        class _Gap:
            def __init__(self, seconds):
                self._s = seconds

            def total_seconds(self):
                return float(self._s)

        class _TS:
            def __init__(self, m):
                self._m = m

            def __sub__(self, other):
                return _Gap((self._m - other._m) * 60)

        rows_k = [{"ts": _TS(30)}, {"ts": _TS(30)}, {"ts": _TS(27)}, {"ts": _TS(34)}]
        gaps_k = mod9._positive_intervals(rows_k)
        check(gaps_k == [7.0],
              "_positive_intervals drops zero and negative gaps instead of letting them into a "
              "division (the fail-closed branch that makes the NO-reading-count cell reachable), "
              "got %r" % gaps_k)
        check("NO reading" in src9 and "MEM_INTERVAL_FLAT_RATIO" in src9,
              "the fail-closed cell and the flat-cadence threshold both exist in the tool, not only "
              "in this test's expectations")
        check('"about %d further readings"' not in src9,
              "v13's mean-only reading count is gone from the source, so it cannot return by an "
              "edit beside this one")
    finally:
        shutil.rmtree(d18, ignore_errors=True)

    # the census must not be able to reach the endpoint by accident: no ssh, no sockets
    src = open(TOOL, encoding="utf-8").read()
    for bad in ("ssh ", "requests", "urllib", "socket."):
        check(bad not in src, "the census tool contains no %s seam" % bad)
    check("pub_preflight.py" in src, "the census drives the real gate, not a copy of its rules")

    if FAILED:
        print("PUB PREFLIGHT CENSUS TEST: %d/%d FAILED:" % (len(FAILED), CHECKS))
        for f in FAILED:
            print("  - " + f)
        return 1
    print("PUB PREFLIGHT CENSUS TEST: %d/%d checks green" % (CHECKS, CHECKS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
