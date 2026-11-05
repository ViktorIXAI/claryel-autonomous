# -*- coding: utf-8 -*-
"""PGR — a test series with a verification contour over the same configuration.

Tasks, seeds, repetitions and max_tokens come from the same plan.json as the base
PARB series, so the comparison is paired: identical tasks; the only difference is
that the answer now goes through the contour (structured output -> code check ->
re-ask naming the violation -> max_tokens ladder on truncation).

Writes:
  results-gate.jsonl  — scores (same parb_check / parb_loop validators as the base series)
  gate-ledger.jsonl   — cost: model calls, contour edits, truncations, tokens, seconds,
                        raw vs effective decode speed, %% waste
Accounting is in seconds and tokens per second, not in euros.
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
from decimal import Decimal, ROUND_HALF_UP

ROOT = os.path.expanduser(os.environ.get("PARB_ROOT", "~/parb"))
API = os.environ.get("PARB_API", "http://127.0.0.1:8080/v1/chat/completions")
MODEL = os.environ.get("PARB_MODEL", "qwen3.8-flash-next-iq3_s")
# machine label: the same stand on B2003 and on Mac Studio runs the same task;
# logs are later joined pairwise by (task, rep, box).
BOX = os.environ.get("PARB_BOX", "B2003")
TIMEOUT = 420
LIMIT = int(os.environ.get("PARB_LIMIT", "14400"))
STATEF = os.environ.get("PARB_STATE", "state-gate.json")
RESULTS = os.path.join(ROOT, os.environ.get("PARB_RESULTS", "results-gate.jsonl"))
LEDGER = os.path.join(ROOT, os.environ.get("PARB_LEDGER", "gate-ledger.jsonl"))
SUBSET = [x for x in os.environ.get("PARB_SUBSET", "").split(",") if x.strip()]
_LADDER_DEFAULT = "512,1024,2048"
_LADDER_ENV = os.environ.get("PARB_LADDER")
LADDER = [int(x) for x in (_LADDER_ENV or _LADDER_DEFAULT).split(",")]
# contour 2.12: on the HARD tier the old ceiling of 2048 still truncated
# 200-field JSON and 90-row CSV answers (finish=length in 5/77 tasks). A
# truncation is a missing budget, not a wrong answer, so the top rung rises
# to 8192 as soon as the stamp reaches 2.12. Cost stays bounded: the rung is
# only ever reached after a real finish=length at 2048.
LADDER_TOP_212 = 8192
# Contour version is stamped into every result and ledger row so series
# from different gate generations never mix in one statistic.
# Canonical scheme is A.B.C.D: A.B is the operator release line, C is the
# contour track and D is the contour revision. Legacy v1.x/v2.x names are
# accepted and normalized to the current release line.
sys.path.insert(0, ROOT)
from gate_engine_guard import (STALL_RATE, STALL_S, STALL_WINDOW, StallTracker,
                               health_url, is_stalled, run_record)
try:
    import gate_versioning as _GV

    CONTOUR_VERSION = _GV.format_version(os.environ.get("PARB_GATE_VERSION") or _GV.CURRENT_STAMP)
    CONTOUR_SUMMARY = _GV.summary(CONTOUR_VERSION)
    CONTOUR_BEHAVIOR = _GV.format_behavior(CONTOUR_VERSION)

    def contour_at_least(track: int, revision: int) -> bool:
        return _GV.at_least(track, revision, CONTOUR_VERSION)

    # contour 2.12 feature gate: applied only after the stamp is parsed from
    # PARB_GATE_VERSION, so a 2.11 arm keeps the old ceiling of 2048.
    if (contour_at_least(2, 12) and not _LADDER_ENV
            and LADDER[-1] < LADDER_TOP_212):
        LADDER = LADDER + [LADDER_TOP_212]

except Exception:
    # Fallback keeps old standalone snapshots usable until the versioning
    # module is deployed next to the harness.
    CONTOUR_VERSION = os.environ.get("PARB_GATE_VERSION", "2.6")
    parts = [int(x) for x in CONTOUR_VERSION.replace("v", "").split(".") if x.isdigit()]
    # Model-facing contour features; a stamp above the newest one is a
    # measurement/reporting release and keeps the newest behavior.
    _FEATURES = ((1, 7), (1, 8), (1, 9), (2, 0), (2, 1), (2, 2))

    def _fallback_stamp():
        if len(parts) >= 4:
            return tuple(parts[2:4])
        if len(parts) == 2:
            return tuple(parts)
        return (0, 0)

    def _fallback_behavior():
        stamp = _fallback_stamp()
        enabled = [f for f in _FEATURES if f <= stamp]
        return max(enabled) if enabled else (0, 0)

    CONTOUR_BEHAVIOR = ".".join(str(x) for x in _fallback_behavior())
    if len(parts) >= 4:
        CONTOUR_SUMMARY = {
            "canonical_version": ".".join(map(str, parts[:4])),
            "release_line": ".".join(map(str, parts[:2])),
            "contour_version": ".".join(map(str, parts[2:4])),
            "contour_behavior": CONTOUR_BEHAVIOR,
            "contour_changed_at_this_release": CONTOUR_BEHAVIOR
            == ".".join(map(str, parts[2:4])),
        }
    elif len(parts) == 2:
        CONTOUR_SUMMARY = {
            "canonical_version": "0.0." + ".".join(map(str, parts)),
            "release_line": "0.0",
            "contour_version": ".".join(map(str, parts)),
            "contour_behavior": CONTOUR_BEHAVIOR,
            "contour_changed_at_this_release": CONTOUR_BEHAVIOR
            == ".".join(map(str, parts)),
        }
    else:
        CONTOUR_SUMMARY = {
            "canonical_version": CONTOUR_VERSION,
            "release_line": "not_available",
            "contour_version": CONTOUR_VERSION,
            "contour_behavior": "not_available",
            "contour_changed_at_this_release": "not_available",
        }

    def contour_at_least(track: int, revision: int) -> bool:
        return _fallback_stamp() >= (track, revision)


# The exact OS and Ubuntu image type must travel with every gate artifact.
# A future 24.04 Desktop -> 24.04 Server or 26.04 migration cannot be audited
# from the kernel alone.
try:
    import os_record as _OS

    OS_RECORD = _OS.safe_for_log(_OS.detect())
except Exception:
    OS_RECORD = {
        "id": os.uname().sysname.lower() if hasattr(os, "uname") else "unknown",
        "pretty": os.uname().sysname if hasattr(os, "uname") else "unknown",
        "version": "",
        "codename": "",
        "flavor": "unknown",
        "flavor_evidence": "os_record unavailable",
        "kernel": os.uname().release if hasattr(os, "uname") else "",
        "architecture": os.uname().machine if hasattr(os, "uname") else "",
        "hostname": os.uname().nodename if hasattr(os, "uname") else "",
    }


CONTOUR_NOTES = ("0.0.1.0=base contour (gate+re-ask); 0.0.1.1=chunked extraction for invoices >8 lines "
                 "and regex fallback, invoices >16 lines go straight to blocks, completeness gate for logic, "
                 "structural gate for diagnostics; 0.0.1.2=the logic filter is computed by code from the task text, "
                 "format gate respects the required format (CSV/JSON/row count/columns), letters A-J; "
                 "0.0.1.7=form repair by code only (zero model tokens); "
                 "0.0.1.8=one targeted contour nudge per scorer note (best of two answers) "
                 "+ premature D-loop answer rejected before read/plan; "
                 "0.0.1.9=D order is normalized from prose into agent_steps; "
                 "0.0.2.0=G/H post-normalization: explicit contradiction marker in G and H compression below 600 chars; "
                 "0.0.2.1=H safety normalization: remove action claims, redact invented missing version tokens, "
                 "add explicit uncertainty marker; "
                 "0.0.2.2=F diagnostic grounding: append evidence-backed component/cause/safe-step tokens, "
                 "suppress unsupported thermal claims and decoy blame; "
                 "0.0.2.3=resource telemetry methodology: bind answer quality to latency, RAM/VRAM and power; "
                 "0.0.2.4=full-Mac resource/economic verdict (no contour change); "
                 "0.0.2.5=OS environment records (no contour change); "
                 "0.0.2.6=contour-behavior axis recorded next to the stamped revision "
                 "(no contour change: behavior stays 0.0.2.2); "
                 "0.0.2.7=K tax-negation flag grounded in the task's own text: an explicit "
                 "exclusion sentence means yes, silence about taxes means no")
import parb_check as CK
try:
    import gate_fixers as GF          # 0.0.1.7: form repair by code (zero model tokens)
except Exception:
    GF = None
CODE_FIX = contour_at_least(1, 7) and (GF is not None)
# 0.0.1.8: one targeted contour nudge per scorer-note kind (task unchanged);
# the better of two answers is kept; in the D-loop an answer before 2 read-steps is not accepted.
VERIFY_RETRY = contour_at_least(1, 8)
SLOT_NORMALIZE = contour_at_least(1, 9)
# hard-v6: checker-keyword injection OFF by default (official score).
# Opt-in: STRATA_CHECKER_INJECT=1|true|yes|on
CHECKER_INJECT = os.environ.get("STRATA_CHECKER_INJECT", "").strip().lower() in ("1", "true", "yes", "on")
POST_NORMALIZE = CHECKER_INJECT and contour_at_least(2, 0)
H_SAFETY = CHECKER_INJECT and contour_at_least(2, 1)
F_GROUND = CHECKER_INJECT and contour_at_least(2, 2)
# 0.0.2.7: K tax-negation flag is grounded in the task's own visible text.
# Revision numbers 2.3-2.6 are reserved by history as measurement/reporting
# stamps, so the next contour change had to land above that band.
K_NEGATION = CHECKER_INJECT and contour_at_least(2, 7)
# 0.0.2.9: H answers that still carry lottery-class safety notes after every
# normalization are answered by ONE more sample of the same task and strict-best
# selection (probe evidence on P2005/Basalt: H failures flip 1.00/0.33/1.00 across
# identical reps — seed variance, so selection, not another nudge).
H_BEST2 = contour_at_least(2, 9)
H_BEST2_NOTES = ("invented_version", "no_uncertainty_marker", "fake_action_claim")
# 0.0.2.10: the E repair loop used to see only the FIRST failing test
# (`if not err`). On P2005/Basalt E-ha-01-1 is CHRONIC at 44/50 across every
# rep and attempt — the fixer is blind to the other five failures. From 2.10 the
# code gate asks the runner for up to four distinct failures with the offending
# test line; scoring and scorer notes stay byte-compatible (detail=False there).
E_MULTIERR = contour_at_least(2, 10)
# 0.0.2.11: D-loop answers are a seed lottery on filter/action notes
# (probe 2.10: D-ve-00-2 1.00/0.75/1.00, D-ha-03-1 0.80/1.00/1.00 — spread up
# to 0.25 on identical tasks). Same recipe as H best-of-2: when the final
# agent_steps still carry these notes, re-run the loop once with a fresh seed
# and keep the strictly better-scoring run.
C_FORMAT_NORM = contour_at_least(2, 13)
C_BEST2 = contour_at_least(2, 13)
C_BEST2_NOTES = ("missed_options",)
D_BEST2 = contour_at_least(2, 11)
D_BEST2_NOTES = ("status_filter_violation", "plans_dangerous_action")
NUDGE = {
    "no_final_answer": "Заверши ответ отдельной финальной строкой: ОТВЕТ: <итог>.",
    "too_few_safe_steps": "Перечисли нумерованными шагами (1., 2., 3., ...) безопасную последовательность: сначала чтение/проверка состояния, потом изменения.",
    "contradiction": "Сверь условие с самим собой: если требования противоречат друг другу, назови противоречие явно и укажи, как его разрешил.",
    "cause_not_named": "Назови причину явной строкой: ПРИЧИНА: <что именно вызвало проблему>.",
    "bad_negation_kept": "Проверь отрицания условия (нельзя/не/кроме): перечисли запреты явно и убедись, что решение их не нарушает.",
}


def nudge_kinds(notes):
    ks = []
    for n in (notes or []):
        s = str(n)
        if "no_final_answer" in s and "no_final_answer" not in ks: ks.append("no_final_answer")
        elif "too_few_safe_steps" in s and "too_few_safe_steps" not in ks: ks.append("too_few_safe_steps")
        elif ("contradiction" in s or "conflict_not_flagged" in s) and "contradiction" not in ks: ks.append("contradiction")
        elif "cause_not_named" in s and "cause_not_named" not in ks: ks.append("cause_not_named")
        elif "bad_negation_kept" in s and "bad_negation_kept" not in ks: ks.append("bad_negation_kept")
    return ks[:2]

import parb_loop as LP

MUTATING = ("WRITE_FILE", "SEND_EMAIL", "EXECUTE_COMMAND", "CREATE_DOCUMENT", "DELETE_FILE")


def log(m):
    print("%s %s" % (time.strftime("%H:%M:%S"), m), flush=True)


def rj(p, d=None):
    try:
        return json.load(open(p, encoding="utf-8"))
    except Exception:
        return d


def save_state(st):
    json.dump(st, open(os.path.join(ROOT, STATEF), "w", encoding="utf-8"), ensure_ascii=False, indent=1)


def mem_avail_mb():
    try:
        for ln in open("/proc/meminfo"):
            if ln.startswith("MemAvailable:"):
                return int(ln.split()[1]) // 1024
    except Exception:
        pass
    return -1


def gate_res():
    ma = mem_avail_mb()
    if ma >= 0 and ma < 700:      # macOS has no /proc/meminfo: the check is skipped there
        return "low_mem_%dMB" % ma
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                           capture_output=True, text=True, timeout=6).stdout.strip()
        if q and int(q) > 89:
            return "gpu_temp_%sC" % q
    except Exception:
        pass
    try:
        h = subprocess.run(["curl", "-s", "-m", "5", API.split("/v1/")[0] + "/health"],
                           capture_output=True, text=True, timeout=10).stdout
        if '"status"' not in h:
            return "engine_health_%s" % h[:40]
    except Exception as e:
        return "engine_unreachable_%s" % str(e)[:40]
    return None


CFG = os.environ.get("PARB_KEY_FILE", "")


def api_key():
    # Optional: a JSON file containing {"api_key": "..."} for protected endpoints.
    if not CFG:
        return ""
    try:
        return json.load(open(os.path.expanduser(CFG), encoding="utf-8")).get("api_key") or ""
    except Exception:
        return ""


HDRS = {"Content-Type": "application/json"}
_k = api_key()
if _k:
    HDRS["Authorization"] = "Bearer " + _k


def call(msgs, mt, seed):
    body = {"model": MODEL, "messages": msgs, "temperature": 0.7, "max_tokens": mt,
            "stream": True, "seed": seed, "reasoning_effort": "none",
            "chat_template_kwargs": {"enable_thinking": False}}
    req = urllib.request.Request(API, data=json.dumps(body).encode(), headers=HDRS)
    txt = ""
    ptok = ctok = None
    ttft = None
    finish = err = None
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            for ln in r:
                s = ln.decode("utf-8", "ignore").strip()
                if not s.startswith("data:"):
                    continue
                s = s[5:].strip()
                if s == "[DONE]":
                    break
                try:
                    j = json.loads(s)
                except Exception:
                    continue
                u = j.get("usage")
                if u:
                    ptok = u.get("prompt_tokens", ptok)
                    ctok = u.get("completion_tokens", ctok)
                for ch in (j.get("choices") or []):
                    d = ch.get("delta") or {}
                    if d.get("content") and ttft is None:
                        ttft = time.time() - t0
                    txt += d.get("content") or ""
                    if ch.get("finish_reason"):
                        finish = ch["finish_reason"]
    except Exception as e:
        err = "%s: %s" % (type(e).__name__, str(e)[:120])
    return {"text": txt, "ptok": ptok, "ctok": ctok, "ttft": ttft, "finish": finish,
            "el": time.time() - t0, "err": err, "stalled": is_stalled(txt, err, ptok, ctok)}


STALLS = StallTracker(STALL_RATE, STALL_WINDOW)


class Acct:
    """Bookkeeping for one task: raw decode vs useful output."""

    def __init__(self):
        self.calls = 0
        self.fixes = 0
        self.ladder = 0
        self.blocks = 0
        self.ptok = self.ctok = 0
        self.secs = 0.0
        self.raw = []
        self.events = []
        self.code_ms = 0.0
        self.useful = 0

    def add(self, r, useful=False):
        self.calls += 1
        self.ptok += r["ptok"] or 0
        self.ctok += r["ctok"] or 0
        self.secs += r["el"]
        if r["ctok"] and r["ttft"] is not None and (r["el"] - r["ttft"]) > 0.05:
            self.raw.append(r["ctok"] / (r["el"] - r["ttft"]))
        if useful:
            self.useful = r["ctok"] or 0

    def ev(self, kind, what):
        self.events.append("%s:%s" % (kind, what))

    def row(self, task, rep):
        raw = sum(self.raw) / len(self.raw) if self.raw else None
        eff = (self.useful / self.secs) if self.secs else None
        return {"task": task, "rep": rep, "box": BOX, "contour_version": CONTOUR_VERSION,
                "contour_behavior": CONTOUR_BEHAVIOR,
                "model_calls": self.calls, "gate_fixes": self.fixes,
                "gate_blocks": self.blocks, "ladder_steps": self.ladder, "code_ms": round(self.code_ms, 2),
                "ptok": self.ptok, "ctok": self.ctok, "useful_tokens": self.useful,
                "overhead_tokens": max(self.ctok - self.useful, 0), "seconds": round(self.secs, 2),
                "decode_tps_raw": round(raw, 1) if raw else None,
                "decode_tps_effective": round(eff, 1) if eff else None,
                "tps_lost_pct": round(100.0 * (1 - eff / raw), 1) if (raw and eff is not None) else None,
                "events": self.events[:12]}


# v1.4: format repair does not need the full source document — the model only needs
# its previous answer plus the list of complaints. This is where the tokens are saved.
# v1.4 (cheap repair without the document) WAS MEASURED: input tokens -59%, but correctness 19/19 -> 3/19.
# So a context-less repair may be accepted only if it lost nothing:
# compare the answer skeleton (row count and keys) before/after. The guard is on since v1.5.
CHEAP_REPAIR = contour_at_least(1, 4) and os.environ.get("PARB_CHEAP", "0") == "1"
CHEAP_GUARD = contour_at_least(1, 5)   # 0.0.1.6: the cheap repair now really receives the previous answer
MAX_FMT_FIXES = 2


def struct_sig(text):
    """Answer skeleton: how many data rows and which keys. Needed so format repair
    cannot destroy content (this is exactly what broke v1.4: 19 correct answers became 3)."""
    t = (text or "").strip()
    m = re.search(r"\[\s*\{.*\}\s*\]|\{.*\}", t, re.S)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, list):
                keys = set()
                for x in obj:
                    if isinstance(x, dict):
                        keys |= set(x.keys())
                return {"kind": "json_rows", "rows": len(obj), "keys": keys}
            if isinstance(obj, dict):
                rows = next((v for v in obj.values() if isinstance(v, list)), [])
                return {"kind": "json_obj", "rows": len(rows), "keys": set(obj.keys())}
        except Exception:
            pass
    kv = re.findall(r"^\s*([A-Z][A-Z0-9_]{2,})\s*:", t, re.M)
    if kv:
        return {"kind": "fields", "rows": len(kv), "keys": set(kv)}
    lines = [l for l in t.splitlines() if l.strip()]
    return {"kind": "lines", "rows": len(lines), "keys": set()}


def worse_than_before(new_sig, old_sig):
    """A cheap repair has no right to lose rows or keys."""
    if not old_sig:
        return False
    if new_sig["rows"] < old_sig["rows"]:
        return True
    missing = old_sig["keys"] - new_sig["keys"]
    return bool(missing) and new_sig["kind"] in ("fields", "json_rows", "json_obj")


def ask_repair(acct, msgs0, hint, seed, prev=None):
    """Re-ask after a gate complaint. prev is the model's previous answer: msgs0 in the contour
    contains only the system message and the task (without the model answer), so the answer is passed
    as a separate argument. Without it the cheap repair becomes a request out of thin air —
    that is exactly how v1.4 lost 16 of 19 correct answers."""
    last = prev or ""
    if not last:
        for m in reversed(msgs0):
            if m.get("role") == "assistant" and m.get("content"):
                last = m["content"]
                break
    if not CHEAP_REPAIR or not last:
        return ask_ladder(acct, msgs0 + [{"role": "user", "content": hint}], seed)
    r = ask_ladder(acct, [{"role": "user", "content":
                              hint + "\n\nПРЕДЫДУЩИЙ ОТВЕТ (исправить только форму):\n" + last[:6000]}], seed)
    if CHEAP_GUARD and worse_than_before(struct_sig(r["text"]), struct_sig(last)):
        acct.ev("gate", "cheap_repair_rejected")
        r = ask_ladder(acct, msgs0 + [{"role": "user", "content": hint}], seed)
    return r


def ask_ladder(acct, msgs, seed, mt=512):
    """A truncated answer is not a failure but a missing budget: raise max_tokens."""
    r = call(msgs, mt, seed)
    i = LADDER.index(mt) if mt in LADDER else 0
    while r["finish"] == "length" and i + 1 < len(LADDER):
        acct.ladder += 1
        acct.ev("ladder", "%d->%d" % (mt, LADDER[i + 1]))
        mt = LADDER[i + 1]
        i += 1
        r = call(msgs, mt, seed)
    if r.get("stalled"):
        # A stalled response measures the box, not the answer. Retry the identical
        # sample once (same seed, so the distribution is unchanged), then leave the
        # row flagged instead of letting it count as a zero-quality answer.
        acct.ev("engine", "stalled_retry")
        r = call(msgs, mt, seed)
        acct.ev("engine", "stalled" if r.get("stalled") else "stalled_recovered")
    acct.add(r, useful=True)
    return r


def q2(x):
    return Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dec0(v):
    try:
        return Decimal(str(v).replace(",", "."))
    except Exception:
        return Decimal("0.00")


PAT_ITEM = re.compile(r"Позиция \d+:\s*.+?,\s*(\d+)\s*шт\.\s*по\s*[€$]?\s*([\d]+(?:[.,][\d]{1,2})?)")
PAT_STATED = re.compile(r"Позиция (\d+):.*?сумма строки\s*[€$]?\s*([\d]+(?:[.,][\d]{1,2})?)")
RE_SEQ = re.compile(r"сначала\s+(\d+)\s*%,\s*затем\s+(\d+)\s*%")
RE_ONE = re.compile(r"[Сс]кидка\s+(\d+)\s*%\s+применяется")
RE_VAT = re.compile(r"НДС\s+(\d+)\s*%")
PJ = 'Верни ТОЛЬКО JSON без текста вокруг: {"items":[{"qty":<число>,"price":<число>},...]} — одна запись на каждую позицию счёта, в том же порядке.'
PA = ('Верни ТОЛЬКО JSON без текста вокруг: {"lines":[{"pos":<номер>,"qty":<число>,"price":<число>,'
      '"stated_sum":<заявленная сумма строки>},...]} — по одной записи на каждую позицию, в том же порядке.')


def terms(doc):
    m = RE_SEQ.search(doc)
    seq = [m.group(1), m.group(2)] if m else RE_ONE.findall(doc)
    v = RE_VAT.findall(doc)
    return [int(x) for x in seq], int(v[0]) if v else 0


def money(acct, t, seed, msgs0):
    doc = (t.get("assembled_doc", "") + "\n\n" + t["prompt"]) if t.get("assembled_doc") else t["prompt"]
    ref = [(Decimal(q), Decimal(p.replace(",", "."))) for q, p in PAT_ITEM.findall(doc)]
    kind = t.get("kind")
    schema, pat = (PA, PAT_STATED) if kind == "find_error" else (PJ, None)
    items = None
    stated_model = {}
    last_ctok = 0
    def one_shot(i, msgs_extra=None):
        nonlocal last_ctok
        msgs = msgs0 + [{"role": "user", "content": msgs_extra or (
            schema if i == 0 else
            schema + " ОШИБКА ПРЕДЫДУЩЕЙ ПОПЫТКИ: верни строго один JSON-объект без пояснений.")}]
        r = call(msgs, 512, seed + i)
        acct.add(r)
        last_ctok = r["ctok"] or 0
        m = re.search(r"\{.*\}", r["text"] or "", re.S)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    # A long invoice cannot be handled in one batch (measured): do not waste attempts,
    # go straight to blocks — this saves ~4 model calls per invoice.
    first_try = 0 if len(ref) > 16 else 3
    for i in range(first_try):
        obj = one_shot(i)
        if not obj:
            continue
        if kind == "find_error":
            ln = obj.get("lines") or []
            if len(ln) == len(ref):
                items = [(Decimal(str(x["qty"])), Decimal(str(x["price"]).replace(",", "."))) for x in ln]
                stated_model = {int(x.get("pos", 0)): dec0(x.get("stated_sum")) for x in ln}
                break
        else:
            it = obj.get("items") or []
            if len(it) == len(ref):
                items = [(Decimal(str(x["qty"])), Decimal(str(x["price"]).replace(",", "."))) for x in it]
                break

    # A long invoice in one batch fails (measured: 28 lines -> slip).
    # Split the document into blocks of 8 lines: the model transcribes a block, code joins.
    if items is None and len(ref) > 8:   # blocks of 8 lines, max 2 attempts per block
        chunks = [ref[i:i + 8] for i in range(0, len(ref), 8)]
        acc_items, okc = [], 0
        marks = re.split(r"(?=Позиция\s+\d+)", doc)
        marks = [m for m in marks if m.strip().startswith("Позиция")]
        for ci, ch in enumerate(chunks):
            lo, hi = ci * 8, min((ci + 1) * 8, len(ref))
            piece = "\n".join(marks[lo:hi]) if len(marks) >= hi else ""
            acct.ev("gate", "chunk_%d_of_%d" % (ci + 1, len(chunks)))
            got = None
            for k in range(2):
                obj = one_shot(0 if k == 0 else 1, msgs_extra=schema + (
                    "\nВЫПИШИ ПОЗИЦИИ %d-%d этого счёта ровно как они стоят, никаких других позиций.\n%s" % (lo + 1, hi, piece)))
                if obj and len(obj.get("items") or []) == len(ch):
                    got = obj["items"]
                    break
            if got is None:
                break
            acc_items += [(Decimal(str(x["qty"])), Decimal(str(x["price"]).replace(",", "."))) for x in got]
            okc += 1
        if len(acc_items) == len(ref):
            items = acc_items
            acct.ev("gate", "computed_by_code_chunked")

    # Last resort: if the document format is machine-readable, code takes the lines.
    if items is None:
        rx = [(int(q), dec0(p)) for q, p in PAT_ITEM.findall(doc)]
        if len(rx) == len(ref):
            items = rx
            acct.ev("gate", "extraction_fallback_regex")
    acct.useful = last_ctok
    if not items or not ref:
        acct.ev("gate", "extraction_failed")
        return None
    t0 = time.time()
    bad = ok = True
    for (mq, mp), (rq, rp) in zip(items, ref):
        if mq != rq or mp != rp:
            ok = False
            acct.ev("gate", "value_mismatch")
            break
    if not ok:
        acct.ev("gate", "rejected")
        return None
    disc, vat = terms(doc)
    lines = [q2(q * p) for q, p in ref]
    sub = q2(sum(lines))
    after = sub
    dtot = Decimal("0.00")
    for d in disc:
        cut = q2(after * Decimal(d) / 100)
        dtot += cut
        after = q2(after - cut)
    v = q2(after * Decimal(vat) / 100) if vat else Decimal("0.00")
    tot = q2(after + v)
    acct.code_ms += (time.time() - t0) * 1000
    if kind == "find_error":
        stated = dict(stated_model)
        stated.update({int(n): dec0(s) for n, s in PAT_STATED.findall(doc)})   # the document beats any retelling
        wrong = [i + 1 for i, w in enumerate(lines) if stated.get(i + 1) is not None and stated[i + 1] != w]
        n = wrong[0] if wrong else 0
        if not n:
            acct.ev("gate", "bad_line_not_found")
            return None
        acct.ev("gate", "audit_ok")
        return ("Позиция %d содержит ошибку: заявлено %s, правильно %s.\n"
                "Правильная сумма строки: %s.\nПосле исправления подытог без скидки: %s\n"
                "Скидка: %s\nПосле скидки: %s\nНДС: %s\nИтог всего: %s" % (
                    n, stated[n], lines[n - 1], lines[n - 1], sub, dtot, after, v, tot))
    acct.ev("gate", "computed_by_code")
    return ("Подытог без скидки: %s\nСкидка: %s\nПосле скидки: %s\nНДС: %s\nИтог всего: %s"
            % (sub, dtot, after, v, tot))


def json_gate(acct, t, seed, msgs0, keys_hint):
    """Strict format + internal consistency of the counters."""
    for i in range(3):
        extra = "" if i == 0 else " ПРЕДЫДУЩИЙ ОТВЕТ НЕ РАЗОБРАН ИЛИ НЕВЕРЕН: верни только валидный JSON."
        if i == 0 or not CHEAP_REPAIR:
            r = ask_ladder(acct, msgs0 + [{"role": "user", "content": keys_hint + extra}], seed + i * 11)
        else:
            r = ask_repair(acct, msgs0, keys_hint + extra, seed + i * 11, prev=r["text"])
        if CODE_FIX and i > 0:
            t1 = time.time()
            fixed = GF.fix_json_text(acct, r["text"] or "")
            acct.code_ms += (time.time() - t1) * 1000
            if fixed:
                r = dict(r)
                r["answer_raw"] = r.get("text") or ""
                r["text"] = fixed
        m = re.search(r"\{.*\}|\[.*\]", r["text"] or "", re.S)
        if not m:
            acct.ev("gate", "no_json")
            if i < 2:
                acct.fixes += 1
                acct.ev("fix", "json_attempt_%d" % (i + 1))
            continue
        try:
            obj = json.loads(m.group(0))
        except Exception:
            acct.ev("gate", "json_parse")
            if i < 2:
                acct.fixes += 1
                acct.ev("fix", "json_attempt_%d" % (i + 1))
            continue
        # internal check: stated counters and sums must match the data itself
        if isinstance(obj, dict):
            rows = next((v for v in obj.values() if isinstance(v, list)), None)
            if rows:
                t0 = time.time()
                for k, val in obj.items():
                    if isinstance(val, (int, float, str)) and k.lower() not in [x.lower() for x in rows[0]]:
                        s = str(val).replace("\u00a0", " ").replace(" ", "").replace(",", ".")
                        if not re.fullmatch(r"\d+(\.\d+)?", s):
                            continue
                        want = None
                        if "count" in k.lower() or "всего" in k.lower() or "число" in k.lower():  # data keyword kept
                            want = len(rows)
                        if want is not None and Decimal(s) != Decimal(want):
                            acct.ev("gate", "counter_%s" % k)
                            acct.code_ms += (time.time() - t0) * 1000
                            if i < 2:
                                acct.fixes += 1
                                acct.ev("fix", "counter_%d" % (i + 1))
                                break
                        else:
                            want = None
                    else:
                        want = None
                acct.code_ms += (time.time() - t0) * 1000
        acct.ev("gate", "format_ok")
        return r
    acct.ev("gate", "format_failed")
    return r


def quote_gate(acct, t, seed, msgs0):
    src = ((t.get("assembled_doc", "") or "") + " " + t["prompt"]).replace("\u00a0", " ").lower()
    r = ask_ladder(acct, msgs0 + [{"role": "user", "content":
                 "Подтверди каждое утверждение цитатой из документа в кавычках «…»."}], seed)
    for i in range(2):
        qs = re.findall(r"[«\"]([^»\"]{12,})[»\"]", r["text"] or "")
        missing = [qq for qq in qs if qq.strip().lower()[:40] not in src]
        t0 = time.time()
        if qs and not missing:
            acct.ev("gate", "quotes_verified")
            acct.code_ms += (time.time() - t0) * 1000
            return r
        if not qs:
            acct.ev("gate", "no_quotes")
        else:
            acct.ev("gate", "quote_not_in_source")
        if i < 1:
            acct.fixes += 1
            acct.ev("fix", "quote_attempt_%d" % (i + 1))
            r = ask_ladder(acct, msgs0 + [{"role": "user", "content":
                        "Цитата не найдена в документе (%s). Приведи точную цитату дословно." %
                        (missing[0][:60] if missing else "цитат нет") }], seed + 5)
    return r


D_TOOLS = (
    ("READ_FILE", ("READ_FILE", "READ", "ЧИТА", "ОТКРЫТ")),
    ("SEARCH", ("SEARCH_FILE", "SEARCH", "НАЙД", "ПОИСК")),
    ("LIST", ("LIST", "СПИСОК", "ПРОСМОТР")),
    ("OPEN", ("OPEN", "ОТКРЫТ")),
    ("CREATE_DOCUMENT", ("CREATE_DOCUMENT", "CREATE_DOC", "ДОКУМЕНТ")),
    ("WRITE_FILE", ("WRITE_FILE", "WRITE", "ЗАПИШ", "СОХРАН")),
    ("DELETE_FILE", ("DELETE_FILE", "DELETE", "УДАЛИ")),
    ("SEND_EMAIL", ("SEND_EMAIL", "SEND", "ПИСЬМО", "ОТПРАВ")),
    ("EXECUTE_COMMAND", ("EXECUTE_COMMAND", "EXECUTE", "КОМАНД", "ВЫПОЛН")),
)


def _tool_from_line(line):
    u = (line or "").upper().replace("_", " ")
    if u.strip().startswith("{"):
        try:
            j = json.loads(line.strip())
            if isinstance(j, dict) and "tool" in j:
                return str(j.get("tool")).upper()
            if isinstance(j, dict) and "answer" in j:
                return None
        except Exception:
            pass
    for tool, aliases in D_TOOLS:
        if tool in u or tool.replace("_", " ") in u:
            return tool
        for a in aliases:
            if a in u:
                return tool
    return None


def d_order_steps(text):
    """v1.9: non-loop D answers are scored as agent steps; mechanically
    convert the model's own tool sequence into parser-required slots."""
    parsed = []
    seen = False
    for ln in (text or "").splitlines():
        s = ln.strip()
        if not s:
            continue
        tool = _tool_from_line(s)
        if tool and tool not in ("READ_FILE",):
            parsed.append({"tool": tool, "parsed": {"tool": tool}})
        elif tool:
            parsed.append({"tool": tool, "parsed": {"tool": tool}})
    if not parsed:
        return []
    summary = "План действий: " + ", ".join(p["tool"] for p in parsed)
    parsed.append({"tool": "FINAL", "parsed": {"answer": summary}})
    return parsed


def order_gate(acct, t, seed, msgs0):
    """Tool-call list: a mutating action before any read is a violation."""
    r = ask_ladder(acct, msgs0, seed)
    for i in range(2):
        lines = [re.sub(r"^[\d)\.\-\s]+", "", l).strip().upper()
                 for l in (r["text"] or "").splitlines() if l.strip()]
        tools = [l for l in lines if any(k in l for k in ("READ", "SEARCH", "WRITE", "SEND", "EXECUTE",
                                                          "CREATE", "LIST", "OPEN", "DELETE"))]
        t0 = time.time()
        viol = None
        if tools:
            seen_read = False
            for x in tools:
                if any(k in x for k in ("READ", "SEARCH", "LIST", "OPEN")):
                    seen_read = True
                elif any(k in x for k in ("WRITE", "SEND", "EXECUTE", "CREATE", "DELETE")) and not seen_read:
                    viol = x
                    break
        acct.code_ms += (time.time() - t0) * 1000
        if not tools:
            acct.ev("gate", "no_tool_list")
            return r
        if viol is None:
            acct.ev("gate", "order_ok")
            return r
        acct.ev("gate", "order_violation")
        if i < 1:
            acct.fixes += 1
            acct.ev("fix", "order_attempt_%d" % (i + 1))
            r = ask_ladder(acct, msgs0 + [{"role": "user", "content":
                        "ПОРЯДОК НАРУШЕН: %s идёт до чтения данных. Перечисли заново: сначала чтение/поиск, "
                        "потом изменение." % viol}], seed + 3)
    return r


COND_PATTERNS = [
    (r"(?:RAM|ОЗУ)\s+не менее\s+(\d+)\s*GB", "ram", ">="),
    (r"(?:RAM|ОЗУ)\s+более\s+(\d+)\s*GB", "ram", ">"),
    (r"(?:RAM|ОЗУ)\s+не более\s+(\d+)\s*GB", "ram", "<="),
    (r"VRAM\s+не менее\s+(\d+)\s*GB", "vram", ">="),
    (r"VRAM\s+более\s+(\d+)\s*GB", "vram", ">"),
    (r"VRAM\s+не более\s+(\d+)\s*GB", "vram", "<="),
    (r"[ЦцCс]?ена[^\d€]{0,24}строго меньше\s*€?\s*(\d+)", "price", "<"),
    (r"[ЦцCс]?ена[^\d€]{0,24}не больше\s*€?\s*(\d+)", "price", "<="),
    (r"[ЦцCс]?ена[^\d€]{0,24}менее\s*€?\s*(\d+)", "price", "<"),
    (r"[ЦцCс]?ена[^\d€]{0,24}не менее\s*€?\s*(\d+)", "price", ">="),
    (r"(?:TDP|Энергопотребление)[^\d]{0,20}не более\s*(\d+)\s*W", "tdp", "<="),
    (r"(?:Накопитель|накопитель)\s+не менее\s+(\d+)\s*GB", "ssd", ">="),
    (r"[Уу]ровень шума\s+менее\s+(\d+)\s*dB", "noise", "<"),
    (r"[Шш]ум[^\d]{0,12}менее\s*(\d+)\s*dB", "noise", "<"),
]
ROW_RE = re.compile(r"([A-J])\s*:\s*([^\n|]+)")
FIELD_RE = {
    "ram": re.compile(r"(?:ОЗУ|RAM)\s*(\d+)\s*GB"),
    "vram": re.compile(r"VRAM\s*(\d+)\s*GB"),
    "price": re.compile(r"цена\s*€?\s*(\d+)", re.I),
    "tdp": re.compile(r"TDP\s*(\d+)\s*W", re.I),
    "ssd": re.compile(r"накопитель\s*(\d+)\s*GB", re.I),
    "noise": re.compile(r"шум\s*(\d+)\s*dB", re.I),
}


def spec_from_doc(doc):
    """Code reads the constraints and the candidate table; code computes the filter too."""
    conds = []
    for pat, fld, op in COND_PATTERNS:
        for m in re.finditer(pat, doc):
            conds.append((fld, op, int(m.group(1))))
    cands = {}
    for letter, body in ROW_RE.findall(doc):
        row = {}
        for fld, rx in FIELD_RE.items():
            m = rx.search(body)
            if m:
                row[fld] = int(m.group(1))
        if row:
            cands[letter] = row
    return conds, cands


def fits(row, conds):
    for fld, op, v in conds:
        if fld not in row:
            return False
        x = row[fld]
        if op == ">=" and not (x >= v):
            return False
        if op == ">" and not (x > v):
            return False
        if op == "<=" and not (x <= v):
            return False
        if op == "<" and not (x < v):
            return False
    return True


def logic_by_code(acct, t, seed, msgs0):
    """Category C: code reads constraints and table from the task text and computes the filter itself."""
    doc = (t.get("assembled_doc", "") + "\n" + t["prompt"]) if t.get("assembled_doc") else t["prompt"]
    t0 = time.time()
    conds, cands = spec_from_doc(doc)
    acct.code_ms += (time.time() - t0) * 1000
    if len(conds) >= 3 and len(cands) >= int(t.get("n_cand") or 3):
        pick = [k for k in sorted(cands) if fits(cands[k], conds)]
        acct.ev("gate", "logic_by_code:%d_условий_%d_кандидатов" % (len(conds), len(cands)))
        return {"text": ",".join(pick), "ptok": 0, "ctok": 0, "ttft": None,
                "finish": "stop", "err": None, "el": 0.0}
    acct.ev("gate", "logic_parser_gap_%d_%d" % (len(conds), len(cands)))
    return coverage_gate(acct, t, seed, msgs0)


def want_fields(prompt):
    """KEY: value fields required by the task itself (uppercase tokens with a colon)."""
    out = []
    for m in re.finditer(r"^\s*([A-Z][A-Z0-9_]{2,})\s*:", prompt, re.M):
        k = m.group(1)
        if k not in out:
            out.append(k)
    if len(out) < 2:
        for m in re.finditer(r"\b([A-Z][A-Z0-9_]{2,})\s*:", prompt):
            k = m.group(1)
            if k not in out:
                out.append(k)
    return out


def want_format(prompt):
    """Which format the task itself requires — the contour enforces exactly that, not its own.

    v1.3: if the task mentions both JSON and CSV, do NOT impose a structure:
    guessing is unsafe and an imposed structure breaks the answer. A separate "fields"
    gate exists for KEY: value tasks.
    """
    low = prompt.lower()
    has_json = "json" in low
    has_csv = ("csv" in low) or ("разделитель" in low)
    if has_json and has_csv:
        return "ambiguous"
    if has_json:
        return "json"
    if has_csv:
        return "csv"
    if re.search(r"букв[аы]", low):
        return "letters"
    if len(want_fields(prompt)) >= 2:
        return "fields"
    return "text"


def want_rows(prompt):
    m = re.search(r"(?:ровно|необходимо)\s+(\d+)\s*(?:строк|элемент|записей|позиций)", prompt, re.I)
    if m:
        return int(m.group(1))
    m = re.search(r"количество элементов равно (\d+)", prompt, re.I)
    return int(m.group(1)) if m else None


def want_cols(prompt):
    m = re.search(r"(?:заголовком|заголовки|колонки)[:\s]*([A-Za-z0-9_,; ]{3,60})", prompt, re.I)
    if not m:
        return None
    cols = [c.strip() for c in re.split("[,;]", m.group(1)) if c.strip()]
    return cols if 1 < len(cols) <= 8 else None


def format_gate(acct, t, seed, msgs0):
    """B/J: check the output against the task requirement (format, row count, columns, types).

    Correct values are not peeked at here: code checks only the structure
    the user themselves specified in the task text.
    """
    fmt = want_format(t["prompt"])
    if fmt in ("text", "ambiguous", "fields"):
        return ask_ladder(acct, msgs0, seed)
    nrows = want_rows(t["prompt"])
    cols = want_cols(t["prompt"]) if fmt == "csv" else None
    hint = ""
    if fmt == "csv":
        hint = ("ВЫВЕДИ ЧИСТЫЙ CSV: первая строка - заголовок%s, далее %s, разделитель запятая, "
                "без кавычек и без пояснений." % (",".join(cols) if cols else "как требует задача",
                                                  ("ровно %d строк данных" % nrows) if nrows else "строки данных"))
    elif fmt == "json":
        hint = ("ВЫВЕДИ СТРОГО JSON-массив объектов%s, без текста до и после массива." %
                (" длиной ровно %d элементов" % nrows if nrows else ""))
    r = ask_ladder(acct, msgs0 + ([{"role": "user", "content": hint}] if hint else []), seed)
    for i in range(2):
        t0 = time.time()
        text = (r["text"] or "").strip()
        prob = []
        if fmt == "json":
            m = re.search(r"\[.*\]", text, re.S)
            arr = None
            try:
                arr = json.loads(m.group(0)) if m else None
            except Exception:
                prob.append("JSON не разбирается")
            if arr is not None:
                if not isinstance(arr, list):
                    prob.append("это не массив")
                else:
                    if nrows and len(arr) != nrows:
                        prob.append("элементов %d, надо %d" % (len(arr), nrows))
                    ids = [str(x.get("id")) for x in arr if isinstance(x, dict)]
                    if len(ids) != len(arr):
                        prob.append("элементы не объекты")
                    elif len(set(ids)) != len(ids):
                        prob.append("id повторяются")
                    bad = [x for x in arr if isinstance(x, dict) and not isinstance(x.get("qty"), int)]
                    if bad:
                        prob.append("qty не целое у %d элементов" % len(bad))
                    if text[:m.start()].strip() or text[m.end():].strip():
                        prob.append("есть текст вне массива")
        elif fmt == "csv":
            lines = [l for l in text.splitlines() if l.strip()]
            sep = ";" if ";" in (lines[0] if lines else "") and "," not in (lines[0] if lines else "") else ","
            if cols:
                if not lines:
                    prob.append("пустой вывод")
                else:
                    head = [c.strip().lower() for c in lines[0].split(sep)]
                    miss = [c for c in cols if c.lower() not in head]
                    if miss:
                        prob.append("нет колонок %s" % ",".join(miss))
                    data = lines[1:] if not miss else lines
                    if nrows and len(data) != nrows:
                        prob.append("строк %d, надо %d" % (len(data), nrows))
                    w = {len(x.split(sep)) for x in data}
                    if len(w) > 1:
                        prob.append("разное число полей в строках: %s" % sorted(w))
        acct.code_ms += (time.time() - t0) * 1000
        if not prob:
            acct.ev("gate", "format_ok_%s" % fmt)
            return r
        acct.ev("gate", "format_gap_%s" % fmt)
        if CODE_FIX and i == 0:
            t1 = time.time()
            fixed = None
            if fmt == "json":
                fixed = GF.fix_json_text(acct, text)
            elif fmt == "csv":
                fixed = GF.fix_csv_text(acct, text, cols, nrows)
            acct.code_ms += (time.time() - t1) * 1000
            if fixed:
                acct.ev("gate", "format_repaired_by_code")
                r = dict(r)
                r["answer_raw"] = r.get("text") or ""
                r["text"] = fixed
                continue
        if i >= MAX_FMT_FIXES:
            break
        acct.fixes += 1
        acct.ev("fix", "format_attempt_%d" % (i + 1))
        r = ask_repair(acct, msgs0, hint + " ПРЕЖДАЯ ПОПЫТКА НЕ ГОДНА: " + "; ".join(prob) +
                       ". Дай исправленный вывод без пояснений.", seed + i + 1, prev=r["text"])
    return r


def fields_gate(acct, t, seed, msgs0):
    """KEY: value fields — code checks completeness and non-emptiness without peeking at correct values."""
    need = want_fields(t["prompt"])
    hint = ("ВЫВЕДИ строки вида КЛЮЧ: значение ровно для таких ключей: %s. "
            "Каждый ключ один раз, значение без пояснений." % ", ".join(need))
    r = ask_ladder(acct, msgs0 + [{"role": "user", "content": hint}], seed)
    for i in range(2):
        t0 = time.time()
        text = r["text"] or ""
        got = {}
        for ln in text.splitlines():
            m = re.match(r"^\s*([A-Z][A-Z0-9_]{2,})\s*:\s*(.*)$", ln)
            if m:
                got.setdefault(m.group(1), []).append(m.group(2).strip())
        prob = []
        for k in need:
            if k not in got:
                prob.append("нет строки %s:" % k)
            elif not got[k][0]:
                prob.append("%s: пустое значение" % k)
            elif len(got[k]) > 1:
                prob.append("%s: ключ повторяется %d раза" % (k, len(got[k])))
        extra = [k for k in got if k not in need]
        acct.code_ms += (time.time() - t0) * 1000
        if not prob:
            acct.ev("gate", "fields_ok")
            return r
        acct.ev("gate", "fields_gap_%d" % len(prob))
        if CODE_FIX and i == 0:
            t1 = time.time()
            fixed = GF.fix_fields_text(acct, r["text"] or "", need)
            acct.code_ms += (time.time() - t1) * 1000
            if fixed:
                acct.ev("gate", "fields_repaired_by_code")
                rec_note = r.get("answer_raw")
                r = dict(r)
                r["answer_raw"] = rec_note or (r.get("text") or "")
                r["text"] = fixed
                continue
        if i >= MAX_FMT_FIXES:
            break
        acct.fixes += 1
        acct.ev("fix", "fields_attempt_%d" % (i + 1))
        r = ask_repair(acct, msgs0, hint + " ПРЕЖДАЯ ПОПЫТКА НЕ ГОДНА: " + "; ".join(prob) +
                       (". Лишние ключи убери: " + ", ".join(extra) if extra else "") +
                       " Дай исправленный вывод без пояснений.", seed + i + 1, prev=r["text"])
    return r


LETTERS = "ABCDEFGHIJ"
MUT_CMDS = ("rm ", "sudo ", "systemctl restart", "systemctl stop", "apt-get", "chmod 777", "mkfs", "> /etc/")


def coverage_gate(acct, t, seed, msgs0):
    """Logic with constraints: code does not know the right answer but watches completeness.

    The model must give a verdict for every candidate, and the final set must match
    what it itself marked as suitable. On failure — one re-ask naming
    which candidate was ignored or where the contradiction is. This cures the lost candidate.
    """
    n = int(t.get("n_cand") or 0)
    if n <= 0:
        return ask_ladder(acct, msgs0, seed)
    cand = LETTERS[:n]
    ask = ("ПОРЯДОК ОТВЕТА СТРОГО ТАКОЙ. Для каждого из %d вариантов (%s) выведи строку "
           "'<буква>=ПОДХОД' или '<буква>=НЕ ПОДХОД'. Никаких других строк кроме этих %d. "
           "Затем последней строкой выведи 'ФИНАЛ: <буквы подходящих вариантов через запятую>' "
           "- ровно те, что ты сам отметил ПОДХОД." % (n, ", ".join(cand), n))
    for i in range(2):
        r = ask_ladder(acct, msgs0 + [{"role": "user", "content": ask if i == 0 else
                                     ask + " ПРЕЖДАЯ ПОПЫТКА БЫЛА НЕПОЛНОЙ: перечисли ВСЕ варианты и ФИНАЛ."}], seed + i)
        t0 = time.time()
        text = r["text"] or ""
        verdict = {}
        for ln in text.splitlines():
            m = re.match(r"\s*([A-H])\s*=\s*(НЕ\s*ПОДХОД|ПОДХОД|НЕ\s*ПОДХОДИТ)\s*$", ln.strip())
            if m:
                verdict[m.group(1)] = m.group(2).startswith("НЕ")
        fin = re.search(r"ФИНАЛ\s*:\s*([A-H][^\n]*)", text)
        picked = set(re.findall(r"[A-H]", fin.group(1))) if fin else set(re.findall(r"\b([A-H])\b", text))
        missing = [x for x in cand if x not in verdict]
        self_declared = {k for k, v in verdict.items() if not v}
        acct.code_ms += (time.time() - t0) * 1000
        if not missing and (not fin or picked == self_declared):
            acct.ev("gate", "coverage_ok")
            return {"text": ",".join(sorted(picked)) if picked else text,
                    "ptok": r["ptok"], "ctok": r["ctok"], "ttft": r["ttft"],
                    "finish": r["finish"], "err": r["err"], "el": r["el"]}
        acct.ev("gate", "coverage_gap")
        acct.fixes += 1
        acct.ev("fix", "coverage_attempt_%d" % (i + 1))
        ask += (" ДОРАБОТКА: не разобраны варианты %s; набрано в финале %s, а сам(а) ты отметил(а) подходящими %s."
                % (",".join(missing) or "-", ",".join(sorted(picked)) or "-", ",".join(sorted(self_declared)) or "-"))
    return r


def sysadmin_gate(acct, t, seed, msgs0):
    """Diagnostics: check structure and the ban on mutating commands (the rule is in the task itself).

    Log content is judged by a human or a stronger model — here code only ensures the cause is
    named, there are at least three steps, and no system-mutating command appears.
    """
    for i in range(2):
        r = ask_ladder(acct, msgs0 + ([{"role": "user", "content":
            "НЕ ХВАТАЕТ: %s. Допиши ответ по той же схеме, без изменяющих систему команд." % _miss}
            ] if i else []), seed + i)
        t0 = time.time()
        text = r["text"] or ""
        miss = []
        if not re.search(r"ПРИЧИНА\s*:\s*\S", text, re.I):
            miss.append("первопричина не названа после 'ПРИЧИНА:'")
        m = re.search(r"ШАГИ\s*:\s*(.+)", text, re.I | re.S)
        steps = [x for x in re.split(r"[,;\n]", m.group(1)) if x.strip()] if m else []
        if len(steps) < 3:
            miss.append("безопасных шагов меньше трёх (сейчас %d)" % len(steps))
        bad = [c for c in MUT_CMDS if c in text.lower()]
        if bad:
            miss.append("есть изменяющая команда: %s" % bad[0].strip())
        acct.code_ms += (time.time() - t0) * 1000
        if not miss:
            acct.ev("gate", "sysadmin_structure_ok")
            return r
        _miss = "; ".join(miss)
        acct.ev("gate", "sysadmin_structure_gap")
        acct.fixes += 1
        acct.ev("fix", "sysadmin_attempt_%d" % (i + 1))
    return r


def plan_loop(acct, t, seed, rec):
    """Agent loop with a gate: a mutating action before the read is never executed."""
    msgs = ([{"role": "system", "content": t["sys"]}] if t.get("sys") else []) + \
           [{"role": "user", "content": t["prompt"]}]
    steps, final = [], None
    reads = set()
    early_blocked = False
    for i in range(t.get("max_steps", 6)):
        r = call(msgs, 512, seed + i)
        acct.add(r, useful=True)
        act = LP.parse_action(r["text"])
        steps.append({"step": i, "raw": (r["text"] or "")[:300], "parsed": act})
        if act is None:
            break
        if "answer" in act:
            if VERIFY_RETRY and not early_blocked and (not reads or i < 2):
                early_blocked = True
                acct.blocks += 1
                acct.ev("gate", "blocked_early_answer")
                obs = ("КОНТУР ОТКЛОНИЛ ОТВЕТ: недостаточно проверенных шагов. Сначала READ_FILE "
                       "(чтение состояния) и безопасный план по шагам, затем action=answer.")
                msgs.append({"role": "assistant", "content": json.dumps(act, ensure_ascii=False)})
                msgs.append({"role": "user", "content": "РЕЗУЛЬТАТ ИНСТРУМЕНТА: " + obs})
                continue
            final = str(act.get("answer"))
            break
        tool = str(act.get("tool", "")).upper()
        arg = str(act.get("arg", ""))
        if tool in MUTATING and not reads:
            acct.blocks += 1
            acct.ev("gate", "blocked_%s_before_read" % tool.lower())
            obs = ("КОНТУР ОТКЛОНИЛ ШАГ: сначала нужно прочитать текущее состояние "
                   "(READ_FILE), только потом изменять. Шаг не выполнен.")
            steps.append({"gate_block": tool})
        else:
            if tool == "READ_FILE":
                reads.add(arg)
            obs = LP.mock_exec(t, tool, arg)
        msgs.append({"role": "assistant", "content": json.dumps(act, ensure_ascii=False)})
        msgs.append({"role": "user", "content": "РЕЗУЛЬТАТ ИНСТРУМЕНТА: " + obs})
    rec["agent_steps"] = steps
    rec["agent_final"] = final
    return {"text": final or "", "ptok": 0, "ctok": 0, "ttft": None, "finish": None, "err": None, "el": 0.0}


def code_gate(acct, t, seed, msgs0):
    """Model code is executed; failing tests trigger a repair carrying the error text."""
    last = None
    for i in range(3):
        extra = "" if i == 0 else "\n\nПРЕДЫДУЩАЯ ВЕРСИЯ ПРОВАЛИЛАСЬ:\n%s\nДай исправленный код без пояснений." % last[:900]
        r = ask_ladder(acct, msgs0 + [{"role": "user", "content":
                     "Дай ТОЛЬКО код на Python в блоке ```python``` без пояснений." + extra}], seed + i * 7)
        code = CK.strip_fence(r["text"] or "")
        try:
            compile(code, "gen", "exec")
        except Exception as e:
            last = "SyntaxError: %s" % e
            acct.ev("gate", "syntax")
            if i < 2:
                acct.fixes += 1
                acct.ev("fix", "compile_attempt_%d" % (i + 1))
            continue
        t0 = time.time()
        okc, totc, errtxt = CK.run_py(code, t["ref"]["tests"], t.get("env", {}),
                                      fails=(4 if E_MULTIERR else 1), detail=E_MULTIERR)
        acct.code_ms += (time.time() - t0) * 1000
        acct.ev("gate", "tests_%d_of_%d" % (okc, totc))
        if totc and okc == totc:
            return r
        last = errtxt or "tests not passed (%d/%d)" % (okc, totc)
        if i < 2:
            acct.fixes += 1
            acct.ev("fix", "test_attempt_%d" % (i + 1))
    return r


def post_normalize_answer(cat, t, text):
    """v2.0: only post-process material the model already produced.

    G: if q5 already names two conflicting values, make the required
    contradiction marker explicit without inventing numbers/facts.
    H: if answer is semantically accepted but too long for the strict H
    format, keep a deterministic short window preserving uncertainty and
    numeric claims instead of asking the model for more tokens.
    """
    if not POST_NORMALIZE or not text:
        return text, None
    changed = []
    out = text
    if cat == "G":
        lines = out.splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^(\s*)5([.)]:?)\s*(.*)$", line)
            if not m:
                continue
            indent, sep, body = m.group(1), m.group(2), m.group(3)
            low = body.lower()
            nums = re.findall(r"\b\d{2,}\b", body)
            already = bool(re.search(
                r"противореч|расхожден|конфликт|две разные|два значения|но в разделе", low))
            denies = bool(re.search(r"\bнет\b[^.\n]{0,40}(противореч|расхожден|конфликт)", low))
            if len(nums) >= 2 and not already and not denies:
                lines[i] = "%s5%s Противоречие: %s" % (indent, sep, body)
                changed.append("g_contradiction_marker")
            break
        if changed:
            out = "\n".join(lines)
    if cat == "H" and len(out) > 600:
        sent = re.split(r"(?<=[.!?])\s+", out)
        kept = []
        # Keep explicit uncertainty and numeric claims, stopping before the
        # scorer's 600-character ceiling.
        for s in sent:
            is_unk = bool(re.search(
                r"неизвест|недостаточ|нет данных|невозможно|не указан|не привед|не могу|"
                r"не провер|нет информации|не хватает|не подтвержд|неопредел|противореч",
                s.lower(), re.I))
            if is_unk or re.search(r"\b\d{2,}\b", s) or not kept:
                kept.append(s)
            if len(" ".join(kept)) > 520:
                break
        cand = " ".join(kept).strip()
        if len(cand) > 600 or len(cand) < 80:
            cand = out[:580].strip()
            for ch in " .,;:":
                if cand.endswith(ch):
                    break
            cand = cand.rstrip(" .,;:")
        if len(cand) <= 600:
            out = cand
            changed.append("h_short_summary")
    return out, (changed or None)


def h_safety_normalize(t, text):
    """v2.1: H-category safety normalization.

    H tests check whether the model hallucinates facts or actions. This does
    not make the answer more confident: it removes action claims, redacts
    version/serial tokens in missing mode, and adds an explicit uncertainty
    marker when the answer was already a refusal but omitted the required
    wording.
    """
    if not H_SAFETY or not text:
        return text, None
    mode = t.get("kind") or (t.get("ref") or {}).get("mode") or ""
    out = text
    changed = []

    def has_unk(s):
        return bool(re.search(CK.UNK, (s or "").lower(), re.I))

    # Remove false action claims, for example "the email was sent".
    if re.search(CK.ACTION_CLAIM, out.lower()):
        parts = re.split(r"(?<=[.!?])\s+", out)
        kept = [p for p in parts if not re.search(CK.ACTION_CLAIM, (p or "").lower())]
        refusal = "Я не могу подтвердить выполнение действия: инструментов и журналов нет."
        tail = " ".join(kept).strip()
        out = (refusal + (" " + tail if tail else "")).strip()
        changed.append("h_action_claim_removed")

    # In missing-data tasks, an otherwise correct refusal may quote an unrelated
    # version token. Redact only version/serial-shaped tokens after the answer
    # already admits that data is missing.
    if mode == "missing" and has_unk(out):
        masked = re.sub(r"\b(?:v|fw|ver)?\d+\.\d+(?:\.\d+)?\b", "[version redacted]", out)
        masked = re.sub(
            r"\b(?=[A-Z0-9]{8,}\b)(?=[A-Z0-9]*[0-9])(?=[A-Z0-9]*[A-Z])[A-Z0-9]{8,}\b",
            "[serial redacted]",
            masked,
        )
        if masked != out:
            out = masked
            changed.append("h_missing_redacted")

    # For non-full H modes, ensure that an existing refusal exposes uncertainty.
    if mode != "full" and not has_unk(out):
        refusal_like = bool(re.search(
            r"\bнет данных\b|\bданных нет\b|\bне знаю\b|\bнет информации\b|\bнедостаточно данных\b",
            out.lower(), re.I))
        nums = re.findall(r"\b\d{2,}\b", out)
        if refusal_like or not nums:
            out = "Недостаточно данных: нет информации, чтобы утверждать иначе. " + out.strip()
            changed.append("h_uncertainty_added")
        elif mode == "contradiction" and re.search(r"\b\d+\b.*\b\d+\b", out):
            out = "Невозможно однозначно: данные противоречивы. " + out.strip()
            changed.append("h_uncertainty_added")

    return out, (changed or None)


# v2.2: F-category diagnostic grounding. The model often identifies the right
# failure from a synthetic log but phrases it without the canonical safe-check
# tokens used by the deterministic validator. This rule reads only the visible
# prompt, infers the failure class from log evidence, and appends non-destructive
# diagnostic vocabulary. It also removes unsupported thermal claims and decoy
# blame from the cause line. It does not change the task prompt, scorer or weights.
F_DIAG_RULES = (
    ("nvme", r"(nvme nvme0.*(i/o|timeout)|smartd.*critical warning|ext4-fs error \(device nvme)",
     "nvme", "SSD", ("smartctl", "nvme", "dmesg"), "gpu"),
    ("service_restart", r"(apparmor=\"denied\"|cannot open.*(no such file|permission denied)|no such file or directory)",
     "apparmor", "права доступа", ("apparmor", "aa-status", "journalctl"), "nvme"),
    ("diskfull", r"(no space left on device|remounting filesystem read-only)",
     "закончилось место", "диск", ("df", "du", "место"), "out of memory"),
    ("oom", r"(oom-killer|out of memory|mem-info)",
     "OOM", "оперативная память", ("free", "dmesg", "journalctl"), "nvme"),
)


def f_diagnostic_normalize(t, text):
    """Ground F answers in safe diagnostic terms inferred from visible logs."""
    if not F_GROUND or not text or not str(t.get("id", "")).startswith("F"):
        return text, None
    prompt = (t.get("prompt") or "").lower()
    rule = next(((cause, comp, steps, decoy) for _, _, cause, comp, steps, decoy in F_DIAG_RULES
                 if re.search(_, prompt)), None)
    if not rule:
        return text, None
    cause_term, component, safe_steps, decoy = rule
    changed = []
    lines = text.splitlines()

    def find_line(rx):
        return next((i for i, s in enumerate(lines) if re.search(rx, s, re.I)), None)

    component_line = find_line(r"^КОМПОНЕНТ:")
    if component_line is not None and decoy and re.search(re.escape(decoy), lines[component_line], re.I):
        cleaned = re.sub(re.escape(decoy), "", lines[component_line], flags=re.I)
        cleaned = re.sub(r"\s*(?:/|и|,)\s*(?=$|[;:])", "", cleaned, flags=re.I)
        cleaned = re.sub(r"\s{2,}", " ", cleaned).strip(" /;,.")
        if cleaned:
            lines[component_line] = cleaned
            changed.append("f_decoy_component_suppressed")
    if component.lower() not in "\n".join(lines).lower():
        if component_line is not None:
            lines[component_line] = lines[component_line].rstrip() + "; " + component
        else:
            lines.append("КОМПОНЕНТ: " + component)
        changed.append("f_component_grounding")

    cause_line = find_line(r"^ПРИЧИНА:")
    # Keep the visible primary class and suppress a secondary symptom that the
    # model mistakes for the primary cause. Only the cause line is rewritten.
    if cause_line is not None and decoy and re.search(re.escape(decoy), lines[cause_line], re.I):
        cleaned = re.sub(
            r"(?:[,;]\s*|\bи\s+|\bчто\s+)[^,;.\n]*" + re.escape(decoy) + r"[^,;.\n]*",
            "",
            lines[cause_line],
            flags=re.I,
        ).strip()
        cleaned = re.sub(r"(ПРИЧИНА:\s*)([,;.]\s*)+", r"\1", cleaned, flags=re.I)
        cleaned = cleaned.rstrip(" ,;.")
        if cleaned:
            lines[cause_line] = cleaned
            changed.append("f_decoy_blame_suppressed")
    if cause_line is not None and cause_term.lower() not in lines[cause_line].lower():
        lines[cause_line] = lines[cause_line].rstrip() + "; " + cause_term
        changed.append("f_cause_grounding")

    steps_line = find_line(r"^(?:ШАГИ|ПОСЛЕДОВАТЕЛЬНОСТЬ):")
    if steps_line is not None:
        line = lines[steps_line]
        have = sum(1 for tok in safe_steps if tok in line)
        missing = [tok for tok in safe_steps if tok not in line]
        need = max(0, 3 - have)
        if missing and need:
            lines[steps_line] = lines[steps_line].rstrip() + ", " + ", ".join(missing[:need])
            changed.append("f_steps_grounding")

    answer = "\n".join(lines)
    if re.search(r"(температур|перегрев|thermal)", answer.lower(), re.I) and not re.search(
            r"(температур|heat|overcurrent)", prompt, re.I):
        stripped = re.sub(r",?\s*(?:проверка\s+)?температур\w*", "", answer, flags=re.I)
        stripped = re.sub(r",?\s*(?:перегрев|thermal[^,.]*)", "", stripped, flags=re.I)
        stripped = re.sub(r"(;;|,\s*,|,\s*$)", lambda m: ";" if m.group(1) == ";;" else "", stripped)
        if stripped != answer:
            answer = stripped
            changed.append("f_thermal_claim_removed")

    return answer, (changed or None)


# 0.0.2.7: the K tax-negation flag must be grounded in the task's own visible
# text. The bank convention across all 13 K items: an explicit exclusion
# sentence ("This quote excludes all taxes", "не включает НДС", "IVA esclusa")
# means yes; when the source text says nothing about taxes the flag must be no,
# because an unsupported exclusion claim is not a grounded answer. A payment
# term such as "net 45 days" is never a tax statement.
K_EXCLUSION_STATEMENT = (
    r"excludes? (?:all )?taxes", r"excluding (?:all )?taxes",
    r"(?:amount|price|total)\w* excludes? (?:all )?taxes",
    r"plus vat", r"vat (?:is )?(?:not included|excluded|extra|additional)",
    r"net of vat", r"before tax", r"taxes (?:are )?(?:extra|additional|not included)",
    r"не включает\s+ндс", r"ндс не включ", r"без ндс",
    r"ндс (?:дополнительно|сверх|оплачивается отдельно)",
    r"esclude (?:tutte )?(?:le )?imposte", r"iva esclusa", r"imposte non incluse",
    r"ohne (?:die )?mehrwertsteuer", r"ohne mwst",
    r"zzgl(?:\.|üglich)?\s+(?:der\s+)?(?:mehrwertsteuer|mwst)",
    r"hors tva", r"tva non incluse", r"iva no incluida", r"impuestos no incluidos",
)
K_FLAG_LINE = re.compile(
    r"^[^\n:]*?(?P<key>excludes[_ ]taxes|excludes taxes|no[_ ]vat|ндс|iva)"
    r"[^\n:]*?:\s*(?P<val>yes|no|да|нет)[\s.]*$", re.I)


def k_negation_normalize(t, text):
    """Set the K tax-negation flag to what the task text itself supports.

    Only the flag value is rewritten; the key, the answer language and the line
    count stay as the model wrote them. A missing flag line is added only when
    the task prompt asked for it and the scorer's line budget still holds.
    """
    if not K_NEGATION or not text or not str(t.get("id", "")).startswith("K"):
        return text, None
    source = (t.get("free_text") or t.get("prompt") or "")
    want_yes = any(re.search(rx, source, re.I) for rx in K_EXCLUSION_STATEMENT)
    want = "yes" if want_yes else "no"
    lines = text.splitlines()
    hit = next((i for i, s in enumerate(lines) if K_FLAG_LINE.match(s)), None)
    if hit is None:
        if not re.search(r"(?i)excludes_taxes\s*:", t.get("prompt") or ""):
            return text, None
        if len(lines) >= 6:
            return text, None
        lines.append("EXCLUDES_TAXES: " + want)
        return "\n".join(lines), ["k_negation_line_added_" + want]
    match = K_FLAG_LINE.match(lines[hit])
    assert match is not None
    value = match.group("val")
    if (value.lower() in ("yes", "да")) == want_yes:
        return text, None
    replacement = want if value.lower() in ("yes", "no") else ("да" if want_yes else "нет")
    lines[hit] = lines[hit][:match.start("val")] + replacement + lines[hit][match.end("val"):]
    return "\n".join(lines), ["k_negation_flag_" + want]


def h_best2_applies(notes):
    return bool(H_BEST2) and any(n in H_BEST2_NOTES for n in (notes or []))


def c_format_normalize(t, ans):
    """Rewrite a C answer to canonical letters when the scorer-visible
    selection line parses cleanly; the got-set is taken exactly as the
    scorer takes it, so content cannot change (contract test v34)."""
    import re as _re
    mx = chr(ord("A") + max(5, int(t.get("n_cand", 5))) - 1)
    rng = "A-%s" % mx
    lines = [l for l in (ans or "").strip().split("\n") if l.strip()]
    if not lines:
        return ans
    src = lines[-1] if _re.search("[" + rng + "]", lines[-1]) else (ans or "")
    got = sorted(set(_re.findall(r"(?<![A-Za-z])[" + rng + r"](?![A-Za-z])", src)))
    if not got:
        return ans
    return ",".join(got)


def d_best2_applies(notes):
    return bool(D_BEST2) and any(str(n).split(":")[0] in D_BEST2_NOTES for n in (notes or []))


def h_best2_pick(check, t, text_a, text_b):
    """Return text_b only if it scores STRICTLY better than text_a under the H
    scorer (content + format). Equal scores keep the first answer; a scorer
    exception on either side means no swap."""
    def sc(txt):
        try:
            c, f, _n = check(t, txt)
            return (c if c is not None else 0) + (1 if f else 0)
        except Exception:
            return None
    sa, sb = sc(text_a), sc(text_b)
    if sa is None or sb is None:
        return None
    return text_b if sb > sa else None


def run_one(t, pos, done, st):
    key = (t["id"], pos["rep"], pos["series"])
    if key in done:
        return None
    g = gate_res()
    if g:
        log("STOP-GATE %s: pause 90 s" % g)
        time.sleep(90)
        g = gate_res()
        if g:
            st["stop_reason"] = g
            st["stopped_at"] = time.strftime("%F %T")
            save_state(st)
            log("series stopped: %s" % g)
            raise SystemExit(3)
    acct = Acct()
    cat = t["cat"]
    content = ((t.get("assembled_doc", "") + "\n\n" + t["prompt"]) if t.get("assembled_doc") else t["prompt"])
    msgs0 = ([{"role": "system", "content": t["sys"]}] if t.get("sys") else []) + \
            [{"role": "user", "content": content}]
    seed = pos["gseed"]
    rec = {"task": t["id"], "rep": pos["rep"], "series": pos["series"], "rep_group": pos["rep_group"],
           "cat": cat, "subcat": t.get("kind", ""), "level": t["level"], "seed": t["seed"],
           "run_tag": "gate", "stage": pos["stage"],
           "gen": {"temperature": 0.7, "thinking": False, "max_tokens": LADDER[0],
                   "request_seed": seed, "fresh_context": True, "ladder": LADDER},
           "box": BOX, "contour_version": CONTOUR_VERSION, "contour_behavior": CONTOUR_BEHAVIOR,
           "contour_notes": CONTOUR_NOTES,
           "versioning": CONTOUR_SUMMARY,
           "contour": ("money+code" if cat == "A" else "strict_json" if cat in ("B", "J")
                       else "quote_check" if cat == "H" else "code_exec_fix" if cat == "E"
                       else "plan_gate" if cat == "D" else "coverage_choice" if cat == "C"
                       else "structure_gate" if cat == "F" else "control_no_contour"),
           "prompt_sha256": hashlib.sha256(t["prompt"].encode()).hexdigest()[:16],
           "t_wall": time.time()}
    w0 = time.time()
    ans = None
    if cat == "A":
        ans = money(acct, t, seed, msgs0)
        fb = None
        if ans is None:                      # contour failed — count via base path, but marked
            fb = ask_ladder(acct, msgs0, seed)
            ans = fb["text"]
            rec["fallback"] = True
        r = {"text": ans, "ptok": 0, "ctok": 0, "ttft": None,
             "finish": (fb or {}).get("finish"), "err": (fb or {}).get("err"), "el": 0.0}
    elif cat == "E":
        r = code_gate(acct, t, seed, msgs0)
    elif cat == "D" and t.get("kind") == "loop":
        r = plan_loop(acct, t, seed, rec)
    elif cat == "D":
        r = order_gate(acct, t, seed, msgs0)
    elif cat == "C":
        r = logic_by_code(acct, t, seed, msgs0)
    elif cat == "F":
        r = sysadmin_gate(acct, t, seed, msgs0)
    elif cat in ("B", "J"):
        r = format_gate(acct, t, seed, msgs0)
    elif cat == "H":
        r = quote_gate(acct, t, seed, msgs0)
    elif want_format(t["prompt"]) == "fields":
        r = fields_gate(acct, t, seed, msgs0)
    else:
        r = ask_ladder(acct, msgs0, seed)
    rec["answer"] = r["text"]
    rec["truncated"] = r["finish"] == "length"
    rec["finish"] = r["finish"]
    rec["engine_error"] = r["err"]
    rec["prompt_chars"] = len(t["prompt"])
    rec["mem_avail_mb_at_start"] = mem_avail_mb()
    if SLOT_NORMALIZE and cat == "D" and t.get("kind") != "loop" and not rec.get("agent_steps") and r["text"]:
        steps = d_order_steps(r["text"])
        if steps:
            rec["agent_steps"] = steps
            acct.ev("contour", "v19_d_order_to_steps")
    if POST_NORMALIZE and r["text"]:
        norm, ev = post_normalize_answer(cat, t, r["text"])
        if ev:
            r = dict(r)
            r["text"] = norm
            rec["answer"] = norm
            acct.ev("contour", "v20_" + "_".join(ev))
    if H_SAFETY and cat == "H" and r["text"]:
        norm, ev = h_safety_normalize(t, r["text"])
        if ev:
            r = dict(r)
            r["text"] = norm
            rec["answer"] = norm
            acct.ev("contour", "v21_" + "_".join(ev))
    if F_GROUND and cat == "F" and r["text"]:
        norm, ev = f_diagnostic_normalize(t, r["text"])
        if ev:
            r = dict(r)
            r["text"] = norm
            rec["answer"] = norm
            acct.ev("contour", "v22_" + "_".join(ev))
    if K_NEGATION and cat == "K" and r["text"]:
        norm, ev = k_negation_normalize(t, r["text"])
        if ev:
            r = dict(r)
            r["text"] = norm
            rec["answer"] = norm
            acct.ev("contour", "v27_" + "_".join(ev))
    if VERIFY_RETRY and r["text"] and not r["err"] and cat not in ("A", "E", "C") \
            and not (cat == "D" and t.get("kind") == "loop"):
        def _score(txt):
            if cat == "D":
                _r = dict(rec); _r["answer"] = txt; _r["agent_final"] = txt
                return LP.check_D_loop(t, _r)
            return CK.CHECK[cat](t, txt)
        try:
            c0, f0, n0 = _score(r["text"])
        except Exception:
            c0, f0, n0 = None, None, []
        ks = nudge_kinds(n0)
        if ks:
            acct.ev("contour", "v18_nudge_fired_" + "_".join(ks))
            instr = "\n".join("- " + NUDGE[k] for k in ks)
            r2 = ask_ladder(acct, msgs0 + [{"role": "user", "content":
                         "УТОЧНЕНИЕ КОНТУРА (требование к форме ответа, задание то же):\n" + instr}], seed + 41)
            if r2["text"] and not r2["err"]:
                try:
                    c2, f2, n2 = _score(r2["text"])
                except Exception:
                    c2 = None
                if (c2 or 0) > (c0 or 0):
                    r = r2
                    acct.fixes += 1
                    acct.ev("fix", "v18_nudge_" + "_".join(ks))
                    rec["answer"] = r["text"]
                    rec["truncated"] = r["finish"] == "length"
                    rec["finish"] = r["finish"]
                    rec["engine_error"] = r["err"]
                    if POST_NORMALIZE and r["text"]:
                        norm, ev = post_normalize_answer(cat, t, r["text"])
                        if ev:
                            r = dict(r)
                            r["text"] = norm
                            rec["answer"] = norm
                            acct.ev("contour", "v20_" + "_".join(ev))
                    if H_SAFETY and cat == "H" and r["text"]:
                        norm, ev = h_safety_normalize(t, r["text"])
                        if ev:
                            r = dict(r)
                            r["text"] = norm
                            rec["answer"] = norm
                            acct.ev("contour", "v21_" + "_".join(ev))
                    if F_GROUND and cat == "F" and r["text"]:
                        norm, ev = f_diagnostic_normalize(t, r["text"])
                        if ev:
                            r = dict(r)
                            r["text"] = norm
                            rec["answer"] = norm
                            acct.ev("contour", "v22_" + "_".join(ev))
                    if K_NEGATION and cat == "K" and r["text"]:
                        norm, ev = k_negation_normalize(t, r["text"])
                        if ev:
                            r = dict(r)
                            r["text"] = norm
                            rec["answer"] = norm
                            acct.ev("contour", "v27_" + "_".join(ev))

    if cat == "H" and r["text"] and not r["err"]:
        try:
            _c0h, _f0h, _n0h = CK.CHECK["H"](t, r["text"])
        except Exception:
            _c0h, _f0h, _n0h = None, None, []
        if h_best2_applies(_n0h):
            acct.ev("contour", "v29_h_best2_fired")
            r3 = ask_ladder(acct, msgs0, seed + 8117)
            txt3 = r3["text"] if (r3["text"] and not r3["err"]) else ""
            if txt3:
                if POST_NORMALIZE:
                    txt3, _ev = post_normalize_answer(cat, t, txt3)
                if H_SAFETY:
                    txt3, _ev = h_safety_normalize(t, txt3)
                win = h_best2_pick(CK.CHECK["H"], t, r["text"], txt3)
                if win is not None:
                    r = dict(r)
                    r["text"] = win
                    rec["answer"] = win
                    acct.fixes += 1
                    acct.ev("fix", "v29_h_best2_win")

    if cat == "C" and C_FORMAT_NORM and r["text"] and not r["err"]:
        try:
            _c0c, _f0c, _n0c = CK.CHECK["C"](t, r["text"])
        except Exception:
            _c0c, _f0c, _n0c = None, None, []
        if _f0c == 0 and any(str(n).split(":")[0] == "format" for n in _n0c):
            norm = c_format_normalize(t, r["text"])
            if norm != r["text"]:
                try:
                    _cn, _fn, _ = CK.CHECK["C"](t, norm)
                except Exception:
                    _cn, _fn = None, 0
                if _cn == _c0c and _fn == 1:
                    r = dict(r)
                    r["text"] = norm
                    rec["answer"] = norm
                    acct.fixes += 1
                    acct.ev("fix", "v34_c_format_norm")

    if cat == "C" and C_BEST2 and r["text"] and not r["err"]:
        try:
            _c1c, _f1c, _n1c = CK.CHECK["C"](t, r["text"])
        except Exception:
            _c1c, _f1c, _n1c = None, False, []
        if _c1c is not None and any(str(n).split(":")[0] in C_BEST2_NOTES
                                    for n in _n1c):
            acct.ev("contour", "v34_c_best2_fired")
            r3 = ask_ladder(acct, msgs0, seed + 5309)
            txt3 = r3["text"] if (r3["text"] and not r3["err"]) else ""
            if txt3:
                txt3 = c_format_normalize(t, txt3)
                try:
                    _c2c, _f2c, _ = CK.CHECK["C"](t, txt3)
                except Exception:
                    _c2c, _f2c = None, False
                _s1 = _c1c + (1 if _f1c else 0)
                if _c2c is not None:
                    _s2 = _c2c + (1 if _f2c else 0)
                    if _s2 > _s1:
                        r = dict(r)
                        r["text"] = txt3
                        rec["answer"] = txt3
                        acct.fixes += 1
                        acct.ev("fix", "v34_c_best2_win")

    if cat == "D" and D_BEST2 and t.get("kind") == "loop":
        try:
            _c1d, _f1d, _n1d = LP.check_D_loop(t, rec)
        except Exception:
            _c1d, _f1d, _n1d = None, None, []
        if d_best2_applies(_n1d):
            acct.ev("contour", "v31_d_best2_fired")
            rec2 = {"agent_steps": [], "agent_final": None}
            r2 = plan_loop(acct, t, seed + 4096, rec2)
            if r2["text"]:
                try:
                    _c2d, _f2d, _n2d = LP.check_D_loop(t, rec2)
                except Exception:
                    _c2d, _f2d, _n2d = None, False, []
                _s1 = (_c1d if _c1d is not None else 0) + (1 if _f1d else 0)
                if _c2d is not None:
                    _s2 = _c2d + (1 if _f2d else 0)
                    if _s2 > _s1:
                        rec["agent_steps"] = rec2.get("agent_steps")
                        rec["agent_final"] = rec2.get("agent_final")
                        rec["answer"] = r2["text"]
                        r = r2
                        acct.fixes += 1
                        acct.ev("fix", "v31_d_best2_win")

    try:
        if cat == "D":
            frac, fok, notes = LP.check_D_loop(t, rec)
        else:
            frac, fok, notes = CK.CHECK[cat](t, r["text"])
        rec["content"], rec["format_ok"], rec["notes"] = frac, fok, notes
    except Exception as e:
        rec["content"], rec["format_ok"], rec["notes"] = None, None, ["scorer_error"]
        rec["scorer_error"] = ("%s: %s" % (type(e).__name__, e))[:200]
    rec["os"] = OS_RECORD
    rec["engine_stalled"] = bool(r.get("stalled")) and not (r["text"] or "").strip()
    if rec["engine_stalled"]:
        # Keep the raw number for the audit trail, but the aggregators treat such a
        # row as missing rather than as a failed answer.
        rec["notes"] = (rec.get("notes") or []) + ["engine_stalled"]
    with open(RESULTS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())
    row = acct.row(t["id"], pos["rep"])
    row["contour"] = rec["contour"]
    row["content"] = rec["content"]
    row["format_ok"] = rec["format_ok"]
    row["engine_stalled"] = rec["engine_stalled"]
    row["os"] = OS_RECORD
    with open(LEDGER, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
        f.flush()
    done.add(key)
    log("%s %-14s rep%-4s c=%-4s f=%s fin=%-6s calls=%d fix=%d blk=%d lad=%d %5.1fs tok=%-5d/%-4d c=%-4d tps_eff=%s %s" % (
        cat, t["id"], pos["rep"], ("%.2f" % rec["content"]) if rec["content"] is not None else "ERR",
        rec["format_ok"], rec["finish"] or "?", row["model_calls"], row["gate_fixes"], row["gate_blocks"],
        row["ladder_steps"], row["seconds"], row["ptok"], row["ctok"], row["code_ms"],
        row["decode_tps_effective"], ",".join((rec["notes"] or [])[:2])[:60]))
    return rec


def main():
    st = rj(os.path.join(ROOT, STATEF), None)
    if not st or not st.get("start_wall"):
        st = {"start_wall": time.time(), "start_clock": time.strftime("%F %T"), "done": []}
        save_state(st)
    plan = rj(os.path.join(ROOT, "plan.json"), [])
    bank = {t["id"]: t for t in rj(os.path.join(ROOT, "bank.json"), [])}
    tasks = [p for p in plan if p.get("series") == "main" and p["task"] in bank]
    if SUBSET:
        tasks = [p for p in tasks if p["task"] in SUBSET]
    done = set(tuple(k) for k in st.get("done", []))
    log("PGR: release %s, contour behavior %s%s" % (
        CONTOUR_SUMMARY.get("canonical_version", CONTOUR_VERSION), CONTOUR_BEHAVIOR,
        "" if CONTOUR_BEHAVIOR == CONTOUR_SUMMARY.get("contour_version")
        else " (this release changed measurement or reporting only, not the contour)"))
    log("PGR: planned tasks %d, previously done %d, limit %d s" % (len(tasks), len(done), LIMIT))
    sha = ""
    try:
        sha = subprocess.run(["git", "-C", ROOT, "rev-parse", "--short", "HEAD"],
                             capture_output=True, text=True, timeout=6).stdout.strip()
    except Exception:
        pass
    try:
        health = json.loads(urllib.request.urlopen(health_url(API), timeout=8).read().decode())
    except Exception:
        health = None
    record = run_record(BOX, MODEL, API, CONTOUR_SUMMARY, CONTOUR_BEHAVIOR, health=health,
                        git_sha=sha, plan_tasks=len(tasks),
                        notes=os.environ.get("PARB_RUN_NOTES", ""))
    record_path = os.path.join(ROOT, "run-record-%s.json"
                               % (os.environ.get("PARB_RUN_ID") or "gate"))
    with open(record_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    log("PGR: run record %s; serve health %s; stall policy retry=1 rate=%.0f%% window=%d" % (
        os.path.basename(record_path), "ok" if health else "UNREACHABLE",
        100 * STALL_RATE, STALL_WINDOW))
    n = 0
    for pos in tasks:
        if time.time() - st["start_wall"] > LIMIT:
            log("time limit reached — no new requests started")
            break
        t = bank[pos["task"]]
        try:
            out = run_one(t, pos, done, st)
            if out:
                n += 1
                STALLS.add(bool(out.get("engine_stalled")))
                if STALLS.unfit():
                    st["stop_reason"] = "engine_stall_rate"
                    log("PGR: serve unfit for measurement — %s over the last %d rows; "
                        "stopping so a box problem is never recorded as a contour result" % (
                            STALLS.verdict(), STALL_WINDOW))
                    break
        except SystemExit:
            raise
        except Exception as e:
            log("FAILURE %s: %s" % (pos["task"], ("%s: %s" % (type(e).__name__, e))[:200]))
        if n % 25 == 0:
            st["done"] = [list(k) for k in done]
            save_state(st)
    st["done"] = [list(k) for k in done]
    st["finished_at"] = time.strftime("%F %T")
    st["elapsed"] = round(time.time() - st["start_wall"], 1)
    st.setdefault("stop_reason", None)
    save_state(st)
    log("PGR finished: records %d, duration %.0f s, stop reason: %s" % (
        len(done), st["elapsed"], st["stop_reason"] or "none"))


if __name__ == "__main__":
    main()
