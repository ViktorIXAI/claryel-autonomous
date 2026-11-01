#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visual contour series: frozen prompts, contour-only improvement.
Per seed: up to MAX_ATT attempts. Between attempts the contour may add
deterministic code repairs (vis_fixers). Success = browser verdict.
All English logs (external material rule)."""
import json, os, subprocess, sys, time, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_fixers

HOME = os.path.expanduser("~")
B2003 = os.environ.get("VIS_B2003_SSH", "user@bench-host")   # sanitized for publication
KEY = os.path.expanduser(os.environ.get("VIS_SSH_KEY", "~/.ssh/id_ed25519"))
OUTROOT = HOME + "/.hermes/bench/visbench/contour1"
PY = sys.executable
MAX_ATT = 3
SERIES = {
    "balls": {"pf": "prompt.txt", "maxtok": 8192, "seed0": 96001},
    "pel":   {"pf": "pelican_prompt.txt", "maxtok": 4096, "seed0": 97001},
    "pgp":   {"pf": "pagoda_prompt_post.txt", "maxtok": 12288, "seed0": 98001},
}

def log(m):
    print(datetime.datetime.now().strftime("%H:%M:%S"), m, flush=True)

def gen(ser, i, att):
    name = "ct%s_%d_a%d" % (ser, i, att)
    s = SERIES[ser]
    env = "PEL_PROMPT_FILE=$HOME/visbench/%s VIS_MAXTOK=%d VIS_SEED=%d VIS_ATTEMPT=%d" % (s["pf"], s["maxtok"], s["seed0"] + i * 7 + att, att)
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-i", KEY, B2003,
                        "cd ~/visbench && %s python3 pelicanbench.py %s" % (env, name)],
                       capture_output=True, text=True, timeout=600)
    loc = os.path.join(OUTROOT, name)
    os.makedirs(loc, exist_ok=True)
    subprocess.run(["rsync", "-az", "-e", "ssh -i " + KEY, "%s:visbench/%s/" % (B2003, name), loc + "/"],  # gitleaks:allow (KEY/B2003 come from env; no literal values)
                   capture_output=True, timeout=120)
    return name, loc

def run_validator(loc, ser):
    r = subprocess.run([PY, HOME + "/.hermes/cache/scratch/visbench/pag_validate.py", loc],
                       capture_output=True, text=True, timeout=180)
    p = os.path.join(loc, "pag_validation.json")
    if not os.path.exists(p):
        return {"verdict": "VALIDATOR_CRASH", "tail": (r.stderr or "")[-200:]}
    return json.load(open(p))

def success(v, ser, loc):
    if v.get("exceptions") or v.get("console_errors"):
        return False
    if ser == "pel":
        mt = os.path.join(loc, "metrics.json")
        m = json.load(open(mt)) if os.path.exists(mt) else {}
        inv = m.get("svg_inventory") or {}
        return bool(m.get("svg_found")) and inv.get("_xml_well_formed") is not False
    return v.get("verdict") == "RENDERS_AND_SPINS"

def main():
    os.makedirs(OUTROOT, exist_ok=True)
    gate = subprocess.run(["ssh", "-o", "BatchMode=yes", "-i", KEY, B2003, "pgrep -fc gate_run.py"],
                          capture_output=True, text=True).stdout.strip()
    log("contour start; B2003 gate procs=%s (parallel run, speed penalty noted)" % gate)
    resf = open(os.path.join(OUTROOT, "contour-results.jsonl"), "a", encoding="utf-8")
    for ser in SERIES:
        wins = 0
        for i in range(5):
            rec = {"series": ser, "seed_idx": i, "attempts": []}
            for att in range(1, MAX_ATT + 1):
                name, loc = gen(ser, i, att)
                html_p = os.path.join(loc, "index.html")
                fixes, bad = [], None
                if os.path.exists(html_p):
                    src = open(html_p, encoding="utf-8").read()
                    fixed, fixes, bad = vis_fixers.fix(src)
                    if fixes:
                        open(html_p, "w", encoding="utf-8").write(fixed)
                    if bad:
                        rec["attempts"].append({"att": att, "dir": name, "fixes": fixes, "static_damage": bad})
                        continue  # syntax imbalance: skip validation, regenerate
                    v = run_validator(loc, ser)
                    ok = success(v, ser, loc)
                    rec["attempts"].append({"att": att, "dir": name, "fixes": fixes,
                                            "verdict": v.get("verdict"),
                                            "raf": v.get("raf_frames_first_6s"),
                                            "moving": (v.get("observed") or {}).get("max_moving_pct")})
                    if ok:
                        rec["final"] = "PASS"
                        rec["best"] = name
                        rec["attempts_used"] = att
                        wins += 1
                        break
                else:
                    rec["attempts"].append({"att": att, "dir": name, "fixes": [], "verdict": "NO_HTML"})
                time.sleep(1)
            if "final" not in rec:
                rec["final"] = "FAIL"
                rec["attempts_used"] = MAX_ATT
            log("%s seed%d %s attempts=%d" % (ser, i, rec["final"], rec["attempts_used"]))
            resf.write(json.dumps(rec, ensure_ascii=False) + "\n"); resf.flush()
        log("SERIES %s: %d/5 PASS" % (ser, wins))
    log("CONTOUR_SERIES_DONE")

main()
