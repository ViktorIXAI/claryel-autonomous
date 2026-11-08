#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch and normalize public benchmarks into one task shape we can run and re-run.

Owner decision 08.11: the hard-bank contour line is FROZEN at the measured stable stamp; the
new workstream runs PUBLIC benchmarks (simple first) with the same publication discipline:
a pinned task file, deterministic scoring, arm answers stored as bytes, a percent row per run.

Normalized task (JSONL, one per line):
  id        stable task id ("<bench>-<n>")
  bench     benchmark name
  prompt    the exact text sent to the model (no template magic after prep)
  gold      reference answer as published
  checker   deterministic scorer to use: exact | number | letter | pytest | ifeval
  meta      benchmark-specific extras (choices, instruction ids, test/entry point)

Sources are pinned by URL + sha16 in MANIFEST.json; a re-run that changes bytes is a new
benchmark VERSION, never an in-place edit (same rule as the hard bank).
"""
import gzip
import hashlib
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "benchmarks", "public")
HF = "https://datasets-server.huggingface.co/rows"


def sha16(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]


def fetch(url, dst, timeout=120):
    if not os.path.exists(dst):
        with urllib.request.urlopen(url, timeout=timeout) as r, open(dst, "wb") as fh:
            fh.write(r.read())
    return dst


def hf_rows(dataset, config, split, dst, total=None):
    """datasets-server pages 100 rows; public datasets need no auth. The endpoint throws
    intermittent 5xx, so each page is retried before the fetch is called a failure. The raw
    JSONL on disk is the cache: once a split is fully downloaded, re-running the prep does not
    re-page the hub (429 lesson from the ARC + GPQA pass)."""
    if os.path.exists(dst) and os.path.getsize(dst) > 0 and not os.environ.get("PUB_FETCH_FORCE"):
        print("  cached %s (%d rows)"
              % (os.path.basename(dst), sum(1 for l in open(dst, encoding="utf-8") if l.strip())))
        return dst
    rows, off = [], 0
    while True:
        u = "%s?dataset=%s&config=%s&split=%s&offset=%d&limit=100" % (
            HF, urllib.parse.quote(dataset), config, split, off)
        data = None
        for attempt in range(4):
            try:
                with urllib.request.urlopen(u, timeout=120) as r:
                    data = json.load(r)
                break
            except Exception as exc:                      # noqa: BLE001 - retry then surface
                if attempt == 3:
                    raise
                wait = 10 * (attempt + 1) if "429" in str(exc) else 3 * (attempt + 1)
                print("  page offset %d: %s - retrying in %ds" % (off, exc, wait))
                time.sleep(wait)
        chunk = data.get("rows") or []
        # the hub wraps rows as {"row_idx": i, "row": {...}}, but some builders return the row
        # objects directly; a bare string row means the response shape changed and we must not
        # silently feed garbage into a normaliser.
        for x in chunk:
            if isinstance(x, dict):
                rows.append(x.get("row", x))
            else:
                raise SystemExit("unexpected rows shape at offset %d in %s: %r"
                                 % (off, dataset, str(x)[:80]))
        off += len(chunk)
        time.sleep(1.0)
        if not chunk or (total and off >= total) or (not total and len(chunk) < 100):
            break
    with open(dst, "w", encoding="utf-8") as fh:
        for x in rows:
            fh.write(json.dumps(x, ensure_ascii=False) + "\n")
    return dst


def gsm8k(raw, out):
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for line in open(raw, encoding="utf-8"):
            d = json.loads(line)
            gold = d["answer"].split("####")[-1].strip()
            fh.write(json.dumps({
                "id": "gsm8k-%04d" % n, "bench": "gsm8k",
                "prompt": d["question"].strip() + "\n\n"
                          "Put the final numeric answer on the last line as: ANSWER: <number>",
                "gold": gold, "checker": "number", "meta": {}}, ensure_ascii=False) + "\n")
            n += 1
    return n


def arc(raw, out, bench, level):
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for line in open(raw, encoding="utf-8"):
            d = json.loads(line)
            labels, texts = d["choices"]["label"], d["choices"]["text"]
            opts = "\n".join("%s. %s" % (l, t) for l, t in zip(labels, texts))
            fh.write(json.dumps({
                "id": "%s-%04d" % (bench, n), "bench": bench,
                "prompt": "%s\n%s\n\nAnswer with exactly one option letter." % (d["question"], opts),
                "gold": d["answerKey"], "checker": "letter",
                "meta": {"level": level, "options": len(labels)}}, ensure_ascii=False) + "\n")
            n += 1
    return n


def humaneval(raw, out):
    n = 0
    with gzip.open(raw, "rt", encoding="utf-8") as src, open(out, "w", encoding="utf-8") as fh:
        for d in src:
            d = json.loads(d)
            fh.write(json.dumps({
                "id": "humaneval-%04d" % n, "bench": "humaneval",
                "prompt": d["prompt"], "gold": d["canonical_solution"], "checker": "pytest",
                "meta": {"task_id": d["task_id"], "test": d["test"],
                         "entry_point": d["entry_point"]}}, ensure_ascii=False) + "\n")
            n += 1
    return n


def ifeval(raw, out):
    n = 0
    for line in open(raw, encoding="utf-8"):
        d = json.loads(line)
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({
                "id": "ifeval-%04d" % n, "bench": "ifeval",
                "prompt": d["prompt"], "gold": "", "checker": "ifeval",
                "meta": {"instruction_id_list": d["instruction_id_list"],
                         "kwargs": d.get("kwargs", [])}}, ensure_ascii=False) + "\n")
        n += 1
    return n


def gpqa(raw, out):
    """GPQA-Diamond (198) as MCQ. This mirror carries the four options inline in `question`
    (a) .. (d)) and the correct option text in `answer`; the gold letter is derived by matching
    the option text, never by guessing."""
    n = 0
    with open(out, "w", encoding="utf-8") as fh:
        for i, line in enumerate(open(raw, encoding="utf-8")):
            r = json.loads(line)
            q = (r.get("question") or "").strip()
            ans = (r.get("answer") or "").strip()
            opts = dict(re.findall(r"(?m)^([a-d])\)\s*(.+)$", q))
            gold = None
            if ans.upper() in ("A", "B", "C", "D"):
                gold = ans.upper()
            else:
                na = re.sub(r"\s+", " ", ans).strip().lower()
                for k, v in opts.items():
                    if re.sub(r"\s+", " ", v).strip().lower() == na:
                        gold = k.upper()
                        break
            if gold is None:
                continue
            fh.write(json.dumps({"id": "gpqa-%03d" % i, "bench": "gpqa-diamond",
                                 "prompt": q + "\n\nReply with the single correct option on the "
                                              "last line exactly as: ANSWER: X",
                                 "gold": gold, "checker": "letter",
                                 "meta": {"n_opts": len(opts), "src": "fingertap/GPQA-Diamond "
                                                                      "(mirror of Idavidrein/gpqa)"}},
                                ensure_ascii=False) + "\n")
            n += 1
    return n


def ifeval_job(rawf, out):
    src = hf_rows("google-deepmind/ifeval", "default", "train", rawf, total=541)
    if os.path.exists(out):
        os.remove(out)
    return ifeval(src, out)


def main():
    os.makedirs(os.path.join(OUT, "raw"), exist_ok=True)
    raw = lambda f: os.path.join(OUT, "raw", f)
    man = {"schema": "pub-bench-v1", "sources": {}, "benches": {}}
    jobs = []
    g = fetch("https://raw.githubusercontent.com/openai/grade-school-math/master/"
              "grade_school_math/data/test.jsonl", raw("gsm8k-test.jsonl"))
    jobs.append(("gsm8k", gsm8k(g, os.path.join(OUT, "gsm8k.tasks.jsonl")), {
        "url": "openai/grade-school-math test.jsonl", "raw_sha16": sha16(g)}))
    he = fetch("https://raw.githubusercontent.com/openai/human-eval/master/data/HumanEval.jsonl.gz",
               raw("HumanEval.jsonl.gz"))
    jobs.append(("humaneval", humaneval(he, os.path.join(OUT, "humaneval.tasks.jsonl")), {
        "url": "openai/human-eval HumanEval.jsonl.gz", "raw_sha16": sha16(he)}))
    if len(sys.argv) > 1 and sys.argv[1] == "--net":
        out_ife = os.path.join(OUT, "ifeval.tasks.jsonl")
        net = [
            ("arc-easy", lambda: arc(hf_rows("allenai/ai2_arc", "ARC-Easy", "test",
                                             raw("arc-easy.jsonl")),
                                     os.path.join(OUT, "arc-easy.tasks.jsonl"),
                                     "arc-easy", "easy"),
             raw("arc-easy.jsonl"), "HF allenai/ai2_arc ARC-Easy test"),
            ("arc-challenge", lambda: arc(hf_rows("allenai/ai2_arc", "ARC-Challenge", "test",
                                                  raw("arc-challenge.jsonl")),
                                          os.path.join(OUT, "arc-challenge.tasks.jsonl"),
                                          "arc-challenge", "challenge"),
             raw("arc-challenge.jsonl"), "HF allenai/ai2_arc ARC-Challenge test"),
            ("gpqa-diamond", lambda: gpqa(hf_rows("fingertap/GPQA-Diamond", "default", "test",
                                                  raw("gpqa-diamond.jsonl")),
                                          os.path.join(OUT, "gpqa-diamond.tasks.jsonl")),
             raw("gpqa-diamond.jsonl"), "HF fingertap/GPQA-Diamond (mirror of Idavidrein/gpqa)"),
            ("ifeval", lambda: ifeval_job(raw("ifeval.jsonl"), out_ife), raw("ifeval.jsonl"),
             "HF google-deepmind/ifeval"),
        ]
        for name, fn, rawf, url in net:
            try:
                jobs.append((name, fn(), {"url": url, "raw_sha16": sha16(rawf)}))
            except Exception as exc:                      # noqa: BLE001 - partial fetch is a fact
                man["benches"][name] = {"tasks": 0, "fetch_error": str(exc)[:200]}
                print("%-14s FETCH FAILED: %s" % (name, str(exc)[:120]))
    for name, count, src in jobs:
        tf = os.path.join(OUT, "%s.tasks.jsonl" % name)
        man["benches"][name] = {"tasks": count, "tasks_sha16": sha16(tf)}
        man["sources"][name] = src
        print("%-14s %5d tasks  tasks_sha16 %s" % (name, count, man["benches"][name]["tasks_sha16"]))
    with open(os.path.join(OUT, "MANIFEST.json"), "w", encoding="utf-8") as fh:
        json.dump(man, fh, indent=2, ensure_ascii=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
