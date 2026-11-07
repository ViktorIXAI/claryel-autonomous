#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""derivability-audit-v2 — gold-derivability census with versioned identity and H ask-atom coverage.

Why v2 exists (queued in bank-defect-v65/v66 changelogs):
  * audit-v1 (`bank_derivability_audit.py`, frozen) printed a "sha-less census": a census
    number could not be attributed to a scanner version, a bank file or a scorer contract.
  * audit-v1 covers only categories A/B/K. The published H defect class (H-ex6-01: the gold
    asks the answer to NAME an artifact the prompt never states, the frozen scorer zeroes a
    faithful paraphrase via `_token_cover`) was found by hand, because the scanner could not
    see H `ask`/`unknown` atoms at all.

v2 changes exactly two things:
  1. identity: every census run stamps scanner version + scanner module sha16 + bank sha16
     + the scorer contract version/id it mirrors. The census chain 39->38->37 stays pinned
     to audit-v1 and is never recomputed under v2 numbers.
  2. H coverage (opt-in: PARB_AUDIT_CATS must contain "H"): for every `ref.unknown` string
     and every `ref.ask` item, the census mirrors the frozen contract's OWN matching rule
     (`_token_cover`: token = `[а-яa-z0-9]{4,}` lowercased, hit = `_stem_tok(token)` present
     as a substring; short needles need the literal). An atom is nameable by an honest reader
     only if at least one of its token stems is present in the prompt in a copyable form.
     Classes reported (CANDIDATES, not verdicts):
       h_absent  — no token stem (nor its transliteration) appears in the prompt: the gold
                   demands naming atoms the prompt never shows (the H-ex6-01 class).
       h_script  — an atom is coverable ONLY through a script bridge (Latin token whose
                   transliterated stem is in the prompt, or Cyrillic token whose Latin
                   transliteration is): the model must cross scripts to score.
     With cats=ABK the ABK logic is byte-behaviour identical to audit-v1 (guarded by
     harness/audit_v2_scanner_test.py on every published bank).

Census, not gate: exit 0 always. Use it before spending GPU time on a task an honest
reader cannot pass; a candidate becomes a published defect only after answer-byte evidence.
"""
import hashlib
import importlib.util
import json
import os
import re
import sys

SCANNER_VERSION = "audit-v2"
CATS = set(os.environ.get("PARB_AUDIT_CATS", "ABK"))

HERE = os.path.dirname(os.path.abspath(__file__))
HARNESS = os.path.join(os.path.dirname(HERE), "harness")


def _load(name):
    """Load a harness module by absolute path (module-path pinning lesson: never pick up an
    older workspace copy off sys.path)."""
    path = os.path.join(HARNESS, name)
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    if not (spec and spec.loader):
        raise ImportError("cannot load harness module %s" % path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.__file__ == path, "module path not pinned: %s" % mod.__file__
    return mod


CK = _load("parb_check_v6.py")
GSC = _load("gate_scorer_contract.py")

MONTHS = {"01": "январ", "02": "феврал", "03": "март", "04": "апрел", "05": "ма",
          "06": "июн", "07": "июл", "08": "август", "09": "сентябр", "10": "октябр",
          "11": "ноябр", "12": "декабр"}

# single deterministic transliteration per direction; the census reports a bridge only
# when the BRIDGED stem is literally present, so ambiguity beyond this table can only
# under-report, never fabricate a hit.
_CYR2LAT = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e",
            "ж": "zh", "з": "z", "и": "i", "й": "i", "к": "k", "л": "l", "м": "m",
            "н": "n", "о": "o", "п": "p", "р": "r", "с": "s", "т": "t", "у": "u",
            "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "",
            "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya"}
_LAT2CYR = {"a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф", "g": "г",
            "h": "х", "i": "и", "j": "й", "k": "к", "l": "л", "m": "м", "n": "н",
            "o": "о", "p": "п", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в",
            "w": "в", "x": "кс", "y": "и", "z": "з"}


def translit(s):
    out = []
    for ch in s:
        if ch in _CYR2LAT:
            out.append(_CYR2LAT[ch])
        elif ch in _LAT2CYR:
            out.append(_LAT2CYR[ch])
        else:
            out.append(ch)
    return "".join(out)


def translit_forms(stem):
    """bridge forms tried for a stem: full transliteration, forms with the trailing
    characters dropped (suffix families differ: operat->опера), and the transliterated
    5-char stem prefix — every contract stem is >= 5 chars, so if the prompt shows that
    prefix root in the other script, the atom is reachable only by crossing scripts."""
    forms = {translit(stem)}
    for cut in (1, 2):
        if len(stem) - cut >= 5:
            forms.add(translit(stem[:-cut]))
    if len(stem) >= 5:
        forms.add(translit(stem[:5]))
    return {f for f in forms if len(f) >= 4}


# ---------- ABK logic: byte-for-byte the audit-v1 rules (frozen behaviour) ----------
def num_forms(x):
    s = repr(x) if not isinstance(x, str) else x
    out = {s}
    try:
        f = float(x)
        out.add(("%f" % f).rstrip("0").rstrip("."))
        if f == int(f):
            out.add(str(int(f)))
    except Exception:
        pass
    return {t for t in out if t and t not in ("0", "1") or t == "0"}


def scan_abk(bank):
    hits = []
    for t in bank:
        if t["id"][0] not in (CATS - {"H"}):
            continue
        pr = re.sub(r"\s+", " ", t["prompt"].lower())
        ref = t.get("ref")
        stack = [(ref, "")]
        while stack:
            v, path = stack.pop()
            if isinstance(v, dict):
                stack.extend((vv, path + "." + kk) for kk, vv in v.items())
            elif isinstance(v, list):
                stack.extend((vv, path + "[%d]" % i) for i, vv in enumerate(v))
            elif isinstance(v, bool):
                continue
            elif isinstance(v, (int, float)):
                if not any(f in pr for f in num_forms(v)):
                    hits.append((t["id"], path, "number", repr(v)))
            elif isinstance(v, str):
                m = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", v)
                if m:
                    y, mo, d = m.groups()
                    iso = v in pr
                    trio = (y in pr and str(int(d)) in pr and MONTHS[mo] in pr)
                    if not (iso or trio):
                        hits.append((t["id"], path, "date", v))
                elif re.fullmatch(r"\d+(\.\d+)?%", v):
                    spec = re.search(r"JSON[^\n]*", t["prompt"])
                    txt = spec.group(0) if spec else t["prompt"]
                    if not re.search('"[^"]*%[^"]*"|«[^»]*%[^»]*»', txt):
                        hits.append((t["id"], path, "type_form", v))
                else:
                    s = re.sub(r"[\u00ab\u00bb\"'`\s]+", " ", v).lower().strip()
                    pnorm = re.sub(r"[\u00ab\u00bb\"'`]+", " ", pr)
                    if len(s) >= 2 and s not in pnorm and not any(
                            f in pr for f in num_forms(s)):
                        hits.append((t["id"], path, "string", v[:40]))
    return hits


# ---------- H ask-atom logic: mirrors the frozen contract's own matcher ----------
def h_atom_hits(t):
    """Mirror check_H_v6's coverage rule: an answer component passes iff
    _token_cover(component_text, [atom]) — i.e. SOME token of the atom has its stem in the
    answer. An honest reader can only write stems the prompt shows; so an atom is
    unnameable when NO token stem appears in the prompt directly, and script-bridged when
    the only reachable form crosses scripts."""
    out = []
    r = t.get("ref") or {}
    pr = re.sub(r"\s+", " ", t["prompt"].lower())
    pnorm = re.sub(r"[\u00ab\u00bb\"'`]+", " ", pr)
    atoms = []
    if r.get("unknown"):
        atoms.append(("unknown", str(r["unknown"])))
    for i, a in enumerate(r.get("ask") or []):
        atoms.append(("ask[%d]" % i, str(a)))
    for path, atom in atoms:
        toks = [w for w in re.findall(r"[а-яa-z0-9]{4,}", atom.lower())]
        if not toks:
            if atom.lower().strip() not in pnorm:
                out.append((t["id"], path, "h_absent",
                            "%s :: literal atom not in prompt" % atom[:40]))
            continue
        direct = [w for w in toks if CK._stem_tok(w) in pnorm]
        if direct:
            continue
        bridged = []
        for w in toks:
            for form in translit_forms(CK._stem_tok(w)):
                if form in pnorm:
                    bridged.append(w)
                    break
        if bridged:
            out.append((t["id"], path, "h_script",
                        "%s :: only via script bridge (%s)" % (atom[:40], ",".join(bridged))))
        else:
            out.append((t["id"], path, "h_absent",
                        "%s :: no token-stem copyable (%s)" % (atom[:40], ",".join(toks))))
    return out


def scan_h(bank):
    hits = []
    for t in bank:
        if t["id"][0] not in (CATS & {"H"}):
            continue
        hits.extend(h_atom_hits(t))
    return hits


def self_sha16():
    return hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()[:16]


if __name__ == "__main__":
    for path in sys.argv[1:]:
        bank = json.load(open(path, encoding="utf-8"))
        b16 = hashlib.sha256(open(path, "rb").read()).hexdigest()[:16]
        cid = GSC.contract_identity(GSC.SCORER_CONTRACT)
        hits = scan_abk(bank) + scan_h(bank)
        print("== %s  tasks=%d  cats=%s" % (path, len(bank), "".join(sorted(CATS))))
        print("   SCAN-ID scanner=%s self-sha16=%s bank-sha16=%s contract=%s contract-sha16=%s"
              % (SCANNER_VERSION, self_sha16(), b16,
                 GSC.SCORER_CONTRACT, cid.get("contract_sha16")))
        for h in sorted(hits):
            print("   %-10s %-22s %-9s %s" % h)
        bycat = {}
        for tid, _, kind, _ in hits:
            bycat[tid] = bycat.get(tid, 0) + 1
        hsum = sum(1 for h in hits if h[2].startswith("h_"))
        print("   summary: %d candidate atoms over %d tasks (ABK=%d, H=%d)"
              % (len(hits), len(bycat), len(hits) - hsum, hsum))
        print("   tasks with candidates: %s" % ", ".join("%s(%d)" % kv for kv in sorted(bycat.items())))
    sys.exit(0)
