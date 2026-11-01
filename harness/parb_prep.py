# -*- coding: utf-8 -*-
"""Калибровка токенов через сам API (без /tokenize) и подготовка банка к прогону."""
import json, os, subprocess, time, urllib.request

ROOT = os.path.expanduser("~/parb")
API = "http://127.0.0.1:8080/v1/chat/completions"
MODEL = "qwen3.8-flash-next-iq3_s"
SEED0 = 20261031
COUNTS = {"A": {"easy": 2, "medium": 4, "hard": 6, "veryhard": 4},
          "B": {"easy": 1, "medium": 4, "hard": 5, "veryhard": 3},
          "C": {"easy": 2, "medium": 4, "hard": 6, "veryhard": 4},
          "D": {"easy": 1, "medium": 3, "hard": 4, "veryhard": 2},
          "E": {"easy": 2, "medium": 4, "hard": 5, "veryhard": 3},
          "F": {"easy": 1, "medium": 3, "hard": 4, "veryhard": 2},
          "H": {"easy": 1, "medium": 4, "hard": 5, "veryhard": 3},
          "I": {"easy": 1, "medium": 4, "hard": 5, "veryhard": 3},
          "J": {"easy": 1, "medium": 4, "hard": 5, "veryhard": 3},
          "K": {"easy": 1, "medium": 4, "hard": 5, "veryhard": 3}}
G_SPECS = [("easy", 1000), ("easy", 1000), ("easy", 1000),
           ("medium", 4000), ("medium", 4000), ("medium", 4000), ("medium", 4000),
           ("hard", 8000), ("hard", 8000), ("hard", 8000), ("hard", 8000),
           ("veryhard", 16000), ("veryhard", 16000), ("veryhard", 32000), ("veryhard", 32000)]
EXTRA = {"B": {"veryhard": ["mt1024", "mt2048"]}, "J": {"veryhard": ["mt1024"]},
         "A": {"veryhard": ["mt1024"]}}


CFG = os.path.expanduser("~/Strata/strata-iq3_s-3060.json")


def api_key():
    try:
        return json.load(open(CFG)).get("api_key") or ""
    except Exception:
        return ""


def headers():
    h = {"Content-Type": "application/json"}
    k = api_key()
    if k:
        h["Authorization"] = "Bearer " + k
    return h


def probe(text):
    body = {"model": MODEL, "messages": [{"role": "user", "content": text}], "temperature": 0.7,
            "max_tokens": 1, "stream": False}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=headers())
    j = json.loads(urllib.request.urlopen(req, timeout=600).read())
    return j["usage"]["prompt_tokens"]


FILLER_TXT = "В отчёте за квартал филиал Таллин обновил регламент %d: подача заявок идёт через очередь, " \
    "согласование занимает 3 рабочих дня, архив хранится 12 месяцев."


def calibrate():
    a = probe("Счёт.")
    txt40 = "\n".join(FILLER_TXT % i for i in range(1, 41))
    b = probe(txt40)
    per = (b - a) / 40.0
    cpl = len(txt40) / float(max(b - a, 1))
    c = probe("Лимит расходов филиала Таллин, пункт 12 — сколько евро?")
    return {"probe_overhead_tokens": a, "tokens_per_filler_unit": round(per, 3),
            "chars_per_token_ru": round(cpl, 3), "probe_question_tokens": c, "n_units_measured": 40}


def isolation_probe():
    ok = subprocess.run(["unshare", "-rn", "true"], capture_output=True, text=True)
    return {"unshare_ok": ok.returncode == 0, "detail": (ok.stderr or "").strip()[:150],
             "method": "unshare -rn + setrlimit + запрещённые модули" if ok.returncode == 0
             else "setrlimit + запрещённые модули (без сетевого namespace: пользовательские namespace запрещены)"}


def main():
    os.makedirs(ROOT, exist_ok=True)
    meta = {"created": time.strftime("%F %T"), "model": MODEL, "bank_seed": SEED0,
            "health": subprocess.run(["curl", "-s", "-m", "5", "http://127.0.0.1:8080/health"],
                                     capture_output=True, text=True).stdout[:100],
            "engine_version": subprocess.run(
                ["sh", "-c", "ls ~/Strata-data/engines 2>/dev/null || true"],
                capture_output=True, text=True).stdout.strip()[:120]}
    for f in ("~/Strata/strata-iq3_s-3060.json", "~/Strata/run-iq3_s-3060.sh"):
        pp = os.path.expanduser(f)
        try:
            meta[f.replace("~/", "")] = open(pp).read()
        except Exception:
            meta[f.replace("~/", "")] = "unavailable"
    meta["meminfo_head"] = "".join(open("/proc/meminfo").readlines()[:3]).strip()
    meta["calibration"] = calibrate()
    meta["isolation"] = isolation_probe()

    tasks = B.build(SEED0, COUNTS)
    per = meta["calibration"]["tokens_per_filler_unit"]
    cpl = meta["calibration"]["chars_per_token_ru"]
    gtasks = []
    for i, (lvl, size) in enumerate(G_SPECS):
        sd = (SEED0 + 90000 + i * 7) % 10**6
        g = B.gen_G(sd, lvl, size)[0]
        known = "\n".join(g["head_units"] + g["mid_units"] + g["tail_units"] + [g["prompt"]])
        est_known = len(known) / float(cpl)
        need = max(0, int(round((size - est_known) / max(per, 0.1))))
        cities = ["Таллин", "Рига", "Вильнюс", "Хельсинки", "Гамбург", "Милан", "Турин", "Варшава"]
        fillers = ["В отчёте за квартал филиал %s обновил регламент %d: подача заявок идёт через очередь, "
                   "согласование занимает %d рабочих дня, архив хранится %d месяца."
                   % (cities[j % 8], 1000 + j, (j % 7) + 1, (j % 11) + 6) for j in range(need)]
        half = need // 2
        g["assembled_doc"] = "\n".join(g["head_units"] + fillers[:half] + g["mid_units"] +
                                       fillers[half:] + g["tail_units"])
        g["target_tokens"], g["filler_units"] = size, need
        g.update({"cat": "G", "level": lvl, "seed": sd, "stage": 5, "kind": "longctx",
                  "id": "G-%s-%02d" % (lvl[:2], i), "units": "longctx"})
        gtasks.append(g)
    tasks = [t for t in tasks if t["cat"] != "G"] + gtasks
    for t in tasks:
        t["stage"] = B.stage_of(t)
        t["extra_series"] = EXTRA.get(t["cat"], {}).get(t["level"], [])
        t["env"] = {"unshare_ok": meta["isolation"]["unshare_ok"]}
    tasks.sort(key=lambda t: (t["cat"], t["id"]))

    vbad = VR.verify(tasks)
    sfail = SF.run(tasks)
    plan = PL.build(tasks)
    meta.update({"bank_hash": B.bank_hash(tasks), "plan_hash": PL.plan_hash(plan),
                 "n_tasks": len(tasks), "n_plan_requests": len(plan),
                 "by_cat": {c: len([t for t in tasks if t["cat"] == c]) for c in sorted({t["cat"] for t in tasks})},
                 "by_level": {l: len([t for t in tasks if t["level"] == l]) for l in B.LEVELS},
                 "ref_verify_mismatches": vbad, "self_check_fails": sfail})
    json.dump(tasks, open(os.path.join(ROOT, "bank.json"), "w"), ensure_ascii=False)
    json.dump(plan, open(os.path.join(ROOT, "plan.json"), "w"), ensure_ascii=False)
    json.dump(meta, open(os.path.join(ROOT, "bank.meta.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(meta, ensure_ascii=False, indent=1)[:4000])
    if vbad or sfail:
        print("ВНИМАНИЕ: самопроверка или сверка эталонов не прошли — прогон не запускать до починки")


import parb_bank as B, parb_verify as VR, parb_self as SF, parb_plan as PL

if __name__ == "__main__":
    main()
