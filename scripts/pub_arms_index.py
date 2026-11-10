#!/usr/bin/env python3
"""Generate and verify the file index in benchmarks/public/arms/README.md.

Why this tool exists (2026-11-10 audit): the index carried ONE hash column labelled `sha16`,
and that column mixed two conventions - 125 rows pinned SHA-256/16 (the digest-row convention
this repo declares in MANIFEST.json -> benches.bfcl.hash_note) while 36 rows pinned SHA-1/16,
because the writers that produced those arms (scripts/pub_bench_repair.py, pub_bench_ifeval.py,
pub_bench_ifeval_v2.py) defined a local `sha16()` on top of hashlib.sha1. All 35 shipped `.sha16`
sidecar files carried SHA-1/16, and 35 of the 196 artifacts had no index row at all. An auditor
who follows the documented convention
(`sha256sum <file> | cut -c1-16`) gets a mismatch on those rows and concludes the shipped bytes
were tampered with, when they were not. The index therefore pins BOTH conventions per file and
`--check` fails closed if any pin, line count or row is stale, missing or unordered.

Usage:
    python3 scripts/pub_arms_index.py --check          # CI mode, exit 3 on drift
    python3 scripts/pub_arms_index.py --write          # rewrite every index table in place
    python3 scripts/pub_arms_index.py --rewrite-sidecars  # sidecar files -> SHA-256/16
    python3 scripts/pub_arms_index.py --report         # print the audit table (no writes)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARMS = os.path.join(ROOT, "benchmarks/public/arms")
README = os.path.join(ARMS, "README.md")
SIDECAR = ".sha16"

HEADER_RE = re.compile(r"^\|\s*arm file\s*\|")
ROW_RE = re.compile(r"^\|(.+)\|$")


def pins(path):
    data = open(path, "rb").read()
    n = data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
    return (n,
            hashlib.sha1(data).hexdigest()[:16],
            hashlib.sha256(data).hexdigest()[:16])


def tracked_files():
    """Every shipped artifact in arms/ (git-tracked; README.md itself excluded)."""
    out = subprocess.run(["git", "-C", ROOT, "ls-files", "--", "benchmarks/public/arms"],
                         capture_output=True, text=True).stdout.split()
    names = sorted(os.path.basename(p) for p in out if os.path.basename(p) != "README.md")
    on_disk = sorted(f for f in os.listdir(ARMS)
                     if f != "README.md" and os.path.isfile(os.path.join(ARMS, f)))
    return names, on_disk


def split_name(cell):
    """`foo.jsonl (72 retry rows)` -> ('foo.jsonl', '72 retry rows')."""
    cell = cell.strip()
    m = re.match(r"^(\S+)(?:\s*\((.*)\))?\s*$", cell)
    if not m:
        return cell, ""
    return m.group(1), (m.group(2) or "").strip()


def is_delim(line):
    """A GFM table delimiter row: `|---|---|`. Without it GitHub renders the table as prose."""
    body = line.replace("|", "").replace(" ", "")
    return bool(body) and line.strip().startswith("|") and set(body) <= {"-", ":"} and "-" in body


def parse_tables(lines):
    """Yield (start_idx, end_idx_exclusive, header_idx) for each arm-file table."""
    tables, i = [], 0
    while i < len(lines):
        if HEADER_RE.match(lines[i]):
            j = i + 1
            if j < len(lines) and is_delim(lines[j]):
                j += 1
            start = j
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            tables.append((start, j, i))
            i = j
        else:
            i += 1
    return tables


def row_cells(line):
    m = ROW_RE.match(line.strip())
    return [c.strip() for c in m.group(1).split("|")] if m else None


def build_row(name, note):
    n, s1, s2 = pins(os.path.join(ARMS, name))
    cell = name if not note else "%s (%s)" % (name, note)
    return "| %s | %d | `%s` | `%s` |" % (cell, n, s1, s2)


HEADER = "| arm file | lines | sha1/16 | sha256/16 |"
SEP = "|---|---|---|---|"


def regenerate(write=False):
    """Rebuild every index table from the files on disk; preserve row order and notes.

    The file is rebuilt in ONE pass (never by patching table slices at stale offsets: the
    delimiter row inserted into the first table shifts every later index).
    """
    lines = open(README, encoding="utf-8").read().split("\n")
    out, problems, indexed, tables = [], [], [], 0
    i = 0
    while i < len(lines):
        if HEADER_RE.match(lines[i]):
            tables += 1
            j = i + 1
            if j < len(lines) and is_delim(lines[j]):
                j += 1
            out += [HEADER, SEP]
            while j < len(lines) and lines[j].startswith("|"):
                cells = row_cells(lines[j])
                if not cells:
                    problems.append("unparsable row: %r" % lines[j])
                else:
                    name, note = split_name(cells[0])
                    if name not in indexed:
                        indexed.append(name)
                    try:
                        out.append(build_row(name, note))
                    except FileNotFoundError:
                        problems.append("index row for a file that is not shipped: %s" % name)
                j += 1
            i = j
        else:
            out.append(lines[i])
            i += 1
    if not tables:
        return ["no arm-file index table found in README.md"]
    names, on_disk = tracked_files()
    for f in on_disk:
        if f in indexed:
            continue
        if f.endswith(SIDECAR) and f[:-len(SIDECAR)] in indexed:
            # keep a sidecar row directly after its target row
            target = f[:-len(SIDECAR)]
            for k, ln in enumerate(out):
                cells = row_cells(ln) if ln.startswith("|") else None
                if cells and split_name(cells[0])[0] == target:
                    out.insert(k + 1, build_row(f, ""))
                    indexed.append(f)
                    break
        if f not in indexed:
            problems.append("file with no index row and no target row: %s" % f)
    if write:
        open(README, "w", encoding="utf-8").write("\n".join(out))
    return problems


def check():
    """Fail closed: every tracked file has a row, every row matches the file, no extra rows."""
    lines = open(README, encoding="utf-8").read().split("\n")
    tables = parse_tables(lines)
    names, on_disk = tracked_files()
    drift, seen = [], set()
    for f in on_disk:
        if f not in names:
            drift.append("UNTRACKED artifact in arms/ (add it or remove it): %s" % f)
    for f in names:
        if f not in on_disk:
            drift.append("TRACKED but missing on disk: %s" % f)
    for start, end, hdr in tables:
        if not HEADER_RE.match(lines[hdr]):
            drift.append("unexpected header at line %d" % (hdr + 1))
        if start == hdr + 1:
            drift.append("table at line %d has NO delimiter row (GitHub renders it as prose)"
                         % (hdr + 1))
        for ln in lines[start:end]:
            cells = row_cells(ln)
            if not cells:
                drift.append("unparsable row: %r" % ln)
                continue
            name, _ = split_name(cells[0])
            if name in seen:
                drift.append("duplicate index row: %s" % name)
            seen.add(name)
            if name not in on_disk:
                drift.append("index row for a file that is not shipped: %s" % name)
                continue
            n, s1, s2 = pins(os.path.join(ARMS, name))
            try:
                clines = int(cells[1])
            except ValueError:
                drift.append("non-numeric line count for %s: %r" % (name, cells[1]))
                clines = None
            if clines is not None and clines != n:
                drift.append("STALE LINE COUNT %s: index says %d, file has %d" % (name, clines, n))
            vals = [c.strip("` ") for c in cells[2:]]
            if len(vals) < 2:
                drift.append("AMBIGUOUS PIN COLUMN %s: index prints %d hash value(s) (%s); "
                             "every row must pin sha1/16 AND sha256/16"
                             % (name, len(vals), ",".join(vals)))
            elif len(vals) == 2:
                if vals[0] != s1:
                    drift.append("STALE PIN (sha1/16) %s: index %s, file %s" % (name, vals[0], s1))
                if vals[1] != s2:
                    drift.append("STALE PIN (sha256/16) %s: index %s, file %s" % (name, vals[1], s2))
            else:
                drift.append("unexpected pin column count for %s: %d" % (name, len(vals)))
    for f in on_disk:
        if f not in seen:
            drift.append("SHIPPED FILE WITH NO INDEX ROW: %s" % f)
    # sidecar content convention: a `.sha16` file pins SHA-256/16 of its target
    for f in on_disk:
        if not f.endswith(SIDECAR):
            continue
        target = f[:-len(SIDECAR)]
        if target not in on_disk:
            drift.append("sidecar without a target file: %s" % f)
            continue
        val = open(os.path.join(ARMS, f), encoding="utf-8").read().strip().split()[0].lower()
        want = hashlib.sha256(open(os.path.join(ARMS, target), "rb").read()).hexdigest()[:16]
        if val != want:
            drift.append("SIDECAR CONVENTION %s: content %s is not the SHA-256/16 of %s (%s)"
                         % (f, val, target, want))
    return drift


def rewrite_sidecars(dry=True):
    """Rewrite every `.sha16` sidecar to the SHA-256/16 convention; report old -> new."""
    moved = []
    for f in sorted(os.listdir(ARMS)):
        if not f.endswith(SIDECAR):
            continue
        target = f[:-len(SIDECAR)]
        if not os.path.isfile(os.path.join(ARMS, target)):
            continue
        p = os.path.join(ARMS, f)
        old = open(p, encoding="utf-8").read().strip()
        want = hashlib.sha256(open(os.path.join(ARMS, target), "rb").read()).hexdigest()[:16]
        if old == want:
            continue
        moved.append((f, old, want))
        if not dry:
            open(p, "w", encoding="utf-8").write(want + "\n")
    return moved


VENDOR = "benchmarks/public/vendor/instruction_following_eval"
TOOL_KEYS = ("checker_files", "scorer_files", "tool_files")


def resolve(rel):
    """A MANIFEST file name, at the repo root or in the vendored checker directory."""
    for cand in (rel, os.path.join(VENDOR, rel)):
        p = os.path.join(ROOT, cand)
        if os.path.isfile(p):
            return p
    return None


def git_bytes(rev, rel):
    try:
        out = subprocess.run(["git", "-C", ROOT, "show", "%s:%s" % (rev, rel)],
                             capture_output=True)
    except OSError:
        return None
    return out.stdout if out.returncode == 0 else None


def audit_manifest_pins(manifest_path=None):
    """Every pin in MANIFEST.json must resolve under a NAMED convention.

    The 2026-11-10 pin audit found the manifest itself mixing conventions: of seven tool pins, six
    (the five IFEval vendor checker files and the LiveCodeBench checker) were SHA-1/16 while the BFCL
    checker pin was SHA-256/16 - and inside the same livecodebench entry `checker_files` printed
    SHA-1/16 while `checker_history[0].sha16` printed SHA-256/16 of the same file name. A reader who
    verifies a checker with `sha256sum` therefore gets a false tamper alarm on the tool that scored
    the row. Pins stay published exactly as printed; this audit only refuses an *unlabelled* one.
    """
    with open(manifest_path or os.path.join(ROOT, "benchmarks/public/MANIFEST.json"),
              encoding="utf-8") as fh:
        man = json.load(fh)
    drift = []
    for bench, entry in sorted(man.get("benches", {}).items()):
        note = (entry.get("hash_note") or "").lower().replace("-", "")
        named_sha1 = "sha1" in note
        tasks = os.path.join(ROOT, "benchmarks/public", "%s.tasks.jsonl" % bench)
        pin = entry.get("tasks_sha16")
        if pin and os.path.isfile(tasks):
            kind = pin_kind(pin, open(tasks, "rb").read())
            if kind is None:
                drift.append("TASKS PIN %s: %s matches neither convention at current bytes"
                             % (bench, pin))
            elif kind == "sha1" and not (entry.get("tasks_sha256_16") and named_sha1):
                drift.append("UNLABELLED TASKS PIN %s: tasks_sha16 %s is SHA-1/16 but the entry "
                             "labels no sha256/16 twin and names no convention" % (bench, pin))
        for key in TOOL_KEYS + ("reference_response_file",):
            twin_key = "%s_sha256_16" % key
            twin = entry.get(twin_key) or {}
            pins_map = (entry.get(key) or {})
            if key == "reference_response_file":
                pins_map = {pins_map.get("name", ""): pins_map.get("sha16")} if pins_map else {}
            for name, val in sorted(pins_map.items()):
                path = resolve(name) if key != "reference_response_file" else resolve(
                    os.path.join("data", name))
                if path is None:
                    drift.append("PIN TARGET MISSING %s: %s -> %s" % (bench, key, name))
                    continue
                blob = open(path, "rb").read()
                kind = pin_kind(val, blob)
                if kind is None:
                    drift.append("TOOL PIN UNRESOLVABLE %s: %s[%s] = %s is neither SHA-1/16 nor "
                                 "SHA-256/16 of the file on disk (sha1=%s sha256=%s)"
                                 % (bench, key, name, val, sha1_16(blob), sha256_16(blob)))
                elif kind == "sha1":
                    want = sha256_16(blob)
                    have = twin if isinstance(twin, str) else twin.get(name)
                    if have != want:
                        drift.append("UNLABELLED TOOL PIN %s: %s[%s] = %s is SHA-1/16; the entry "
                                     "must carry %s = %s"
                                     % (bench, key, name, val,
                                        twin_key if isinstance(twin, str) or twin_key ==
                                        "reference_response_file" else "%s[%s]" % (twin_key, name),
                                        want))
                    if "sha1" not in note.lower():
                        drift.append("CONVENTION NOT NAMED %s: a %s pin is SHA-1/16 but hash_note "
                                     "does not say so" % (bench, key))
        for i, h in enumerate(entry.get("checker_history") or []):
            conv = (h.get("pin_hash_convention") or "").lower()
            if not conv:  # a self-named key declares its own convention
                if "sha256_16" in h:
                    conv = "sha256/16"
                elif "sha1_16" in h:
                    conv = "sha1/16"
            if conv not in ("sha1/16", "sha256/16"):
                drift.append("HISTORY PIN CONVENTION UNDECLARED %s: checker_history[%d] names no "
                             "pin_hash_convention" % (bench, i))
                continue
            rev, src = h.get("pinned_at_commit"), h.get("pinned_file")
            val = h.get("sha16") or h.get("sha256_16") or h.get("sha1_16")
            if rev and src:
                blob = git_bytes(rev, src)
                if blob is None:
                    drift.append("HISTORY PIN UNCHECKABLE %s: git show %s:%s failed"
                                 % (bench, rev, src))
                elif val != pin_hash_of(conv, blob):
                    drift.append("HISTORY PIN WRONG %s: checker_history[%d] says %s of %s at %s "
                                 "is %s, git bytes give %s"
                                 % (bench, i, conv, src, rev, val, pin_hash_of(conv, blob)))
    return drift


def pin_kind(pin, blob):
    if pin == hashlib.sha256(blob).hexdigest()[:16]:
        return "sha256"
    if pin == hashlib.sha1(blob).hexdigest()[:16]:
        return "sha1"
    return None


def sha1_16(blob):
    return hashlib.sha1(blob).hexdigest()[:16]


def sha256_16(blob):
    return hashlib.sha256(blob).hexdigest()[:16]


def pin_hash_of(conv, blob):
    return sha1_16(blob) if conv == "sha1/16" else sha256_16(blob)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify the index and the sidecars")
    ap.add_argument("--write", action="store_true", help="rewrite the index tables from the files")
    ap.add_argument("--rewrite-sidecars", action="store_true",
                    help="rewrite .sha16 sidecars to SHA-256/16 (default: --dry-run)")
    ap.add_argument("--apply", action="store_true", help="with --rewrite-sidecars: actually write")
    ap.add_argument("--report", action="store_true", help="print pins for every shipped file")
    ap.add_argument("--pins", action="store_true",
                    help="audit MANIFEST.json pins: every pin must resolve under a named convention")
    a = ap.parse_args()

    if a.rewrite_sidecars:
        moved = rewrite_sidecars(dry=not a.apply)
        for f, old, want in moved:
            print("%-58s old=%s new=%s%s" % (f, old, want, "" if a.apply else "  (dry run)"))
        print("sidecars to move to SHA-256/16: %d (applied=%s)" % (len(moved), a.apply))
        return 0
    if a.write:
        problems = regenerate(write=True)
        for p in problems:
            print("NOTE:", p)
        print("index rewritten")
    if a.report:
        for f in tracked_files()[1]:
            print("%-58s %s" % (f, " ".join(str(x) for x in pins(os.path.join(ARMS, f)))))
        return 0
    if a.pins:
        bad = audit_manifest_pins()
        for x in bad:
            print("DRIFT:", x)
        print("manifest pin drift: %d" % len(bad))
        return 3 if bad else 0
    drift = check() + audit_manifest_pins()
    for d in drift:
        print("DRIFT:", d)
    print("index drift: %d" % len(drift))
    return 3 if drift else 0


if __name__ == "__main__":
    sys.exit(main())
