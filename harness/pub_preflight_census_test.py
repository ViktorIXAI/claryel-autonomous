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
        check(rcd == 0 and len(hdr) == 1 and "pub-preflight-census-v7" in hdr[0],
              "the census names its v7 shape, got rc=%s %r" % (rcd, hdr[:1]))
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
        c_zone = cell(outd, "day dead zone, highest GO draw to lowest swap-rule refusal")
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
        c_z2 = cell(outz, "day dead zone, highest GO draw to lowest swap-rule refusal")
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
        check("NO-DATA" in (cell(outy, "day dead zone, highest GO draw to lowest swap-rule refusal")
                            or ""),
              "a day with no GO draws has no dead zone to state, got %r"
              % cell(outy, "day dead zone, highest GO draw to lowest swap-rule refusal"))
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
        check(rcs == 0 and len(hdrs) == 1 and "pub-preflight-census-v7" in hdrs[0],
              "the census names its v7 shape, got rc=%s %r" % (rcs, hdrs[:1]))
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
        cz_day = cell(outs, "dead zone, DAY `20300102`")
        cz_win = cell(outs, "dead zone, last 24 h")
        check(cz_day == "NO ZONE at this scope (no launchable draw or no swap-rule refusal with a "
                        "parseable window)",
              "the as-of day has no launchable draw, so it cannot state a dead zone at all, got %r"
              % cz_day)
        check(cz_win == "EMPTY (0 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)",
              "the window scope states the zone the day scope cannot, got %r" % cz_win)
        c_state = cell(outs, "dead-zone scope state (computed, never asserted)")
        check(c_state.startswith("PARTLY UNMEASURABLE — a zone exists only at last 24 h, whole "
                                 "corpus") and "no zone at DAY `20300102`" in c_state,
              "a scope with no zone is named, not silently averaged away, got %r" % c_state)
        # non-vacuity A: one launchable draw ON the as-of day makes all three scopes agree
        scope_a = dict(SCOPE)
        scope_a["preflight-20300102-0003.txt"] = {}
        rca, outa = run_fx(scope_a)
        check(rca == 0 and cell(outa, "dead-zone scope state (computed, never asserted)")
              .startswith("IDENTICAL AT ALL THREE SCOPES (bounds 0.01-3.00 x, width 2.995 x "
                          "(59.9 MiB/s), EMPTY (0 inside))"),
              "the scope state follows the row sets; a single GO on the as-of day collapses the "
              "divergence, got %r"
              % cell(outa, "dead-zone scope state (computed, never asserted)"))
        # non-vacuity B: a GPU-rule refusal at 0.50 x sits INSIDE the zone, but only for the wider
        # row sets — same bounds, different occupancy, which is the difference between a boundary
        # the rule has never been tested against and one it has.
        scope_b = dict(scope_a)
        scope_b["preflight-20300101-2355.txt"] = GPU_MID
        rcb, outb = run_fx(scope_b)
        c_sb = cell(outb, "dead-zone scope state (computed, never asserted)")
        check(rcb == 0 and c_sb.startswith("SAME BOUNDS, DIFFERENT OCCUPANCY")
              and cell(outb, "dead zone, DAY `20300102`")
              == "EMPTY (0 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)"
              and cell(outb, "dead zone, last 24 h")
              == "POPULATED (1 windows inside), bounds 0.01-3.00 x, width 2.995 x (59.9 MiB/s)",
              "the day scope calls the zone empty while the window scope has a reading inside it, "
              "got %r / %r / %r" % (c_sb, cell(outb, "dead zone, DAY `20300102`"),
                                    cell(outb, "dead zone, last 24 h")))
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
        c_sc = cell(outc, "dead-zone scope state (computed, never asserted)")
        check(rcc == 0 and c_sc.startswith("SCOPE-DEPENDENT — the DAY `20300102` dead zone is "
                                           "2.995 x (59.9 MiB/s) wide and the last 24 h one 2.250 x "
                                           "(45.0 MiB/s)"),
              "differing widths name both scopes and the factor, got %r" % c_sc)
        check(cell(outc, "dead zone, whole corpus")
              == "EMPTY (0 windows inside), bounds 0.75-3.00 x, width 2.250 x (45.0 MiB/s)",
              "the corpus GO bound follows the previous day's draw, got %r"
              % cell(outc, "dead zone, whole corpus"))
        # non-vacuity D: with no launchable draw anywhere, no scope may state a zone
        scope_d = {k: v for k, v in SCOPE.items() if k != "preflight-20300101-2340.txt"}
        rcd2, outd2 = run_fx(scope_d)
        check(rcd2 == 0 and cell(outd2, "dead-zone scope state (computed, never asserted)")
              .startswith("NO DEAD ZONE AT ANY SCOPE")
              and all(cell(outd2, lbl).startswith("NO ZONE at this scope")
                      for lbl in ("dead zone, DAY `20300102`", "dead zone, last 24 h",
                                  "dead zone, whole corpus")),
              "no scope invents a dead zone out of a refusal column alone, got %r"
              % cell(outd2, "dead-zone scope state (computed, never asserted)"))
        # the block is generated, so a snapshot of it must check clean and appear exactly once
        tbl10 = os.path.join(d10, "CEN.md")
        write_fixtures(d10, SCOPE)
        rcw10, outw10 = run(["--dir", d10, "--as-of", "20300102-0005", "--markdown", tbl10])
        check(rcw10 == 0, "writing the scope-band snapshot exits 0, got %r" % outw10[-300:])
        rcv10, outv10 = run(["--dir", d10, "--as-of", "20300102-0005", "--check", tbl10])
        check(rcv10 == 0, "the scope-band snapshot checks clean, got %r" % outv10[-300:])
        text10 = open(tbl10, encoding="utf-8").read()
        check(text10.count("| dead-zone scope state (computed, never asserted) |") == 1
              and text10.count("| rule band at three scopes (added 2026-11-16, tick 195) |") == 1,
              "the three-scope block appears exactly once in a committed table")
    finally:
        shutil.rmtree(d10, ignore_errors=True)

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
