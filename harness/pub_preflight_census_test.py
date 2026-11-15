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
"""
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
