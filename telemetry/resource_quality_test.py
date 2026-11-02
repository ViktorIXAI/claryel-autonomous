#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic contract test for resource/latency/quality joining."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = Path(BASE).parent


def main():
    res = [
        {"task": "A-1", "series": "main", "rep": 0, "t_wall": 110.0,
         "content": 1.0, "contour_version": "v2.2"},
        {"task": "B-1", "series": "main", "rep": 0, "t_wall": 130.0,
         "content": 0.5, "contour_version": "v2.1"},
    ]
    led = [
        {"task": "A-1", "series": "main", "rep": 0, "seconds": 10.0},
        {"task": "B-1", "series": "main", "rep": 0, "seconds": 20.0},
    ]
    telem = [
        {"kind": "telemetry-header", "run_id": "test"},
        {"kind": "sample", "ts": 99.0, "ram_used_mb": 100, "vram_used_mb": 10,
         "gpu_power_w": 50, "ram_avail_mb": 900},
        {"kind": "sample", "ts": 105.0, "ram_used_mb": 200, "vram_used_mb": 90,
         "gpu_power_w": 100, "ram_avail_mb": 800},
        {"kind": "sample", "ts": 125.0, "ram_used_mb": 300, "vram_used_mb": None,
         "gpu_power_w": None, "ram_avail_mb": 700},
    ]
    with tempfile.TemporaryDirectory() as td:
        p_res = Path(td) / "res.jsonl"
        p_led = Path(td) / "led.jsonl"
        p_tel = Path(td) / "tel.jsonl"
        p_out = Path(td) / "out.json"
        for p, rows in ((p_res, res), (p_led, led), (p_tel, telem)):
            p.write_text("".join(json.dumps(x) + "\n" for x in rows), encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "telemetry" / "resource_quality.py"),
                        str(p_res), str(p_led), str(p_tel), "--out-json", str(p_out)], check=True)
        out = json.loads(p_out.read_text(encoding="utf-8"))
    assert out["run_level"]["n"] == 2
    assert out["run_level"]["content"]["mean"] == 0.75
    assert out["run_level"]["end_to_end_seconds"]["median"] == 15.0
    assert out["run_level"]["peak_vram_used_mb"]["max"] == 90.0
    assert out["run_level"]["peak_gpu_power_w"]["max"] == 100.0
    assert out["run_level"]["energy_wh"]["mean"] == 0.28
    assert out["per_attempt"][0]["peak_ram_used_mb"] == 200.0
    assert out["per_attempt"][1]["peak_ram_used_mb"] == 300.0
    assert out["per_attempt"][1]["min_ram_avail_mb"] == 700.0
    print("RESOURCE QUALITY TEST: PASS")


if __name__ == "__main__":
    main()
