#!/usr/bin/env python3
"""v2.2 F diagnostic-grounding tests."""
import importlib.util
import os
import sys

os.environ["PARB_GATE_VERSION"] = "v2.2"
BASE = os.path.dirname(os.path.abspath(__file__))


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, os.path.join(BASE, filename))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


GR = load_module("gate_run", "gate_run.py")
CK = load_module("parb_check", "parb_check.py")


def task(tid, kind, prompt, ref):
    return {"id": tid, "kind": kind, "cat": "F", "prompt": prompt, "ref": ref, "decoy": None}


oom_prompt = (
    "kernel: node invoked oom-killer: gfp_mask=0x14200ca\n"
    "kernel: Out of memory: Killed process 4123 (strata)\n"
    "kernel: Mem-Info: active_anon:17441234 free:1204 kB\n"
    "kernel: nvme0: I/O sqid:1 completion path ok"
)
disk_prompt = (
    "dockerd[912]: failed to create tmpfs: no space left on device\n"
    "kernel: EXT4-fs (nvme0n1p2): Remounting filesystem read-only\n"
    "kernel: Out of memory: Killed process 771 (node)\n"
    "kernel: hw heat: CPU temperature above threshold"
)
nvme_prompt = (
    "kernel: nvme nvme0: I/O 1288 QID 1 timeout, aborting\n"
    "kernel: EXT4-fs error (device nvme0n1p2): ext4_find_entry\n"
    "NVRM: GPU at PCI:0000:02:00: GPU boot sick\n"
    "smartd[2110]: Device /dev/nvme0 smart status: critical warning"
)
apparmor_prompt = (
    "systemd[1]: strata.service: Scheduled restart job\n"
    "strata[5510]: cannot open /data/models/IQ3_S/native.gguf: No such file or directory\n"
    "kernel: audit: type=1400 apparmor=\"DENIED\" operation=\"open\"\n"
    "kernel: nvme0: reserved requests exhausted"
)

cases = [
    task("F-oom", "oom", oom_prompt,
         {"cause": "OOM", "component": "оперативная память",
          "safe": ["free", "dmesg", "journalctl"], "decoy": "nvme"}),
    task("F-disk", "diskfull", disk_prompt,
         {"cause": "место", "component": "диск",
          "safe": ["df", "du", "journalctl --vacuum", "clean", "место"], "decoy": "out of memory"}),
    task("F-nvme", "nvme", nvme_prompt,
         {"cause": "nvme", "component": "SSD",
          "safe": ["smartctl", "nvme", "dmesg", "df", "backup"], "decoy": "gpu"}),
    task("F-apparmor", "service_restart", apparmor_prompt,
         {"cause": "apparmor", "component": "права доступа",
          "safe": ["apparmor", "aa-status", "journalctl"], "decoy": "nvme"}),
]

answers = [
    "ПРИЧИНА: нехватка оперативной памяти (OOM) при работе процесса strata\n"
    "КОМПОНЕНТ: процесс strata\n"
    "ШАГИ: анализ дампа ядра, лимиты cgroup, мониторинг потребления",

    "ПРИЧИНА: нехватка дискового пространства, файловая система read-only\n"
    "КОМПОНЕНТ: файловая система nvme0n1p2\n"
    "ШАГИ: проверка службы, анализ журнала systemd, проверка температуры CPU",

    "ПРИЧИНА: сбой NVMe, timeouts и EXT4\n"
    "КОМПОНЕНТ: процесс strata / GPU\n"
    "ШАГИ: перезапуск службы, проверка логов, проверка GPU",

    "ПРИЧИНА: отказ доступа из-за AppArmor и исчерпанию ресурсов NVMe\n"
    "КОМПОНЕНТ: Служба strata и AppArmor\n"
    "ШАГИ: Проверить модуль AppArmor, проверить файл, проанализировать логи NVMe",
]

fails = 0
for t, raw in zip(cases, answers):
    before, before_fmt, before_notes = CK.check_F(t, raw)
    norm, ev = GR.f_diagnostic_normalize(t, raw)
    after, fmt, notes = CK.check_F(t, norm)
    print(f"{t['id']}: {before:.3f} {before_notes} -> {after:.3f} {notes} fmt={fmt} events={ev}")
    if after < 0.999999 or not fmt or not ev:
        fails += 1
        print(norm)

# A complete answer should not receive a redundant safe-step token.
good = task("F-good", "oom", oom_prompt,
            {"cause": "OOM", "component": "оперативная память",
             "safe": ["free", "dmesg", "journalctl"], "decoy": "nvme"})
answer = "ПРИЧИНА: OOM\nКОМПОНЕНТ: оперативная память\nШАГИ: free, dmesg, journalctl"
norm, ev = GR.f_diagnostic_normalize(good, answer)
score, fmt, notes = CK.check_F(good, norm)
if score < 0.999999 or not fmt or ev:
    fails += 1
    print("GOOD REGRESSION", score, notes, ev, norm)

print("RESULT", "PASS 8/8" if fails == 0 else f"FAIL {fails}")
sys.exit(1 if fails else 0)
