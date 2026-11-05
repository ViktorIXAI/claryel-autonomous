#!/usr/bin/env python3
"""Contract v38 (contour 2.17): the keyword-free format repair must reach the official pipeline.

Diagnosed on the 0.0.2.16 full hard-v6 arm: the deterministic repairs added in 0.0.2.15
(B/D one-element-list unwrap, J decorated items -> bare ids) never ran in the official
score, because every call site was gated by POST_NORMALIZE = CHECKER_INJECT and ..., while
issue #15 switched CHECKER_INJECT off. Six strict cells in that arm were format-only
losses with content already 1.00.

Checks (no model calls):
  1. at 0.0.2.16 with injection OFF the pipeline gate admits no repair (the bug);
  2. at 0.0.2.17 with injection OFF the gate opens and the repair transforms the answer;
  3. scorer-KEYWORD injectors (G contradiction marker, K tax-negation) stay OFF at 0.0.2.17
     with injection off — unbundling the repair must not smuggle them back in;
  4. with STRATA_CHECKER_INJECT=1 both gates stay open (historical behaviour preserved).
"""
import os, sys, json, importlib

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


J_TASK = {"cat": "J", "ref": ["m4", "m1", "m3"]}
B_TASK = {"cat": "B", "mode": "plain"}
DECORATED = '[{"id": "m4", "qty": 1}, {"id": "m1", "qty": 1}, {"id": "m3", "qty": 1}]'
WRAPPED = '[{"net": 1827.0, "vat": 365.4}]'
G_TEXT = "5) В разделе A сумма 1200, в разделе B сумма 1700."
K_TEXT = "Итого к оплате 1200 рублей, налог неIncluded"

fails = []


def check(name, cond, detail=""):
    print("%-46s %s %s" % (name, "PASS" if cond else "FAIL", detail))
    if not cond:
        fails.append(name)


G16 = load("0.0.2.16")
check("2.16 + inject OFF: gate closed (the bug)", G16.post_normalize_allowed() is False,
      "POST_NORMALIZE=%s FORMAT_REPAIR=%s" % (G16.POST_NORMALIZE, G16.FORMAT_REPAIR))

G17 = load("0.0.2.17")
check("2.17 + inject OFF: gate open", G17.post_normalize_allowed() is True and G17.CHECKER_INJECT is False,
      "CHECKER_INJECT=%s" % G17.CHECKER_INJECT)
j_out, j_ev = G17.post_normalize_answer("J", J_TASK, DECORATED)
check("2.17 J decorated items -> bare ids", json.loads(j_out) == ["m4", "m1", "m3"]
      and j_ev == ["j_id_norm"], "%s %s" % (j_out, j_ev))
b_out, b_ev = G17.post_normalize_answer("B", B_TASK, WRAPPED)
check("2.17 one-element list -> object", json.loads(b_out) == {"net": 1827.0, "vat": 365.4}
      and b_ev == ["obj_unwrap"], "%s %s" % (b_out, b_ev))

g_out, g_ev = G17.post_normalize_answer("G", {"cat": "G"}, G_TEXT)
check("2.17 does NOT inject G contradiction marker", g_out == G_TEXT and g_ev is None,
      "%r %s" % (g_out[:60], g_ev))
k_out, k_ev = G17.post_normalize_answer("K", {"cat": "K", "ref": {"requires_tax_note": True}},
                                        K_TEXT.replace("неIncluded", "без налога"))
check("2.17 does NOT inject K negation flag", k_out == K_TEXT.replace("неIncluded", "без налога")
      and k_ev is None, "%r %s" % (k_out[:60], k_ev))

GINJ = load("0.0.2.17", inject="1")
check("2.17 + inject ON: both gates open", GINJ.post_normalize_allowed() is True
      and GINJ.POST_NORMALIZE is True, "POST_NORMALIZE=%s" % GINJ.POST_NORMALIZE)
j2, e2 = GINJ.post_normalize_answer("J", J_TASK, DECORATED)
check("2.17 + inject ON: repair still applied", json.loads(j2) == ["m4", "m1", "m3"]
      and e2 == ["j_id_norm"], "%s %s" % (j2, e2))

# the repair must be idempotent: a second pass over already-repaired text changes nothing
j3, e3 = G17.post_normalize_answer("J", J_TASK, j_out)
check("2.17 repair is idempotent", j3 == j_out and e3 is None, "%s %s" % (j3, e3))

os.environ.pop("STRATA_CHECKER_INJECT", None)
print("\n%s" % ("ALL PASS" if not fails else "FAILED: %s" % fails))
sys.exit(1 if fails else 0)
