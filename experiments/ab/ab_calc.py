# -*- coding: utf-8 -*-
"""A/B: how to raise financial-math correctness on the same model and the same arena.
Variants (thinking off, a batch of 8 tasks x 5 repetitions):
V0 — the prompt from the main run, temperature 0.7 (paired baseline);
V1 — same prompt, temperature 0.2;
V2 — the model only itemises lines (qty x price), code computes the sums;
V3 — the model returns strict JSON lines, code computes the sums.
Scoring is independent: Decimal + cent rounding, reconciled against the bank reference."""
import json, os, re, sys, time, zlib, collections
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

os.environ.setdefault("PARB_THINKING", "off")
sys.path.insert(0, os.path.expanduser("~/parb"))
import parb_run as R

ROOT = os.path.expanduser("~/parb")
BANK = {t["id"]: t for t in json.load(open(os.path.join(ROOT, "bank.json")))}
TASKS = ["A-ea-00-0", "A-ea-01-0", "A-me-00-0", "A-me-01-0", "A-me-02-0", "A-me-03-0",
         "A-ha-00-0", "A-ha-02-0"]
PAT = re.compile(r"Позиция \d+: .*?, (\d+) шт\. по €([\d]+(?:[.,][\d]{1,2})?)")
TIMEBOX = 1500


def q2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dec(s):
    s = s.replace(",", ".").strip()
    try:
        return Decimal(s)
    except InvalidOperation:
        return None


def items_of(prompt):
    out = [(dec(n), dec(p)) for n, p in PAT.findall(prompt)]
    return [(n, p) for n, p in out if n is not None and p is not None]


def nums(txt):
    res = []
    for m in re.findall(r"\d[\d ]*\d(?:[.,]\d{1,2})?", (txt or "").replace("\u00a0", " ")):
        d = dec(m.replace(" ", ""))
        if d is not None:
            res.append(d)
    return res


def ref_totals(t):
    r = t["ref"]
    for k in ("sub", "disc", "after", "vat", "total"):
        if k not in r:
            return None
    return [Decimal(r[k]) for k in ("sub", "disc", "after", "vat", "total")]


def score_totals(t, ans):
    ref = ref_totals(t)
    if not ref:
        return None, None
    an = nums(ans)
    hits = [any(abs(a - x) <= Decimal("0.02") for a in an) for x in ref]
    return sum(hits) / float(len(hits)), all(hits)


V2_ADD = ("\nНе считай итоговые суммы. Для каждой позиции выпиши отдельной строкой: "
          "Позиция N: <кол-во> x <цена> = <произведение>")
V3_ADD = ('\nОтветь строго JSON без пояснений: {"items":[{"qty":<число>,"price":<число>},...]} '
          '— ровно по одной записи на каждую позицию счёта.')


def extract_items_v3(ans):
    m = re.search(r"\{.*\}", ans or "", re.S)
    if not m:
        return None, "no_json"
    try:
        j = json.loads(m.group(0))
    except Exception as e:
        return None, "json_parse:" + str(e)[:40]
    its = j.get("items")
    if not isinstance(its, list):
        return None, "no_items_key"
    out = []
    for it in its:
        if not isinstance(it, dict) or "qty" not in it or "price" not in it:
            return None, "bad_item"
        q = dec(str(it["qty"]))
        p = dec(str(it["price"]))
        if q is None or p is None:
            return None, "bad_number"
        out.append((q, p))
    return out, None


def extract_items_v2(ans):
    out = []
    for line in (ans or "").splitlines():
        m = re.search(r"(\d+)\s*(?:x|×|\*)\s*([\d.,]+)\s*=\s*([\d., ]+)", line)
        if m:
            q, p = dec(m.group(1)), dec(m.group(2))
            if q is not None and p is not None:
                out.append((q, p))
    return out


def main():
    t0 = time.monotonic()
    out = open(os.path.join(ROOT, "ab_results.jsonl"), "a")
    stat = collections.defaultdict(lambda: collections.Counter())
    for tid in TASKS:
        t = BANK[tid]
        ref_items = items_of(t["prompt"])
        for var in ("V0", "V1", "V2", "V3"):
            temp = 0.2 if var == "V1" else 0.7
            prompt = t["prompt"]
            if var == "V2":
                prompt = t["prompt"] + V2_ADD
            elif var == "V3":
                prompt = t["prompt"] + V3_ADD
            for rep in range(5):
                if time.monotonic() - t0 > TIMEBOX:
                    print("TIMEBOX", flush=True)
                    break
                seed = 550000 + zlib.crc32((tid + var).encode()) % 9999 + rep
                r = R.call_api([{"role": "user", "content": prompt}], 1024, seed)
                ans = r["text"]
                rec = {"task": tid, "variant": var, "rep": rep, "temp": temp,
                       "ptok": r["ptok"], "ctok": r["ctok"], "finish": r["finish"],
                       "ttft": r["ttft"], "total_s": round(r["el"], 2),
                       "answer": ans, "prompt": prompt}
                if var in ("V0", "V1"):
                    frac, full = score_totals(t, ans)
                    rec["totals_frac"], rec["totals_full"] = frac, bool(full)
                    stat[var]["full" if full else "part"] += 1
                else:
                    its = extract_items_v2(ans) if var == "V2" else extract_items_v3(ans)[0]
                    err = None if var == "V2" else extract_items_v3(ans)[1]
                    rec["extract_error"] = err
                    if its and len(its) == len(ref_items):
                        good = all(abs(a[0] - b[0]) < Decimal("0.001") and abs(a[1] - b[1]) < Decimal("0.001")
                                   for a, b in zip(its, ref_items))
                        sub = q2(sum(q * p for q, p in its))
                        rec["items_exact"] = good
                        rec["sum_by_code"] = str(sub)
                        rec["sum_ok"] = (ref_totals(t) is not None and abs(sub - ref_totals(t)[0]) <= Decimal("0.02"))
                        stat[var]["items_exact" if good else "items_wrong"] += 1
                        stat[var]["sum_ok" if rec["sum_ok"] else "sum_bad"] += 1
                    else:
                        rec["items_exact"] = False
                        rec["sum_ok"] = False
                        stat[var]["extract_fail"] += 1
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                out.flush()
                print("%s %s rep%d var=%s full=%s items=%s sumok=%s ctok=%s" % (
                    time.strftime("%T"), tid, rep, var, rec.get("totals_full"),
                    rec.get("items_exact"), rec.get("sum_ok"), r["ctok"]), flush=True)
    out.close()
    summ = {v: dict(stat[v]) for v in stat}
    json.dump({"summary": summ, "elapsed": round(time.monotonic() - t0, 1)},
              open(os.path.join(ROOT, "ab_summary.json"), "w"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False))


if __name__ == "__main__":
    main()
