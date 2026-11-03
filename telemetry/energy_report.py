#!/usr/bin/env python3
"""Integrate measured Terminal-Bench telemetry into energy and electricity cost.

Sources are deliberately separate.  A wall meter is not present on this fleet,
so the report calls the Intel RAPL + NVIDIA result an instrumented component
energy rather than a whole-system electricity claim.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from typing import Iterable


def parse_time(value: str | None) -> float | None:
    if not value:
        return None
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return dt.datetime.fromisoformat(value).timestamp()


def load(path: Path) -> tuple[dict, list[dict]]:
    header: dict = {}
    rows: list[dict] = []
    for raw in path.read_text().splitlines():
        if not raw.strip():
            continue
        obj = json.loads(raw)
        if obj.get("kind") == "telemetry-header":
            header = obj
        elif obj.get("kind") == "sample":
            rows.append(obj)
    return header, sorted(rows, key=lambda row: row.get("ts", 0))


def interval_samples(rows: Iterable[dict], start: float, end: float) -> list[dict]:
    return [r for r in rows if start - 2.0 <= float(r.get("ts", 0)) <= end + 2.0]


def integrate_power(rows: list[dict], field: str) -> float | None:
    values = [(float(r["ts"]), float(r[field])) for r in rows if r.get(field) is not None]
    if len(values) < 2:
        return None
    total = 0.0
    for (t0, p0), (t1, p1) in zip(values, values[1:]):
        if t1 <= t0:
            continue
        total += ((p0 + p1) / 2.0) * (t1 - t0)
    return total / 3_600_000.0  # W*s -> kWh


def integrate_energy(rows: list[dict], field: str) -> float | None:
    """Integrate cumulative mJ with wraparound. Used only if power is unavailable."""
    values = [(float(r["ts"]), float(r[field])) for r in rows if r.get(field) is not None]
    if len(values) < 2:
        return None
    total = 0.0
    for (_, e0), (_, e1) in zip(values, values[1:]):
        if e1 >= e0:
            total += e1 - e0
    return total / 3_600_000.0


def host_report(path: Path, start: float | None, end: float | None) -> dict:
    header, rows = load(path)
    start = start if start is not None else float(rows[0]["ts"])
    end = end if end is not None else float(rows[-1]["ts"])
    rows = interval_samples(rows, start, end)
    gpu_wh = integrate_power(rows, "gpu_power_w")
    cpu_wh = integrate_power(rows, "rapl_pkg_w")
    if cpu_wh is None:
        cpu_wh = integrate_energy(rows, "rapl_pkg_mj")
    if gpu_wh is None:
        gpu_wh = 0.0
    if cpu_wh is None:
        cpu_wh = 0.0
    measured_wh = gpu_wh + cpu_wh
    return {
        "machine": header.get("machine"),
        "os": header.get("os"),
        "samples": len(rows),
        "start_utc": dt.datetime.fromtimestamp(start, dt.timezone.utc).isoformat(),
        "end_utc": dt.datetime.fromtimestamp(end, dt.timezone.utc).isoformat(),
        "gpu_kwh": round(gpu_wh / 1000.0, 8),
        "rapl_package_kwh": round(cpu_wh / 1000.0, 8),
        "instrumented_component_kwh": round(measured_wh / 1000.0, 8),
        "measurement_scope": "NVIDIA GPU + Intel RAPL package; not a wall-meter total",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--telemetry", action="append", required=True, type=Path)
    ap.add_argument("--start")
    ap.add_argument("--end")
    ap.add_argument("--eur-per-kwh", type=float, default=0.25)
    ap.add_argument("--solved", type=int, default=1)
    ap.add_argument("--label", default="run")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()

    start = parse_time(args.start)
    end = parse_time(args.end)
    hosts = [host_report(p, start, end) for p in args.telemetry]
    total_kwh = sum(h["instrumented_component_kwh"] for h in hosts)
    solved = max(args.solved, 1)
    result = {
        "label": args.label,
        "hosts": hosts,
        "total_instrumented_kwh": round(total_kwh, 8),
        "cost_eur": round(total_kwh * args.eur_per_kwh, 8),
        "solved_tasks": solved,
        "cost_eur_per_solved_task": round(total_kwh * args.eur_per_kwh / solved, 8),
    }
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
