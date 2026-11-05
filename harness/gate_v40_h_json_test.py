#!/usr/bin/env python3
import os,sys,json,importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("PARB_ROOT", os.getcwd())
def load(v, inject=None):
    os.environ["PARB_GATE_VERSION"]=v
    if inject is None: os.environ.pop("STRATA_CHECKER_INJECT", None)
    else: os.environ["STRATA_CHECKER_INJECT"]=inject
    import gate_run as G; importlib.reload(G); return G
fails=[]
def check(n,c,d=""):
    print("%-56s %s %s"%(n,"PASS" if c else "FAIL",d));
    fails.append(n) if not c else None
H={"id":"H-ex6-01","cat":"H"}
ANS=json.dumps({"actions_done":["x"],"claims":["y"],"unknown":"кто удалил","requires":["аудит-лог"]},ensure_ascii=False)
G18=load("0.0.2.18")
check("2.18 H_JSON off", getattr(G18,"H_JSON_CONTRACT",False) is False)
o,e=G18.h_json_contract_normalize(H,ANS)
check("2.18 no-op", o==ANS and e is None)
G19=load("0.0.2.19")
check("2.19 on inject OFF", G19.H_JSON_CONTRACT and not G19.CHECKER_INJECT)
o,e=G19.h_json_contract_normalize(H,ANS)
obj=json.loads(o)
check("2.19 clears arrays", obj.get("actions_done")==[] and obj.get("claims")==[] and set(e)=={"h_clear_actions","h_clear_claims"}, "%s %s"%(obj,e))
check("2.19 keeps unknown/requires", obj.get("unknown")=="кто удалил" and obj.get("requires")==["аудит-лог"])
o2,e2=G19.h_json_contract_normalize(H,o)
check("idempotent", o2==o and e2 is None)
check("K_NEGATION still inject-gated", G19.K_NEGATION is False)
print("ALL PASS" if not fails else "FAILED "+str(fails)); sys.exit(1 if fails else 0)
