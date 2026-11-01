#!/usr/bin/env python3
import os, json, re, glob, collections

BASE = os.path.expanduser("~/.hermes/bench/parb")
VIS = os.path.expanduser("~/.hermes/bench/visbench")

def rows(p):
    n = 0
    if not os.path.exists(p):
        return 0
    with open(p, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if line.strip():
                n += 1
    return n

def stats_rows(p):
    d = {}
    if not os.path.exists(p):
        return {}, 0
    with open(p, encoding="utf-8", errors="ignore") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            k = (r.get("task"), r.get("rep"), r.get("box"))
            if k not in d or float(r.get("content") or 0) > float(d[k].get("content") or 0):
                d[k] = r
    return d, len(d)

print("== gate result files under bench/parb ==")
gate_files = sorted(glob.glob(BASE + "/**/results*.jsonl", recursive=True))
for p in gate_files:
    d, n = stats_rows(p)
    tasks = sorted(set(k[0] for k in d))
    boxes = sorted(set(k[2] for k in d if k[2]))
    reps = sorted(set(k[1] for k in d if k[1] is not None))
    print(f"{p.replace(BASE,'BASE')} records={rows(p)} unique(task,rep,box)={n} boxes={boxes} n_tasks={len(tasks)} rep_range={min(reps) if reps else '-'}..{max(reps) if reps else '-'}")

print("\n== gate ledger files under bench/parb ==")
led_files = sorted(glob.glob(BASE + "/**/gate-ledger*.jsonl", recursive=True))
for p in led_files:
    print(f"{p.replace(BASE,'BASE')} records={rows(p)}")

print("\n== version log ==")
log = BASE + "/gate-versions.log"  # rig-side Russian decision log; the repo keeps the English translation gate-versions.en.md
if os.path.exists(log):
    lines = [l.rstrip("\n") for l in open(log, encoding="utf-8", errors="ignore")]
    print("lines", len(lines))
    for l in lines:
        if re.match(r".*(v1\.[0-9]|FINAL|contour|v1\.9|smoke|probe|запущ).*(=|DONE|FINAL|FIX|NEG|REJECT|OK|PASS|fail|не)", l, re.I):
            print(l[:350])

print("\n== visual benchmark counts ==")
for label, pat in [
    ("visbench result jsonl", VIS + "/**/*results*.jsonl"),
    ("visbench run dirs", VIS + "/**/attempt*"),
    ("visbench logs", VIS + "/**/*.log"),
    ("published html", VIS + "/**/index.html"),
    ("videos", VIS + "/**/*.mp4"),
    ("zips", VIS + "/**/*.zip"),
]:
    files = sorted(glob.glob(pat, recursive=True))
    if label.endswith("run dirs"):
        dirs = [f for f in files if os.path.isdir(f)]
        print(label, len(dirs))
    else:
        print(label, len(files))
        if len(files) <= 20:
            for f in files:
                print(" ", f.replace(VIS, "VIS"))

print("\n== all saved file counts by area ==")
for root in [BASE, VIS, os.path.expanduser("~/.hermes/cache/scratch/parb"), os.path.expanduser("~/.hermes/cache/scratch/visbench")]:
    cnt = 0
    size = 0
    exts = collections.Counter()
    for dirpath, _, filenames in os.walk(root):
        for name in filenames:
            fp = os.path.join(dirpath, name)
            try:
                st = os.stat(fp)
            except Exception:
                continue
            cnt += 1
            size += st.st_size
            exts[os.path.splitext(name)[1] or "none"] += 1
    print(f"{root} files={cnt} bytes={size/1e6:.1f}MB top_ext={exts.most_common(8)}")
