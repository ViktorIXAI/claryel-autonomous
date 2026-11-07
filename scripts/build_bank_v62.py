#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build bank-hard-v6.2.json from the published v6.1 bytes (9ec86dfca4a6f85f).

Exactly three corrections, everything else byte-identical:
  A-ex6-03  ref ONLY: gold re-derived from the prompt's OWN printed chain
            (the v6.1 gold was computed from a base value 5700.0 that the
            prompt never prints; 0/89 published rows ever passed).
  C-ex6-02  ref ONLY: gold = the executed truth table of the shipped
            snippets on CPython (all four options print [1, 2, 3];
            v6.1 gold want=["C"] is refuted by executing the snippets
            the task itself ships; 0/89 published rows ever passed).
  K-ex6-03  prompt ONLY: the field spec now states the FREE_SHIPPING value
            form (`yes/no`) so the gold token `yes` is contract-derivable
            (9/91 published rows lost 0.25 on unstated-form answers).
Gold for K and the prompts for A/C stay exactly as shipped. The v6.1 file
is never modified.

Deterministic: every new value is RE-DERIVED at build time from the shipped
task bytes (constants parsed from the A prompt, options executed on this
CPython for C), then written. A CI re-run of this script reproduces the
exact output bytes.
"""
import hashlib
import json
import re
import sys

SRC = "benchmarks/hard/bank-hard-v6.json"
DST = "benchmarks/hard/bank-hard-v6.2.json"
SRC_SHA16 = "9ec86dfca4a6f85f"  # published v6.1 identity guard

raw = open(SRC, "rb").read()
if hashlib.sha256(raw).hexdigest()[:16] != SRC_SHA16:
    sys.exit("FATAL: v6.1 source bytes moved (expected sha16 %s)" % SRC_SHA16)
bank = json.loads(raw)

tasks = {t["id"]: t for t in bank}

# ---------- A-ex6-03: re-derive from the printed chain ----------
a = tasks["A-ex6-03"]
gp = a["prompt"]
gross = float(re.search(r"gross=([0-9]+(?:\.[0-9]+)?)", gp).group(1))
soc_rate = float(re.search(r"Соцвзнос (\d+)%", gp).group(1)) / 100.0
soc_cap = float(re.search(r"не более (\d+)", gp).group(1))
tax_rate = float(re.search(r"Налог (\d+)%", gp).group(1)) / 100.0
ded = float(re.search(r"вычет (\d+)", gp).group(1))
social = min(soc_rate * gross, soc_cap)
tax = max(tax_rate * (gross - social - ded), 0.0)
net = gross - social - tax
a_new_ref = {"net": round(net, 2), "social": round(social, 2), "tax": round(tax, 2)}

# ---------- C-ex6-02: executed truth table of the shipped options ----------
c = tasks["C-ex6-02"]
opts = dict(re.findall(r"^([A-F]): (.*)$", c["prompt"], re.M))
target = [1, 2, 3]
truth = []
for letter in sorted(opts):
    # An option "prints" the target iff evaluating the shipped expression on
    # this CPython yields exactly [1, 2, 3] (the quiz semantics).
    ns = {}
    exec(compile("val=" + opts[letter], "<opt%s>" % letter, "exec"), ns)
    if ns["val"] == target:
        truth.append(letter)
c_new_letters = sorted(truth)
if c_new_letters != ["A", "B", "C", "D"]:
    sys.exit("FATAL: C-ex6-02 executed truth changed: %s" % c_new_letters)
c_new_ref = {"letters": c_new_letters, "n_cand": c["ref"]["n_cand"]}

# ---------- K-ex6-03: state the value form in the field spec ----------
k = tasks["K-ex6-03"]
spec = "Поля: ITEM, QTY, LEAD_WEEKS, FREE_SHIPPING"
if not k["prompt"].endswith(spec):
    sys.exit("FATAL: K-ex6-03 prompt no longer ends with the shipped field spec")
k_new_prompt = k["prompt"] + " (FREE_SHIPPING: yes/no)"

# ---------- apply ----------
changed = []
a["ref"] = a_new_ref
changed.append("A-ex6-03.ref")
c["ref"] = c_new_ref
changed.append("C-ex6-02.ref")
k["prompt"] = k_new_prompt
changed.append("K-ex6-03.prompt")

out = json.dumps(bank, ensure_ascii=False, indent=1).encode() + b"\n"
# the v6.1 file's exact trailing-newline convention:
if not raw.endswith(b"\n"):
    out = out[:-1]
open(DST, "wb").write(out)

print("changed fields:", ", ".join(changed))
print("A-ex6-03 new ref:", a_new_ref)
print("C-ex6-02 new ref:", c_new_ref)
print("K-ex6-03 new prompt tail:", k_new_prompt)
print("wrote %s  sha16=%s  bytes=%d" % (DST, hashlib.sha256(out).hexdigest()[:16], len(out)))
