#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for derivability-audit-v2 (scripts/bank_derivability_audit_v2.py).

Pins, in order:
 1. module-path pinning: v2 loads the harness matcher from THIS repo's harness dir;
 2. identity: the census header stamps scanner version, its own module sha16, the bank
    sha16 and the scorer contract id — a census line without them must fail this test;
 3. H mirror: the scanner's nameability verdict agrees with the frozen contract's own
    `_token_cover` on synthetic atoms (direct / absent / script-bridge / short-literal);
 4. ABK behaviour equivalence: on EVERY published bank file, v2 with cats=ABK reproduces
    audit-v1's hit set exactly (the frozen chain 39->38->37 stays reproducible);
 5. the published H-ex6-01 history: v6.4/v6.5 banks report the h_absent candidate on
    ask[0] BEFORE the v6.5 prompt fix names the artifact... (v6.5 names it, so v6.5+ must
    be clean on that atom) — the scanner sees the published defect class mechanically.
"""
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
V2 = os.path.join(SCRIPTS, "bank_derivability_audit_v2.py")
V1 = os.path.join(SCRIPTS, "bank_derivability_audit.py")

CHECKS = 0


def ok(cond, what):
    global CHECKS
    CHECKS += 1
    if not cond:
        raise AssertionError("FAIL: %s" % what)


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if not (spec and spec.loader):
        raise ImportError(path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


os.environ["PARB_AUDIT_CATS"] = "ABKH"
v2 = load(V2, "v2_under_test")
ok(v2.CK.__file__ == os.path.join(ROOT, "harness", "parb_check_v6.py"),
   "v2 harness module path not pinned: %s" % v2.CK.__file__)
ok(v2.SCANNER_VERSION == "audit-v2", "scanner version constant")

# ---------- 3. synthetic H mirror against the frozen matcher ----------
def mk(tid, prompt, unknown=None, ask=None):
    return {"id": tid, "prompt": prompt,
            "ref": {"unknown": unknown, "ask": ask or []}}

t_dir = mk("H-t00", "нужно проверить возврат по заказу 778 в платёжной системе",
           unknown="возврат по заказу", ask=["проверку в платёжной системе"])
ok(v2.h_atom_hits(t_dir) == [], "direct atoms must be clean: %r" % v2.h_atom_hits(t_dir))
ok(v2.CK._token_cover(t_dir["prompt"], ["возврат по заказу"]), "matcher sanity (direct)")

t_abs = mk("H-t01", "кто-то удалил бэкап сервера, разберись",
           unknown="кто удалил бэкап", ask=["аудит-лог operations"])
hits = v2.h_atom_hits(t_abs)
ok(len(hits) == 1 and hits[0][1] == "ask[0]" and hits[0][2] == "h_absent",
   "unnameable ask atom must be h_absent: %r" % hits)
ok(not v2.CK._token_cover(t_abs["prompt"], ["аудит-лог operations"]),
   "matcher sanity (absent): prompt itself must fail coverage")

t_scr = mk("H-t02", "посмотри историю операций и скажи, что не так",
           unknown=None, ask=["аудит-лог operations"])
hits = v2.h_atom_hits(t_scr)
ok(len(hits) == 1 and hits[0][2] == "h_script",
   "script-bridge-only atom must be h_script: %r" % hits)

t_short = mk("H-t03", "сделай ревью", unknown=None, ask=["ОК"])
hits = v2.h_atom_hits(t_short)
ok(len(hits) == 1 and hits[0][2] == "h_absent" and hits[0][1] == "ask[0]",
   "short literal missing must be h_absent: %r" % hits)
t_short2 = mk("H-t04", "статус ОК проверь", unknown=None, ask=["ОК"])
ok(v2.h_atom_hits(t_short2) == [], "short literal present must be clean")

# noneed: empty ref atoms are not census fodder (check_H_v6 no_gold_components path)
ok(v2.h_atom_hits(mk("H-t05", "текст", unknown=None, ask=[])) == [], "empty ref clean")

# ---------- 2. CLI identity header ----------
with tempfile.TemporaryDirectory() as td:
    p = os.path.join(td, "bank.json")
    json.dump([t_abs, t_dir], open(p, "w", encoding="utf-8"), ensure_ascii=False)
    out = subprocess.run([sys.executable, V2, p], capture_output=True, text=True,
                         cwd=ROOT, env={**os.environ, "PARB_AUDIT_CATS": "ABKH"})
    ok(out.returncode == 0, "CLI exit %d %s" % (out.returncode, out.stderr))
    m = re.search(r"SCAN-ID scanner=(\S+) self-sha16=([0-9a-f]{16}) bank-sha16=([0-9a-f]{16}) "
                  r"contract=(\S+) contract-sha16=([0-9a-f]{16})", out.stdout)
    ok(m, "identity header missing:\n%s" % out.stdout)
    ok(m.group(1) == "audit-v2", "scanner id in header")
    self16 = hashlib.sha256(open(V2, "rb").read()).hexdigest()[:16]
    ok(m.group(2) == self16 == v2.self_sha16(), "self sha16 in header")
    ok(m.group(3) == hashlib.sha256(open(p, "rb").read()).hexdigest()[:16], "bank sha16 in header")
    ok(m.group(4) == "v6.2", "contract version in header")
    ok("h_absent" in out.stdout and out.stdout.count("summary") == 1, "hit + summary printed")

# ---------- 4. ABK equivalence over every published bank ----------
v1 = load(V1, "v1_frozen")
ok(set(v1.CATS) == {"A", "B", "K", "H"}, "v1 inherits the test env cats")
v1.CATS = {"A", "B", "K"}  # pin audit-v1 to its frozen chain categories
banks = sorted(f for f in os.listdir(os.path.join(ROOT, "benchmarks", "hard"))
               if re.fullmatch(r"bank-hard-v6(\.\d)?\.json", f))
ok(len(banks) >= 6, "published banks found: %r" % banks)
v1_hits_by_bank = {}
for f in banks:
    path = os.path.join(ROOT, "benchmarks", "hard", f)
    _, hits_a = v1.scan(path)
    bank = json.load(open(path, encoding="utf-8"))
    hits_b = v2.scan_abk(bank)  # CATS currently ABKH; H must be excluded from ABK walk
    v1_hits_by_bank[f] = sorted(hits_a)
    ok(sorted(hits_a) == sorted(hits_b),
       "ABK divergence on %s: v1=%d v2=%d" % (f, len(hits_a), len(hits_b)))

# ---------- 5. the published H history is mechanically visible ----------
hard = os.path.join(ROOT, "benchmarks", "hard")
def h_census(bankfile):
    bank = json.load(open(os.path.join(hard, bankfile), encoding="utf-8"))
    return [h for h in v2.scan_h(bank) if h[0] == "H-ex6-01" and h[1] == "ask[0]"]
pre = [h for bf in ("bank-hard-v6.json", "bank-hard-v6.2.json", "bank-hard-v6.3.json",
                    "bank-hard-v6.4.json") for h in h_census(bf)]
ok(len(pre) == 4 and all(h[2] == "h_absent" for h in pre),
   "audit-v2 must flag H-ex6-01 ask[0] on every bank BEFORE the v6.5 naming fix: %r" % pre)
post = [h for bf in ("bank-hard-v6.5.json", "bank-hard-v6.6.json") for h in h_census(bf)]
ok(post == [], "v6.5+ names the artifact, atom must be clean: %r" % post)

print("audit_v2_scanner_test: %d checks PASS" % CHECKS)
