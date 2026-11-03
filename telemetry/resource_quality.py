#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Join answer quality with end-to-end latency and resource peaks.

Inputs are the gate artifacts:
  results.jsonl  (task, rep, t_wall, content)
  ledger.jsonl   (task, rep, seconds, tokens, contour_version)
  telemetry JSONL (collector2.py output)

For each task/rep attempt the tool reconstructs the approximate execution
window [t_wall - ledger_seconds, t_wall] and reports the observed peak/min
resource samples inside that window. It never interpolates: a missing sample
is reported as not_available.

Example:
  python3 telemetry/resource_quality.py results-v21.jsonl gate-ledger-v21.jsonl samp.jsonl \
    --out-json joined-resources.json --out-md resources.md
"""
import argparse
import json
import os
import statistics
from collections import defaultdict

METRICS = ("ram_used_mb", "ram_avail_mb", "ram_wired_mb", "ram_compressor_mb",
           "vram_used_mb", "vram_total_mb", "gpu_power_w", "gpu_util_pct")
KEY_FIELDS = ("task", "series", "rep")


def read_jsonl(path):
    with open(os.path.expanduser(path), encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def key(row):
    return (row.get("task"), row.get("series", "main"), row.get("rep"))


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    pos = (len(ordered) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(ordered) - 1)
    return round(ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo), 2)


def summary(values):
    vals = [x for x in values if isinstance(x, (int, float))]
    if not vals:
        return {"n": 0, "mean": None, "median": None, "p95": None,
                "min": None, "max": None}
    return {"n": len(vals), "mean": round(statistics.mean(vals), 2),
            "median": round(statistics.median(vals), 2),
            "p95": percentile(vals, 0.95), "min": round(min(vals), 2),
            "max": round(max(vals), 2)}


def aggregate(samples, label):
    scores = [x["content"] for x in samples if isinstance(x.get("content"), (int, float))]
    lat = [x["seconds"] for x in samples if isinstance(x.get("seconds"), (int, float))]
    energy = [x.get("energy_wh") for x in samples if isinstance(x.get("energy_wh"), (int, float))]
    out = {"label": label, "n": len(samples), "content": summary(scores),
           "perfect_rate_pct": round(100.0 * sum(1 for x in scores if x >= 0.999) / len(scores), 1) if scores else None,
           "end_to_end_seconds": summary(lat),
           "energy_wh": summary(energy)}
    for m in METRICS:
        peak_field = "peak_" + m
        vals = [x[peak_field] for x in samples if isinstance(x.get(peak_field), (int, float))]
        out[peak_field] = summary(vals)
        if m.endswith("_avail_mb"):
            min_vals = [x["min_" + m] for x in samples if isinstance(x.get("min_" + m), (int, float))]
            out["min_" + m] = summary(min_vals)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("ledger")
    ap.add_argument("telemetry")
    ap.add_argument("--out-json")
    ap.add_argument("--out-md")
    args = ap.parse_args()

    res = read_jsonl(args.results)
    led_rows = read_jsonl(args.ledger)
    led = defaultdict(list)
    for r in led_rows:
        led[key(r)].append(r)

    samples_all = []
    header = None
    for s in read_jsonl(args.telemetry):
        if s.get("kind") == "telemetry-header":
            header = s
        elif s.get("kind") == "sample":
            samples_all.append(s)
    samples_all.sort(key=lambda x: x.get("ts", 0))
    ts_values = [s.get("ts", 0) for s in samples_all]

    attempts = []
    for r in res:
        k = key(r)
        secs = sum(float(e.get("seconds") or 0) for e in led.get(k, []))
        secs = max(secs, 1.0)
        t_end = float(r.get("t_wall") or 0)
        t_start = t_end - secs
        window = [s for s in samples_all if t_start <= s.get("ts", 0) <= t_end + 1.0]
        item = {"attempt": "%s#%s" % (r.get("task"), r.get("rep")), "task": r.get("task"),
                "series": r.get("series", "main"), "rep": r.get("rep"),
                "contour": r.get("contour_version") or r.get("contour"),
                "content": r.get("content"), "seconds": round(secs, 2),
                "samples_in_window": len(window), "t_start": t_start, "t_end": t_end}
        for m in METRICS:
            vals = [s[m] for s in window if isinstance(s.get(m), (int, float))]
            item["peak_" + m] = max(vals) if vals else None
            if m.endswith("_avail_mb"):
                item["min_" + m] = min(vals) if vals else None
        power = [s.get("gpu_power_w") for s in window if isinstance(s.get("gpu_power_w"), (int, float))]
        item["energy_wh"] = round(statistics.mean(power) * secs / 3600.0, 4) if power else None
        attempts.append(item)

    by_contour = defaultdict(list)
    for item in attempts:
        by_contour[item["contour"]].append(item)
    run = aggregate(attempts, "all")
    per_contour = {c: aggregate(v, c) for c, v in sorted(by_contour.items())}

    out = {"header": header, "run_level": run, "per_contour": per_contour,
           "per_attempt": attempts}
    text = json.dumps(out, indent=1, ensure_ascii=False)
    if args.out_json:
        with open(os.path.expanduser(args.out_json), "w", encoding="utf-8") as f:
            f.write(text + "\n")
    if args.out_md:
        md = ["# Resource, latency and quality report", ""]

        def fmt(x):
            return "-" if x is None else x

        if header:
            osr = header.get("os")
            if isinstance(osr, dict):
                md.append("**OS:** %s %s (%s), %s, kernel %s" % (
                    osr.get("id", "-"), osr.get("pretty", "-"), osr.get("codename", "-"),
                    osr.get("flavor", "-"), osr.get("kernel", "-")))
            else:
                md.append("**OS:** %s" % fmt(osr))
            md.append("")
        for label, agg in [("All attempts", run)] + sorted(per_contour.items()):
            md += ["## " + label, "", "| Metric | value |", "|---|---:|"]
            md.append("| attempts | %s |" % agg["n"])
            md.append("| content mean | %s |" % fmt(agg["content"]["mean"]))
            md.append("| perfect rate | %s%% |" % fmt(agg["perfect_rate_pct"]))
            e = agg["end_to_end_seconds"]
            md.append("| latency median s | %s |" % fmt(e["median"]))
            md.append("| latency p95 s | %s |" % fmt(e["p95"]))
            md.append("| latency max s | %s |" % fmt(e["max"]))
            for m in METRICS:
                p = agg["peak_" + m]
                if p["n"]:
                    md.append("| peak %s | %s |" % (m, fmt(p["max"])))
            en = agg["energy_wh"]
            md.append("| estimated GPU energy Wh | %s |" % fmt(en["mean"]))
            md.append("")
        with open(os.path.expanduser(args.out_md), "w", encoding="utf-8") as f:
            f.write("\n".join(md))
    if not args.out_json:
        print(text)


if __name__ == "__main__":
    main()
