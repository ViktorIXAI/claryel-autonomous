# -*- coding: utf-8 -*-
"""PARB runner. Читает bank.json + plan.json, идёт по этапам с временными боксами,
пишет results.jsonl (flush на запись), ведёт дедлайн 14400 с по wall-clock от старта
(монотонный внутри сессии) и стоп-гейты ресурсов.
"""
import json, os, time, sys, hashlib, signal, subprocess, urllib.request

ROOT = os.path.expanduser(os.environ.get("PARB_ROOT", "~/parb"))
API = os.environ.get("PARB_API", "http://127.0.0.1:8080/v1/chat/completions")
MODEL = os.environ.get("PARB_MODEL", "qwen3.8-flash-next-iq3_s")
TIMEOUT = 420
LIMIT = int(os.environ.get("PARB_LIMIT", "14400"))
STATEF = os.environ.get("PARB_STATE", "state.json")
RESULTS = os.path.join(ROOT, os.environ.get("PARB_RESULTS", "results.jsonl"))
NOBOX = os.environ.get("PARB_NOBOX", "0") == "1"
RUNTAG = os.environ.get("PARB_TAG", "")
SERIES = {"main": 512, "mt1024": 1024, "mt2048": 2048}
# режим-thinking задаётся переменной окружения: фаза 1 шла с thinking по умолчанию движка
THINKING_OFF = os.environ.get("PARB_THINKING", "off").lower() == "off"
KEYS = ["mem_avail_mb", "swap_used_mb", "dirty_kb", "nvme_rd_kbs", "nvme_wr_kbs", "vram_used_mb",
        "gpu_util", "gpu_power_w", "gpu_temp_c", "gpu_clk_mhz", "cpu_temp_c", "load1"]
sys.path.insert(0, ROOT)
import parb_check as CK
import parb_plan as PL
import parb_loop as LP


def log(m):
    s = "%s %s" % (time.strftime("%H:%M:%S"), m)
    print(s, flush=True)
    open(os.path.join(ROOT, "run.log"), "a").write(s + "\n")


def rj(p, d=None):
    return json.load(open(p)) if os.path.exists(p) else d


def save_state(st):
    tmp = os.path.join(ROOT, STATEF + ".tmp")
    json.dump(st, open(tmp, "w"), ensure_ascii=False)
    os.replace(tmp, os.path.join(ROOT, STATEF))


def done_keys():
    s = set()
    p = RESULTS
    if os.path.exists(p):
        for ln in open(p):
            try:
                r = json.loads(ln)
            except Exception:
                continue
            s.add((r.get("task"), r.get("rep"), r.get("series")))
    return s


def mem_avail_mb():
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) // 1024
    except Exception:
        pass
    return -1


def gpu_q():
    try:
        return subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu,power.draw,clocks.sm,memory.used,"
                                     "utilization.gpu", "--format=csv,noheader,nounits"],
                              capture_output=True, text=True, timeout=6).stdout.strip()
    except Exception:
        return ""


def gate():
    ma = mem_avail_mb()
    if ma < 700:
        return "low_mem_%dMB" % ma
    q = gpu_q()
    try:
        if int(q.split(",")[0]) > 89:
            return "gpu_temp_%sC" % q.split(",")[0]
    except Exception:
        pass
    try:
        h = subprocess.run(["curl", "-s", "-m", "5", "http://127.0.0.1:8080/health"],
                           capture_output=True, text=True, timeout=10).stdout
        if '"status"' not in h:
            return "engine_health_%s" % h[:40]
    except Exception as e:
        return "engine_unreachable_%s" % str(e)[:40]
    return None


def api_key():
    try:
        return json.load(open(os.path.expanduser("~/Strata/strata-iq3_s-3060.json"))).get("api_key") or ""
    except Exception:
        return ""


HDRS = {"Content-Type": "application/json"}
_k = api_key()
if _k:
    HDRS["Authorization"] = "Bearer " + _k


def call_api(msgs, mt, seed):
    body = {"model": MODEL, "messages": msgs, "temperature": 0.7, "max_tokens": mt,
            "stream": True, "seed": seed}
    if THINKING_OFF:
        # движок по умолчанию стримит reasoning_content; без этих параметров
        # условие «thinking выключен» не выполняется
        body["reasoning_effort"] = "none"
        body["chat_template_kwargs"] = {"enable_thinking": False}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=HDRS)
    t0 = time.monotonic()
    txt, rtxt, ptok, ctok, finish, err, ttft = "", "", None, None, None, None, None
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            for raw in resp:
                ln = raw.decode("utf-8", "ignore").strip()
                if not ln.startswith("data:"):
                    continue
                d = ln[5:].strip()
                if d == "[DONE]":
                    break
                try:
                    j = json.loads(d)
                except Exception:
                    continue
                ch = (j.get("choices") or [{}])[0]
                dl = ch.get("delta") or {}
                rs = dl.get("reasoning_content") or ""
                if rs:
                    rtxt += rs
                piece = dl.get("content") or ch.get("content") or ""
                if piece:
                    if ttft is None:
                        ttft = time.monotonic() - t0
                    txt += piece
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
                if j.get("usage"):
                    ptok = j["usage"].get("prompt_tokens", ptok)
                    ctok = j["usage"].get("completion_tokens", ctok)
    except Exception as e:
        err = ("%s: %s" % (type(e).__name__, e))[:200]
    return {"text": txt, "reasoning": rtxt, "ptok": ptok, "ctok": ctok, "finish": finish, "err": err,
            "ttft": ttft, "el": time.monotonic() - t0}


def telemetry(t0, t1):
    f = os.path.join(ROOT, "telem", "samp.csv")
    if not os.path.exists(f):
        return {"telemetry": "unavailable"}
    acc = {k: [] for k in KEYS}
    n = 0
    try:
        for ln in open(f):
            p = ln.strip().split(",")
            if len(p) < 13:
                continue
            try:
                ts = float(p[0])
            except Exception:
                continue
            if not (t0 - 1 <= ts <= t1 + 1):
                continue
            n += 1
            for i, k in enumerate(KEYS, start=1):
                try:
                    acc[k].append(float(p[i]))
                except Exception:
                    pass
    except Exception:
        return {"telemetry": "unreadable"}
    if not n:
        return {"telemetry": "no_samples"}
    out = {"samples": n}
    for k in KEYS:
        v = acc[k]
        if v:
            out[k] = {"min": round(min(v), 1), "avg": round(sum(v) / len(v), 1), "max": round(max(v), 1)}
    return out


def agent_loop(t, mt, seed, rec):
    msgs = [{"role": "system", "content": t["sys"]}, {"role": "user", "content": t["prompt"]}]
    steps, final = [], None
    agg = {"text": "", "ptok": 0, "ctok": 0, "ttft": None, "el": 0.0, "finish": None, "err": None}
    for i in range(t.get("max_steps", 6)):
        r = call_api(msgs, mt, seed + i)
        agg["ptok"] += r["ptok"] or 0
        agg["ctok"] += r["ctok"] or 0
        agg["el"] += r["el"]
        agg["ttft"] = agg["ttft"] if agg["ttft"] is not None else r["ttft"]
        agg["finish"] = r["finish"] or agg["finish"]
        agg["err"] = r["err"] or agg["err"]
        act = LP.parse_action(r["text"])
        steps.append({"step": i, "raw": r["text"][:400], "parsed": act})
        if act is None:
            break
        if "answer" in act:
            final = str(act.get("answer"))
            break
        obs = LP.mock_exec(t, str(act.get("tool", "")), str(act.get("arg", "")))
        steps.append({"mock": obs[:150]})
        msgs.append({"role": "assistant", "content": json.dumps(act, ensure_ascii=False)})
        msgs.append({"role": "user", "content": "РЕЗУЛЬТАТ ИНСТРУМЕНТА: " + obs})
    agg["text"] = final or ""
    rec["agent_steps"] = steps
    rec["agent_final"] = final
    return agg


def run_one(t, pos, done, st):
    key = (t["id"], pos["rep"], pos["series"])
    if key in done:
        return None
    g = gate()
    if g:
        log("СТОП-ГЕЙТ %s: пауза 90 с, повторная проверка" % g)
        time.sleep(90)
        g = gate()
        if g:
            st["stop_reason"] = g
            st["stopped_at"] = time.strftime("%F %T")
            save_state(st)
            log("испытания остановлены досрочно: %s" % g)
            raise SystemExit(3)
    mt = SERIES[pos["series"]]
    rec = {"task": t["id"], "rep": pos["rep"], "series": pos["series"], "rep_group": pos["rep_group"],
           "cat": t["cat"], "subcat": t.get("kind", ""), "level": t["level"], "seed": t["seed"],
           "run_tag": RUNTAG,
           "stage": pos["stage"], "gen": {"temperature": 0.7, "thinking": (not THINKING_OFF), "max_tokens": mt,
                                          "request_seed": pos["gseed"], "fresh_context": True},
           "prompt_sha256": hashlib.sha256(t["prompt"].encode()).hexdigest()[:16],
           "t_wall": time.time(), "elapsed_from_start": round(time.time() - st["start_wall"], 1)}
    w0 = time.time()
    if t["kind"] == "loop":
        r = agent_loop(t, mt, pos["gseed"], rec)
    else:
        content = (t.get("assembled_doc", "") + "\n\n" + t["prompt"]) if t.get("assembled_doc") else t["prompt"]
        msgs = ([{"role": "system", "content": t["sys"]}] if t.get("sys") else []) + \
               [{"role": "user", "content": content}]
        r = call_api(msgs, mt, pos["gseed"])
    rec["reasoning_chars"] = len(r.get("reasoning") or "")
    rec["reasoning_head"] = (r.get("reasoning") or "")[:200]
    rec.update({"answer": r["text"], "ptok": r["ptok"], "ctok": r["ctok"],
                "ttft_s": round(r["ttft"], 3) if r["ttft"] is not None else None,
                "total_s": round(r["el"], 3), "finish": r["finish"], "engine_error": r["err"],
                "truncated": r["finish"] == "length", "prompt_chars": len(t["prompt"]),
                "mem_avail_mb_at_start": mem_avail_mb()})
    if r["ctok"] and r["ttft"] is not None and (r["el"] - r["ttft"]) > 0.05:
        rec["decode_tps"] = round(r["ctok"] / (r["el"] - r["ttft"]), 2)
        if r["ptok"]:
            rec["prefill_tps"] = round(r["ptok"] / max(r["ttft"], 1e-6), 1)
    if r["ptok"] and t.get("target_tokens"):
        rec["ctx_target"] = t["target_tokens"]
        rec["ctx_ratio"] = round(r["ptok"] / float(t["target_tokens"]), 3)
    try:
        if t["kind"] == "loop":
            frac, fok, notes = LP.check_D_loop(t, rec)
        else:
            frac, fok, notes = CK.CHECK[t["cat"]](t, r["text"])
        rec["content"], rec["format_ok"], rec["notes"] = frac, fok, notes
    except Exception as e:
        rec["content"], rec["format_ok"], rec["notes"] = None, None, ["scorer_error"]
        rec["scorer_error"] = ("%s: %s" % (type(e).__name__, e))[:200]
    if r["err"]:
        rec["content"] = None
    rec["telemetry"] = telemetry(w0, time.time())
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    done.add(key)
    log("%s %-14s rep%-4s mt%-4d c=%-4s f=%s fin=%-6s %6.1fs ptok=%-6s ctok=%-4s %s %s" % (
        t["cat"], t["id"], pos["rep"], mt, ("%.2f" % rec["content"]) if rec["content"] is not None else "ERR",
        rec["format_ok"], rec["finish"] or "?", r["el"], r["ptok"], r["ctok"],
        ("ENGINE_ERR" if r["err"] else ""), ",".join((rec["notes"] or [])[:3])[:80]))
    return rec


def main():
    st = rj(os.path.join(ROOT, STATEF), None)
    if not st or not st.get("start_wall"):
        st = {"start_wall": time.time(), "start_clock": time.strftime("%F %T")}
        save_state(st)
    if not st.get("run_started_wall"):
        st["run_started_wall"] = time.time()
    deadline = st["start_wall"] + LIMIT
    tasks = json.load(open(os.path.join(ROOT, "bank.json")))
    if os.path.exists(os.path.join(ROOT, "bank_extra.json")):
        tasks += json.load(open(os.path.join(ROOT, "bank_extra.json")))
    plan = json.load(open(os.path.join(ROOT, os.environ.get("PARB_PLAN", "plan.json"))))
    meta = rj(os.path.join(ROOT, "bank.meta.json"), {})
    byid = {t["id"]: t for t in tasks}
    done = done_keys()
    log("старт: задач %d, позиций плана %d, уже выполнено %d, хеш банка %s, хеш плана %s" %
        (len(tasks), len(plan), len(done), meta.get("bank_hash"), meta.get("plan_hash")))
    cur = None
    for pos in plan:
        if time.time() >= deadline:
            log("ДЕДЛАЙН %d с истёк — новых запросов не начинаем" % LIMIT)
            break
        if (pos["task"], pos["rep"], pos["series"]) in done:
            continue
        box = PL.STAGE_BOX[pos["stage"]]
        box_end = st["start_wall"] + box[1]
        if not NOBOX and pos["stage"] != 1 and time.time() >= box_end:
            if cur != pos["stage"]:
                log("этап %d пропущен: время бокса уже вышло" % pos["stage"])
                cur = pos["stage"]
            continue
        if cur != pos["stage"]:
            cur = pos["stage"]
            st["current_stage"] = pos["stage"]
            save_state(st)
            log("=== этап %d (боксы %d..%d с от старта) ===" % (pos["stage"], box[0], box[1]))
        t = byid[pos["task"]]
        try:
            run_one(t, pos, done, st)
        except SystemExit:
            raise
        except Exception as e:
            log("СБОЙ ПОЗИЦИИ %s: %s" % (pos["task"], str(e)[:150]))
        if len(done) % 20 == 0:
            st["done"] = len(done)
            save_state(st)
    st["done"] = len(done)
    st["finished_at"] = time.strftime("%F %T")
    st["elapsed"] = round(time.time() - st["start_wall"], 1)
    save_state(st)
    log("прогон завершён: записей %d, длительность %.0f с, стоп-причина: %s" %
        (len(done), st["elapsed"], st.get("stop_reason", "нет")))


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(143))
    main()
