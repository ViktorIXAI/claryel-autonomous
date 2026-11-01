#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Visual contour v2: frozen prompts + contour-only improvement, upgraded:
- deterministic repair rules incl. mergeGeometries (from contour1 failure study)
- motion reminder attempt when page renders but does not move (RENDERS_STATIC):
  frozen base prompt kept; contour appends its own clarification note (logged)
- pixel proxy metric: saturated blob count from screenshot (balls compliance)
All English logs (external material rule)."""
import json, os, subprocess, sys, time, datetime, colorsys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vis_fixers
from PIL import Image

HOME = os.path.expanduser("~")
B2003 = os.environ.get("VIS_B2003_SSH", "user@bench-host")   # sanitized for publication
KEY = os.path.expanduser(os.environ.get("VIS_SSH_KEY", "~/.ssh/id_ed25519"))
OUTROOT = HOME + "/.hermes/bench/visbench/" + os.environ.get("PARVIS_OUT", "contour2")
SEEDOFF = int(os.environ.get("PARVIS_SEEDOFF", "10"))
SERIES_NAMES = os.environ.get("PARVIS_SERIES", "pgp,balls,pel").split(",")
PY = sys.executable
MAX_ATT = 3
SERIES = {
    "balls": {"pf": "prompt.txt", "maxtok": 8192, "seed0": 96001 + SEEDOFF},
    "pel":   {"pf": "pelican_prompt.txt", "maxtok": 4096, "seed0": 97001 + SEEDOFF},
    "pgp":   {"pf": "pagoda_prompt_post.txt", "maxtok": 12288, "seed0": 98001 + SEEDOFF},
}
NOTE = ("\n\nCONTOUR NOTE (not part of the original prompt): the previous "
        "submission rendered fine but the scene did not move. The original "
        "requirements demand continuous visible motion (e.g. auto-rotating "
        "orbit camera updated inside requestAnimationFrame). Fix exactly that.\n")

def log(m):
    print(datetime.datetime.now().strftime("%H:%M:%S"), m, flush=True)

def blob_count(png):
    if not os.path.exists(png):
        return None
    try:
        im = Image.open(png).convert("RGB"); px = im.load(); W, H = im.size
    except Exception:
        return None
    seen = [[False] * W for _ in range(H)]; out = 0
    for y in range(H):
        for x in range(W):
            if seen[y][x]:
                continue
            r, g, b = px[x, y]
            hh, ss, vv = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if ss < 0.35 or vv < 0.35:
                seen[y][x] = True
                continue
            q = [(x, y)]; seen[y][x] = True; hue = hh * 360; n = 0
            while q:
                cx, cy = q.pop(); n += 1
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < W and 0 <= ny < H and not seen[ny][nx]:
                        seen[ny][nx] = True
                        r2, g2, b2 = px[nx, ny]
                        h2, s2, v2 = colorsys.rgb_to_hsv(r2 / 255, g2 / 255, b2 / 255)
                        dh = abs(h2 * 360 - hue); dh = min(dh, 360 - dh)
                        if s2 > 0.3 and v2 > 0.3 and dh < 45:
                            q.append((nx, ny))
            if 60 <= n <= 8000:
                out += 1
    return out

def gen(ser, i, att, note=False):
    name = "ct2_%s_%d_a%d" % (ser, i, att)
    s = SERIES[ser]
    pf = s["pf"]
    if note:
        nfile = "note_%s.txt" % ser
        base = open(os.path.join(HOME, ".hermes/cache/scratch/visbench", s["pf"]), encoding="utf-8").read()
        tmp = "/tmp/" + nfile
        open(tmp, "w", encoding="utf-8").write(base + NOTE)
        subprocess.run(["scp", "-q", "-i", KEY, tmp, "%s:visbench/%s" % (B2003, nfile)], capture_output=True, timeout=60)
        pf = nfile
    env = "PEL_PROMPT_FILE=$HOME/visbench/%s VIS_MAXTOK=%d VIS_SEED=%d VIS_ATTEMPT=%d" % (
        pf, s["maxtok"], s["seed0"] + i * 7 + att, att)
    subprocess.run(["ssh", "-o", "BatchMode=yes", "-i", KEY, B2003,
                    "cd ~/visbench && %s python3 pelicanbench.py %s" % (env, name)],
                   capture_output=True, text=True, timeout=600)
    loc = os.path.join(OUTROOT, name)
    os.makedirs(loc, exist_ok=True)
    subprocess.run(["rsync", "-az", "-e", "ssh -i " + KEY, "%s:visbench/%s/" % (B2003, name), loc + "/"],
                   capture_output=True, timeout=120)
    return name, loc

def run_validator(loc, ser, timeout=420, obs=None):
    env = os.environ.copy()
    if obs is not None:
        env["PAG_OBS"] = str(obs)
    try:
        subprocess.run([PY, HOME + "/.hermes/cache/scratch/visbench/pag_validate.py", loc],
                       capture_output=True, text=True, timeout=timeout, env=env)
    except subprocess.TimeoutExpired:
        pass
    p = os.path.join(loc, "pag_validation.json")
    if not os.path.exists(p):
        return {"verdict": "VALIDATOR_TIMEOUT"}
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

def load_done(res_path):
    done = set()
    if not os.path.exists(res_path):
        return done
    for line in open(res_path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            done.add((r.get("series"), int(r.get("seed_idx"))))
        except Exception:
            pass
    return done

def main():
    os.makedirs(OUTROOT, exist_ok=True)
    res_path = os.path.join(OUTROOT, "contour-results.jsonl")
    done = load_done(res_path)
    gate = subprocess.run(["ssh", "-o", "BatchMode=yes", "-i", KEY, B2003, "pgrep -fc gate_run.py"],
                          capture_output=True, text=True).stdout.strip()
    log("contour2 start; B2003 gate procs=%s; resume done=%d" % (gate, len(done)))
    resf = open(res_path, "a", encoding="utf-8")
    for ser in SERIES_NAMES:
        wins = 0
        for i in range(5):
            if (ser, i) in done:
                log("%s seed%d already complete, skipping" % (ser, i))
                continue
            rec = {"series": ser, "seed_idx": i, "attempts": []}
            nudged = False
            for att in range(1, MAX_ATT + 1):
                note = (ser in ("balls", "pgp")) and att == MAX_ATT and not nudged and any(
                    a.get("verdict") == "RENDERS_STATIC" for a in rec["attempts"])
                name, loc = gen(ser, i, att, note=note)
                fixes, bad = [], None
                html_p = os.path.join(loc, "index.html")
                if os.path.exists(html_p):
                    src = open(html_p, encoding="utf-8").read()
                    fixed, fixes, bad = vis_fixers.fix(src)
                    if fixes:
                        open(html_p, "w", encoding="utf-8").write(fixed)
                    if note:
                        fixes = fixes + ["static_nudge"]
                        nudged = True
                    if bad:
                        rec["attempts"].append({"att": att, "dir": name, "fixes": fixes, "static_damage": bad})
                        continue
                    v = run_validator(loc, ser, timeout=420, obs=5 if ser in ("balls", "pgp") else None)
                    ok = success(v, ser, loc)
                    ar = {"att": att, "dir": name, "fixes": fixes, "verdict": v.get("verdict"),
                          "raf": v.get("raf_frames_first_6s"),
                          "moving": (v.get("observed") or {}).get("max_moving_pct"),
                          "blobs": blob_count(os.path.join(loc, "screenshot.png"))}
                    rec["attempts"].append(ar)
                    if ok:
                        rec["final"] = "PASS"; rec["best"] = name; rec["attempts_used"] = att
                        wins += 1
                        log("%s seed%d PASS att=%d blobs=%s" % (ser, i, att, ar["blobs"]))
                        break
                else:
                    rec["attempts"].append({"att": att, "dir": name, "fixes": [], "verdict": "NO_HTML"})
                time.sleep(1)
            if "final" not in rec:
                rec["final"] = "FAIL"; rec["attempts_used"] = MAX_ATT
            log("%s seed%d %s attempts=%d" % (ser, i, rec["final"], rec["attempts_used"]))
            resf.write(json.dumps(rec, ensure_ascii=False) + "\n"); resf.flush()
        log("SERIES %s: %d/5 PASS" % (ser, wins))
    log("CONTOUR2_DONE")

main()
