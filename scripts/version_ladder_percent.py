#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Version ladder in percent: one row per (contour stamp, bank), with growth.

The operator wants a single screenshot-friendly table: version number, percent of the bank
solved, growth over the previous version. Both halves are generated, never retyped:

  * percentages come from the rows `run_digest.py` wrote into DIGEST.md (arm means over that
    stamp's full-bank arms on that bank);
  * the verdict column is read out of the pair verdict docs (title / `Verdict:` line), so the
    ladder cannot quietly present a frozen or UNMEASURED stamp as progress.

Growth is only printed between rows measured on the SAME bank: a bank fix moves the ceiling of
every arm, so a jump across a bank change is not contour progress.
"""
import glob
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
V6 = os.path.normpath(os.path.join(HERE, "..", "benchmarks", "hard", "v6-results"))


def verdicts():
    """stamp -> ADOPTED / NOT ADOPTED / UNMEASURED, read from pair verdict docs.

    A status is taken only from a line that NAMES a stamp and carries a verdict marker
    (`UNMEASURED`, `not adopted`, `NEGATIVE`, uppercase `ADOPTED`, or "line moves/becomes
    0.0.2.N"), never from a wiring or prose line ("control X vs candidate Y", "the adopted
    ladder") - the loose version of this parser labeled frozen stamps as wins, which is exactly
    the error the ladder must not reproduce. First verdict wins, never overwritten; a stamp no
    doc rules on stays blank rather than being guessed.
    """
    out = {}
    pat = re.compile(r"0\.0\.2\.(\d+)")
    moves = re.compile(r"line (?:moves|becomes|is|stays)\s+`?(?:0\.0\.2\.)?(\d+)")
    for f in sorted(glob.glob(os.path.join(V6, "PAIR-*.md"))):
        lines = open(f, encoding="utf-8").readlines()
        for line in lines:
            if "(control" not in line and "(candidate" not in line and "candidate `" not in line:
                nums = pat.findall(line)
                up = line.upper()
                st = None
                if "UNMEASURED" in up:
                    st = "UNMEASURED"
                elif re.search(r"not\s+adopted", line, re.I) or "NEGATIVE" in up:
                    st = "NOT ADOPTED"
                elif re.search(r"\bADOPTED\b", line):
                    st = "ADOPTED"
                if st:
                    for n in nums:
                        out.setdefault(int(n), st)
            for mv in moves.finditer(line):
                out.setdefault(int(mv.group(1)), "ADOPTED")
        # A verdict heading may name no stamp at all ("the pair is UNMEASURED"); then the
        # candidate is by convention the higher of the two stamps the doc opens with.
        head = "".join(lines[:12]).upper()
        if "UNMEASURED" in head:
            nums = [int(n) for n in pat.findall("".join(lines[:12]))]
            if len(set(nums)) >= 2:
                out.setdefault(max(nums), "UNMEASURED")
    return out


def main():
    rows = []
    for line in open(os.path.join(V6, "DIGEST.md"), encoding="utf-8"):
        if not line.startswith("| ") or "when |" in line or set(line) <= set("|- "):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) < 8:
            continue
        bank, stamp, arms = c[2], c[3], int(c[4])
        m = re.search(r"([\d.]+)%\*\*$", c[7])
        if not m:
            continue
        pct = float(m.group(1))
        rows.append((tuple(int(x) for x in stamp.split(".")), bank, stamp, arms,
                     c[5], c[6], pct))
    ver = verdicts()
    rows.sort(key=lambda r: (r[0], r[1]))

    print("| version | bank | arms | single-shot | loop-D | percent of bank | growth | verdict |")
    print("|---|---|---|---|---|---|---|---|")
    last = {}
    for _, bank, stamp, arms, ss, lp, pct in rows:
        d = "" if bank not in last else ("%+.1f" % (pct - last[bank]))
        if bank in last and abs(pct - last[bank]) < 1.4:
            d = (d + " *") if d else ""
        last[bank] = pct
        print("| %s | %s | %d | %s | %s | **%.1f %%** | %s | %s |"
              % (stamp, bank.split()[0], arms, ss, lp, pct, d or "-",
                 ver.get(int(stamp.split(".")[-1]), "")))
    print("\n`*` growth below the resolution floor (~1.4 cells = ~1.8 pp at three seeds) - not "
          "confirmed by the mean, only by cell attribution. Rows are arm means over every "
          "full-bank arm of that stamp on that bank; growth is printed only within one bank, "
          "because a bank fix moves the ceiling of every arm. Tooling releases (2.45, 2.46, 2.49) "
          "do not change contour behavior, so their spread is re-measurement noise. `/77` includes "
          "the 10 category-E docker tasks; paired cross-arm tables use the 61-cell common set.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
