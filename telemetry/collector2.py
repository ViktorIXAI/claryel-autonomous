#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Telemetry collector v2 — per-run, per-machine, self-describing JSONL.

One JSONL file per run. Line 1 = header (units + source per metric).
Data lines = one sample/second. Every metric either carries a real reading
from a named source or is literally `null` with source `not_available` —
never an estimate. Linux reads procfs/sysfs/nvidia-smi; macOS reads
vm_stat/sysctl/top (temperatures and GPU power require root there and are
published as not_available, not sudo'd).

Env: PARB_RUN_ID  run identifier bound into every line (set it to the same
     value the runner logs); PARB_TELEM output path; PARB_MACHINE name.
Run detached during a series; join with telemetry/join.py afterwards.
"""
import json
import os
import platform
import re
import subprocess
import sys
import time

MACHINE = os.environ.get("PARB_MACHINE") or platform.node()
RUN_ID = os.environ.get("PARB_RUN_ID", "unbound")
OUT = os.path.expanduser(os.environ.get("PARB_TELEM", "~/parb/telem/samp2.jsonl"))
INTERVAL = float(os.environ.get("PARB_TELEM_INTERVAL", "1.0"))
IS_MAC = platform.system() == "Darwin"

UNITS = {"cpu_pct": "%", "load1": "procs", "cpu_ghz": "GHz", "cpu_temp_c": "C",
         "ram_used_mb": "MB", "ram_avail_mb": "MB", "ram_wired_mb": "MB",
         "ram_compressor_mb": "MB", "swap_used_mb": "MB",
         "vram_used_mb": "MB", "vram_total_mb": "MB", "gpu_util_pct": "%",
         "gpu_power_w": "W", "gpu_temp_c": "C", "gpu_clk_mhz": "MHz",
         "gpu_throttle": "flags", "disk_rd_kbps": "kB/s", "disk_wr_kbps": "kB/s"}


# The exact OS record must be bound into the telemetry header, not inferred
# from hostname or a kernel version alone. Ubuntu Desktop and Ubuntu Server
# can share the same 24.04 version but have different installed packages.
try:
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "harness"))
    import os_record as _OS

    OS_METADATA = _OS.safe_for_log(_OS.detect())
except Exception:
    OS_METADATA = {
        "id": platform.system().lower(),
        "pretty": "%s %s" % (platform.system(), platform.release()),
        "version": "",
        "codename": "",
        "flavor": "unknown",
        "flavor_evidence": "os_record unavailable",
        "kernel": platform.release(),
        "architecture": platform.machine(),
        "hostname": platform.node(),
    }
Nvidia = ["utilization.gpu,power.draw,temperature.gpu,clocks.current.graphics,"
          "clocks_event_reasons.active,memory.used,memory.total",
          "--format=csv,noheader,nounits"]


def parse_mac_bytes(value):
    m = re.fullmatch(r"([\d.]+)([KMGT]?B)", value)
    if not m:
        return 0.0
    n = float(m.group(1))
    unit = m.group(2)[:-1] or ""
    return n * {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4}[unit]


def meminfo():
    d = {}
    for ln in open("/proc/meminfo"):
        k = ln.split(":")[0]
        try:
            d[k] = int(ln.split()[1])
        except ValueError:
            pass
    return d


def diskstats():
    r = w = 0
    for ln in open("/proc/diskstats"):
        p = ln.split()
        if len(p) > 10 and re.match(r"(nvme\d+n\d+|sd[a-z]+|mmcblk\d+)$", p[2]):
            r += int(p[5])
            w += int(p[9])
    return r, w


def temps():
    best = None
    for f in (list(__import__("glob").glob("/sys/class/thermal/thermal_zone*/temp")) +
              list(__import__("glob").glob("/sys/class/hwmon/hwmon*/temp*_input"))):
        try:
            v = int(open(f).read().strip())
            v = v / 1000 if v > 1000 else v
            if 0 < v < 120 and (best is None or v > best):
                best = v
        except Exception:
            pass
    return best


def cpu_ghz():
    try:
        cur = open("/proc/cpuinfo").read()
        m = re.findall(r"cpu MHz\s*:\s*([\d.]+)", cur)
        if m:
            return round(max(float(x) for x in m) / 1000, 3)
    except Exception:
        pass
    try:
        return round(int(open("/sys/devices/system/cpu/cpu0/cpufreq/"
                              "scaling_cur_freq").read()) / 1e6, 3)
    except Exception:
        return None


def nvidia():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=" + Nvidia[0]] + Nvidia[1:],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        rows = []
        for line in out.splitlines():
            p = [x.strip() for x in line.split(",")]
            if len(p) < 7:
                continue
            try:
                rows.append({"gpu_util_pct": float(p[0]), "gpu_power_w": float(p[1]),
                             "gpu_temp_c": float(p[2]), "gpu_clk_mhz": float(p[3]),
                             "gpu_throttle": p[4], "vram_used_mb": float(p[5]),
                             "vram_total_mb": float(p[6])})
            except ValueError:
                continue
        if not rows:
            return {}
        env_idx = os.environ.get("PARB_GPU_INDEX")
        if env_idx is not None:
            idx = int(env_idx)
            return rows[idx] if 0 <= idx < len(rows) else {}
        return max(rows, key=lambda g: (g["vram_total_mb"], g["vram_used_mb"]))
    except Exception:
        return {}


def cpu_pct(prev):
    try:
        f = open("/proc/stat").readline().split()
        idle = int(f[4]) + int(f[5])
        tot = sum(int(x) for x in f[1:11])
        if prev:
            dt, di = tot - prev[0], idle - prev[1]
            if dt > 0:
                return round(100.0 * (dt - di) / dt, 1), (tot, idle)
        return None, (tot, idle)
    except Exception:
        return None, prev


def sample():
    global _PREV_CPU, _PREV_DISK
    s, src = {}, {k: "not_available" for k in UNITS}
    for k in UNITS:
        s[k] = None
    now = time.time()
    s["ts"] = round(now, 2)
    s["ts_iso"] = time.strftime("%FT%TZ", time.gmtime(now))
    s["machine"] = MACHINE
    s["run_id"] = RUN_ID
    if IS_MAC:
        # load + cpu via os.getloadavg; mem via vm_stat; rest not_available
        try:
            s["load1"] = round(os.getloadavg()[0], 2)
            src["load1"] = "syscall(getloadavg)"
        except Exception:
            s["load1"] = None; src["load1"] = "not_available"
        try:
            out = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
            page = int(re.search(r"page size of (\d+)", out).group(1))
            def pg(name):
                m = re.search(r"^" + name + r":\s+([\d.]+)\.", out, re.M)
                return float(m.group(1)) if m else None
            total_mb = int(subprocess.run(["sysctl", "-n", "hw.memsize"], capture_output=True,
                                          text=True, timeout=5).stdout.strip()) / 1048576
            free = pg("Pages free") or 0
            inactive = pg("Pages inactive") or 0
            speculative = pg("Pages speculative") or 0
            wired = pg("Pages wired down") or 0
            compressor = pg("Pages occupied by compressor") or 0
            s["ram_avail_mb"] = round((free + inactive + speculative) * page / 1048576, 0)
            src["ram_avail_mb"] = "vm_stat(free+inactive+speculative)"
            s["ram_used_mb"] = round(max(total_mb - free * page / 1048576, 0), 0)
            src["ram_used_mb"] = "vm_stat(total-free)"
            s["ram_wired_mb"] = round(wired * page / 1048576, 0)
            src["ram_wired_mb"] = "vm_stat(wired)"
            s["ram_compressor_mb"] = round(compressor * page / 1048576, 0)
            src["ram_compressor_mb"] = "vm_stat(compressor)"
        except Exception:
            for k in ("ram_used_mb", "ram_avail_mb", "ram_wired_mb", "ram_compressor_mb"):
                s[k] = None
                src[k] = "not_available"
        try:
            out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True,
                                 text=True, timeout=5).stdout
            m = re.search(r"used\s*=\s*([\d.]+)([KMGT]?B)", out)
            if m:
                s["swap_used_mb"] = round(parse_mac_bytes(m.group(1) + m.group(2)) / 1048576, 0)
                src["swap_used_mb"] = "sysctl(vm.swapusage)"
        except Exception:
            s["swap_used_mb"] = None; src["swap_used_mb"] = "not_available"
        for k in ("cpu_ghz", "vram_used_mb", "vram_total_mb",
                  "gpu_util_pct", "gpu_power_w", "gpu_temp_c",
                  "gpu_clk_mhz", "gpu_throttle", "disk_rd_kbps", "disk_wr_kbps"):
            s[k] = None
            src[k] = "not_available(root-required on macOS)" if k in ("gpu_power_w", "gpu_temp_c", "gpu_util_pct") else "not_available"
        if s.get("ram_avail_mb") is None:
            s["ram_avail_mb"] = None; src["ram_avail_mb"] = "not_available(macOS vm_stat could not expose reclaimable memory)"
        return s, src
    m = meminfo()
    # /proc/meminfo values are kB; convert to MB so the unit label is honest
    s["ram_avail_mb"] = m["MemAvailable"] // 1024 if "MemAvailable" in m else None
    s["ram_used_mb"] = (m["MemTotal"] - m["MemAvailable"]) // 1024 if "MemTotal" in m and "MemAvailable" in m else None
    s["swap_used_mb"] = (m.get("SwapTotal", 0) - m.get("SwapFree", 0)) // 1024
    src.update({k: "procfs(meminfo)" for k in ("ram_avail_mb", "ram_used_mb", "swap_used_mb")})
    try:
        s["load1"] = round(float(open("/proc/loadavg").read().split()[0]), 2)
        src["load1"] = "procfs(loadavg)"
    except Exception:
        s["load1"] = None; src["load1"] = "not_available"
    pct, _PREV_CPU = cpu_pct(_PREV_CPU)
    s["cpu_pct"] = pct
    src["cpu_pct"] = "procfs(stat-delta)" if pct is not None else "not_available"
    s["cpu_ghz"] = cpu_ghz()
    src["cpu_ghz"] = "procfs/cpuinfo(max)" if s["cpu_ghz"] else "not_available"
    s["cpu_temp_c"] = temps()
    src["cpu_temp_c"] = "sysfs(thermal_zone/hwmon max)" if s["cpu_temp_c"] else "not_available(no sensors exposed)"
    try:
        out = open("/sys/class/power_supply/ac/power_now_cap").read()  # rare; keep opt
        s["psu_w"] = float(out)
        src["psu_w"] = "sysfs"
    except Exception:
        pass
    g = nvidia()
    for k in ("vram_used_mb", "vram_total_mb", "gpu_util_pct", "gpu_power_w",
              "gpu_temp_c", "gpu_clk_mhz", "gpu_throttle"):
        s[k] = g.get(k)
        src[k] = "nvidia-smi" if k in g else "not_available"
    nowr = diskstats()
    if _PREV_DISK:
        dt = now - _PREV_DISK[2]
        if dt > 0:
            s["disk_rd_kbps"] = round((nowr[0] - _PREV_DISK[0]) * 512 / dt / 1024, 1)
            s["disk_wr_kbps"] = round((nowr[1] - _PREV_DISK[1]) * 512 / dt / 1024, 1)
        else:
            s["disk_rd_kbps"] = s["disk_wr_kbps"] = None
    else:
        s["disk_rd_kbps"] = s["disk_wr_kbps"] = None
    src["disk_rd_kbps"] = src["disk_wr_kbps"] = "procfs(diskstats-delta)"
    _PREV_DISK = (nowr[0], nowr[1], now)
    return s, src


_PREV_CPU = None
_PREV_DISK = None


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    hdr = {"kind": "telemetry-header", "run_id": RUN_ID, "machine": MACHINE,
           "os": OS_METADATA,
           "os_line": "%s %s" % (platform.system(), platform.release()),
           "interval_s": INTERVAL, "units": UNITS, "started_utc": time.strftime("%FT%TZ", time.gmtime())}
    with open(OUT, "a") as f:
        f.write(json.dumps(hdr, ensure_ascii=False) + "\n")
        prev = None
        try:
            while True:
                s, src = sample()
                s["kind"] = "sample"
                s["sources"] = src
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
                f.flush()
                time.sleep(INTERVAL)
        except KeyboardInterrupt:
            pass
        except BrokenPipeError:
            pass


if __name__ == "__main__":
    main()
