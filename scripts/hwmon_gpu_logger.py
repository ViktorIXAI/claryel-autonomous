#!/usr/bin/env python3
# P3001 logger v2: AMD RX 580 (amdgpu hwmon) + CPU coretemp + RAM/swap, CSV every 5 s, values in C / W / MHz.
import glob, os, time, csv, sys

CARD = "/sys/class/drm/card1/device"
HW = glob.glob(CARD + "/hwmon/hwmon*")[0]
CPU = [h for h in glob.glob("/sys/class/hwmon/hwmon*")
       if os.path.exists(h + "/name") and open(h + "/name").read().strip() == "coretemp"][0]
OUT = os.path.expanduser("~/llama-vulkan/temps.csv")
SUM = os.path.expanduser("~/llama-vulkan/temps_summary.txt")


def val(path, scale=1.0):
    try:
        return round(float(open(path).read().strip()) / scale, 2)
    except Exception:
        return ""


def cpu_max():
    t = []
    for f in glob.glob(CPU + "/temp*_input"):
        try:
            v = float(open(f).read().strip()) / 1000.0
            if 15 < v < 130:
                t.append(v)
        except Exception:
            pass
    return (max(t), min(t)) if t else ("", "")


def mem_used():
    d = {}
    for line in open("/proc/meminfo"):
        k = line.split(":")[0]
        d[k] = int(line.split()[1])
    return round((d["MemTotal"] - d["MemAvailable"]) / 1048576.0, 1)


def swap_used():
    tot = 0.0
    for l in open("/proc/swaps").read().splitlines()[1:]:
        p = l.split()
        tot += float(p[3])
    return round(tot / 1048576.0, 2)


dur = int(sys.argv[1]) if len(sys.argv) > 1 else 5400
t0 = time.time()
peak = {"edge": 0.0, "power": 0.0, "cpu": 0.0}
with open(OUT, "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["ts", "gpu_edge_C", "gpu_busy_pct", "gpu_power_W", "gpu_clock_MHz",
                "fan_rpm", "fan_pwm_pct", "power_cap_W", "cpu_max_C", "cpu_min_C",
                "ram_used_G", "swap_used_G"])
    while time.time() - t0 < dur:
        gmax = val(HW + "/temp1_input", 1000.0)
        pw = val(HW + "/power1_input", 1e6)
        cx, cn = cpu_max()
        row = [time.strftime("%H:%M:%S"), gmax, val(CARD + "/gpu_busy_percent"), val(HW + "/power1_input", 1e6),
               val(HW + "/freq1_input", 1e6), val(HW + "/fan1_input"),
               round(val(HW + "/pwm1") / 255.0 * 100, 1) if val(HW + "/pwm1") != "" else "",
               val(HW + "/power1_cap", 1e6), cx, cn, mem_used(), swap_used()]
        w.writerow(row)
        fh.flush()
        for k, v in (("edge", gmax), ("power", pw), ("cpu", cx)):
            if v != "" and v > peak[k]:
                peak[k] = v
        with open(SUM, "w") as s:
            s.write("since %s  peak_gpu_C=%s  peak_gpu_W=%s  peak_cpu_C=%s  last_row=%s\n"
                    % (time.strftime("%H:%M", time.localtime(t0)), peak["edge"], peak["power"], peak["cpu"], row))
        time.sleep(5)
