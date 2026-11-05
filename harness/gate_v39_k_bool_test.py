#!/usr/bin/env python3
import os, sys, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PARB_ROOT", os.getcwd())

def load(version, inject=None):
    os.environ["PARB_GATE_VERSION"] = version
    if inject is None:
        os.environ.pop("STRATA_CHECKER_INJECT", None)
    else:
        os.environ["STRATA_CHECKER_INJECT"] = inject
    import gate_run as G
    importlib.reload(G)
    return G

fails = []
def check(name, cond, detail=""):
    print("%-56s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(name)

K_TASK = {"id": "K-ex6-00", "cat": "K", "fields": ["ITEM", "AMOUNT", "DATE", "EXCLUDES_TAXES"], "ref": ["Aurora 13", "1299", "2026-05-11", "yes"], "prompt": "x"}
ANS_TRUE = "ITEM: Aurora 13\nAMOUNT: 1299 EUR\nDATE: 2026-05-11\nEXCLUDES_TAXES: true"
ANS_FALSE = "ITEM: Aurora 13\nAMOUNT: 1299 EUR\nDATE: 2026-05-11\nEXCLUDES_TAXES: false"
ANS_YES = "ITEM: Aurora 13\nAMOUNT: 1299 EUR\nDATE: 2026-05-11\nEXCLUDES_TAXES: yes"

G17 = load("0.0.2.17")
check("2.17 + inject OFF: K_BOOL_CANON off", getattr(G17, "K_BOOL_CANON", False) is False)
out17, ev17 = G17.k_bool_canonicalize(K_TASK, ANS_TRUE)
check("2.17 canonicalize is a no-op on true", out17 == ANS_TRUE and ev17 is None, "%r %s" % (out17, ev17))

G18 = load("0.0.2.18")
check("2.18 + inject OFF: K_BOOL_CANON on", G18.K_BOOL_CANON is True and G18.CHECKER_INJECT is False)
out, ev = G18.k_bool_canonicalize(K_TASK, ANS_TRUE)
check("2.18 true -> yes", "EXCLUDES_TAXES: yes" in out and ev == ["k_bool_yes"], "%r %s" % (out, ev))
outf, evf = G18.k_bool_canonicalize(K_TASK, ANS_FALSE)
check("2.18 false -> no", "EXCLUDES_TAXES: no" in outf and evf == ["k_bool_no"], "%r %s" % (outf, evf))
outy, evy = G18.k_bool_canonicalize(K_TASK, ANS_YES)
check("2.18 yes untouched", outy == ANS_YES and evy is None)
K01 = {"id": "K-ex6-01", "fields": ["SERVICE", "TOTAL", "DATE", "INCLUDES_TAX"], "ref": ["hosting", "90.00", "2026-06-02", "yes"]}
o1, e1 = G18.k_bool_canonicalize(K01, "SERVICE: hosting\nTOTAL: 90.00\nDATE: 2026-06-02\nINCLUDES_TAX: true")
check("2.18 INCLUDES_TAX true -> yes", o1.endswith("INCLUDES_TAX: yes") and e1 == ["k_bool_yes"], "%r %s" % (o1, e1))
K03 = {"id": "K-ex6-03", "fields": ["ITEM", "QTY", "LEAD_WEEKS", "FREE_SHIPPING"], "ref": ["x", "200", "14", "yes"]}
o3, e3 = G18.k_bool_canonicalize(K03, "ITEM: x\nQTY: 200\nLEAD_WEEKS: 14\nFREE_SHIPPING: true")
check("2.18 FREE_SHIPPING true -> yes", o3.endswith("FREE_SHIPPING: yes") and e3 == ["k_bool_yes"], "%r %s" % (o3, e3))
outA, evA = G18.k_bool_canonicalize({"id": "A-ex6-00", "fields": []}, ANS_TRUE)
check("2.18 non-K untouched", outA == ANS_TRUE and evA is None)
g_out, g_ev = G18.post_normalize_answer("G", {"cat": "G"}, "5) A 1200 B 1700")
check("2.18 does NOT inject G contradiction marker", g_ev is None)
check("2.18 K_NEGATION still tied to inject (OFF)", G18.K_NEGATION is False)
print("ALL PASS" if not fails else "FAILED: %s" % fails)
sys.exit(1 if fails else 0)
