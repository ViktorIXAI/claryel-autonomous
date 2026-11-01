# -*- coding: utf-8 -*-
"""PARB telemetry: 1 Hz, unbuffered CSV.
Columns: ts, mem_avail_mb, swap_used_mb, dirty_kb, nvme_rd_kbs, nvme_wr_kbs, vram_used_mb,
gpu_util, gpu_power_w, gpu_temp_c, gpu_clk_mhz, cpu_temp_c, load1
"""
import os, sys, time, subprocess, glob

OUT = os.path.expanduser("~/parb/telem/samp.csv")
os.makedirs(os.path.dirname(OUT), exist_ok=True)


def meminfo():
    d = {}
    for ln in open("/proc/meminfo"):
        k = ln.split(":")[0]
        d[k] = int(ln.split()[1])
    return d


def diskstats():
    tot_r = tot_w = 0
    for ln in open("/proc/diskstats"):
        p = ln.split()
        name = p[2]
        if name.startswith("nvme") and "p" not in name[4:]:
            tot_r += int(p[5])
            tot_w += int(p[9])
        elif name in ("sda", "sdb", "sdc", "mmcblk0"):
            tot_r += int(p[5])
            tot_w += int(p[9])
    return tot_r, tot_w


def cpu_temp():
    best = 0
    for f in glob.glob("/sys/class/thermal/thermal_zone*/temp") + \
            glob.glob("/sys/class/hwmon/hwmon*/temp*_input"):
        try:
            v = int(open(f).read().strip())
            if v > 1000:
                v //= 1000
            best = max(best, v)
        except Exception:
            pass
    return best


def gpu():
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=utilization.gpu,power.draw,temperature.gpu,"
                                    "memory.used,clocks.sm", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5).stdout.strip().split(",")
        return [float(x) for x in out[:5]]
    except Exception:
        return [None] * 5


def main():
    dur = float(sys.argv[1]) if len(sys.argv) > 1 else 15000
    t_end = time.time() + dur
    prev = diskstats()
    pt = time.time()
    first = not os.path.exists(OUT)
    f = open(OUT, "a", buffering=1)
    if first:
        f.write("ts,mem_avail_mb,swap_used_mb,dirty_kb,nvme_rd_kbs,nvme_wr_kbs,vram_used_mb,gpu_util,"
                "gpu_power_w,gpu_temp_c,gpu_clk_mhz,cpu_temp_c,load1\n")
    while time.time() < t_end:
        m = meminfo()
        d = diskstats()
        now = time.time()
        dt = max(now - pt, 0.2)
        rd = (d[0] - prev[0]) * 512 / 1024.0 / dt
        wr = (d[1] - prev[1]) * 512 / 1024.0 / dt
        prev = d
        pt = now
        g = gpu()
        load = open("/proc/loadavg").read().split()[0]
        row = [round(now, 3), m["MemAvailable"] // 1024, (m["SwapTotal"] - m["SwapFree"]) // 1024,
               m.get("Dirty", 0), round(rd, 1), round(wr, 1),
               g[3] if g[3] is not None else "", g[0] if g[0] is not None else "",
               g[1] if g[1] is not None else "", g[2] if g[2] is not None else "",
               g[4] if g[4] is not None else "", cpu_temp(), load]
        f.write(",".join("" if v == "" else str(v) for v in row) + "\n")
        time.sleep(max(1.0 - (time.time() - now), 0.05))


if __name__ == "__main__":
    main()
