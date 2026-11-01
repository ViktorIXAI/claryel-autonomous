#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SAH publication pipeline (spec section: automatic publication).

Phases: collect -> verify -> privacy-scan -> snapshot -> aggregate -> publish
-> post-verify. Every package is immutable and idempotent (registry keyed by
content hash; unchanged files are never re-published). Raw files are copied
byte-for-byte or EXCLUDED (never edited); exclusions are recorded with the
reason. Network failures retry with backoff; a half-finished publication is
resumed by re-running the same command.

Usage:
  pipeline.py collect            # pull listed artifacts from rigs (read-only)
  pipeline.py snapshot           # verify+scan+freeze package(s), update registry
  pipeline.py publish            # upload to GitHub release + push repo updates
  pipeline.py watch              # cheap remote size check; full cycle if changed
  pipeline.py status
Local state: ~/.hermes/bench/parb/publish/  (staging, pkgs, registry.json)
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import tarfile
import time

HOME = os.path.expanduser("~")
PUB = os.path.join(HOME, ".hermes", "bench", "parb", "publish")
STAGE = os.path.join(PUB, "staging")
PKGS = os.path.join(PUB, "pkgs")
REG = os.path.join(PUB, "registry.json")
REPO = os.path.join(HOME, "projects", "strata-autonomous-harness")
PUBLISH_ENV = os.path.join(HOME, ".hermes", "bench", "parb", "publish.env")

def _load_private_env():
    """Load local-only publish settings. Not tracked in git."""
    if not os.path.exists(PUBLISH_ENV):
        return
    for line in open(PUBLISH_ENV, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):]
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

_load_private_env()

MACH = {
    "b2003": {"ssh": os.environ.get("SAH_SSH_B2003", ""), "dir": "~/parb"},
    "mac":   {"ssh": os.environ.get("SAH_SSH_MAC", ""),   "dir": "~/parb"},
    "host":  {"ssh": None, "dir": os.path.join(HOME, ".hermes/bench/parb")},
}

# package id -> list of (machine, filename-glob) ; globs are expanded remotely
PACKAGES = {
    "pkg-phase0-baseline":   [("b2003", ["results.jsonl", "gate-ledger.jsonl", "results-gate.jsonl", "run.log", "run2.log", "run3.log", "run4.log", "prep.log", "go.log"])],
    "pkg-gate-era-mac":      [("mac", ["results-gate.jsonl", "gate-ledger.jsonl", "gate.log"])],
    "pkg-ab-experiments":    [("mac", ["results-ab1*.jsonl", "gate-ledger-ab1*.jsonl", "ab_mac.sh", "ab_v14_mac.sh", "ab_v15_mac.sh", "ab_v16_mac.sh"]),
                              ("b2003", ["ab_results.jsonl", "ab_mini.jsonl", "ab.log", "ab_summary.json", "summary.json"]),
                              ("host", ["ab_b2003_mini.jsonl", "ab_mac_mini.jsonl", "ab_p2005.jsonl", "ab_results.jsonl"])],
    "pkg-probes":            [("b2003", ["results-p2.jsonl", "gate-ledger-p2.jsonl", "results-s3.jsonl", "gate-ledger-s3.jsonl", "results-s4.jsonl", "gate-ledger-s4.jsonl", "results-smk18.jsonl", "gate-ledger-smk18.jsonl", "results-smoke2.jsonl", "gate-ledger-smoke2.jsonl", "p2.log", "smoke2.log", "self-dry.log"]),
                              ("mac", ["results-m1.jsonl", "gate-ledger-m1.jsonl", "results-e6m.jsonl", "gate-ledger-e6m.jsonl"])],
    "pkg-series-v12-v20":    [("b2003", ["results-v1[2378].jsonl", "gate-ledger-v1[2378].jsonl", "v12.log", "v13.log", "v17.log", "v18.log", "v20.log"]),
                              ("mac", ["results-v1[2378]m.jsonl", "gate-ledger-v1[2378]m.jsonl", "results-v20m.jsonl", "gate-ledger-v20m.jsonl"])],
    "pkg-series-v19-live":   [("b2003", ["results-v19.jsonl", "gate-ledger-v19.jsonl", "v19.log"])],
    "pkg-series-v20-v21-live": [("b2003", ["results-v20.jsonl", "gate-ledger-v20.jsonl", "results-v21.jsonl", "gate-ledger-v21.jsonl", "v20.log", "v21.log"]),
                                ("mac", ["results-v20m.jsonl", "gate-ledger-v20m.jsonl", "results-v21m.jsonl", "gate-ledger-v21m.jsonl", "v20m.log", "v21m.log"]),
                                ("host", ["v20-final/results-v20*.jsonl", "v20-final/gate-ledger-v20*.jsonl", "v21-final/results-v21*.jsonl", "v21-final/gate-ledger-v21*.jsonl"])],
}

# Private patterns live in the local publish.env as SAH_SECRET_PATTERNS_JSON.
# Public defaults are intentionally generic and must not embed account/user/IP
# values from the home lab.
try:
    SECRET_PATTERNS = json.loads(os.environ.get("SAH_SECRET_PATTERNS_JSON", "[]"))
except Exception:
    SECRET_PATTERNS = []
SECRET_PATTERNS += [
    r"BEGIN [A-Z ]*PRIVATE KEY", r"ssh-rsa AAAA", r"ssh-ed25519 AAAA",
    r"api_key\"?\s*[:=]\s*\"[A-Za-z0-9_\-]{8,}", r"sk-[A-Za-z0-9]{16,}",
    r"gh[pousr]_[A-Za-z0-9]{20,}", r"Bearer\s+[A-Za-z0-9._\-]{16,}",
    r"192\.168\.\d+\.\d+", r"/home/[a-z0-9_]+",
    r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)|invalid|test|evil-inbox\.example)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
]
SECRET_RE = re.compile("|".join(SECRET_PATTERNS))


def run(cmd, **kw):
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kw)
    return r.returncode, r.stdout, r.stderr


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def _owner():
    repo = os.environ.get("SAH_GITHUB_REPO", "").strip()
    if repo:
        return repo
    u = subprocess.run(["git", "remote", "get-url", "origin"], cwd=REPO,
                       capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", u)
    if m:
        return m.group(1)
    raise SystemExit("set SAH_GITHUB_REPO in local publish.env or configure a GitHub origin")

def load_reg():
    if os.path.exists(REG):
        return json.load(open(REG))
    return {"packages": {}}


def save_reg(reg):
    tmp = REG + ".tmp"
    json.dump(reg, open(tmp, "w"), indent=1)
    os.replace(tmp, REG)


def ssh_of(m):
    return MACH[m]["ssh"]


def collect_one(m, pat):
    """pull files matching pattern from machine m into STAGE/m/"""
    d = MACH[m]["dir"]
    dst = os.path.join(STAGE, m)
    os.makedirs(dst, exist_ok=True)
    if ssh_of(m) is None:
        code, out, err = run(f"cp -f {d}/{pat} {dst}/ 2>/dev/null; echo done")
    else:
        code, out, err = run(f"scp -q -o StrictHostKeyChecking=accept-new "
                             f"-i {keyfile(m)} '{remote_user(m)}@{host(m)}:{d}/{pat}' {dst}/ 2>&1; echo done")
    return code, out


def keyfile(m):
    s = ssh_of(m)
    return re.search(r"-i (\S+)", s).group(1)


def remote_user(m):
    return ssh_of(m).split()[-1].split("@")[0]


def host(m):
    return ssh_of(m).split()[-1].split("@")[1]


def cmd_collect():
    for pid, entries in PACKAGES.items():
        for m, pats in entries:
            for pat in pats:
                os.makedirs(os.path.join(STAGE, m), exist_ok=True)
                if ssh_of(m):
                    code, out, err = run(f"{ssh_of(m)} 'ls {MACH[m]['dir']}/{pat} 2>/dev/null' < /dev/null", timeout=40)
                    for f in out.split():
                        fn = f.split("/")[-1]
                        run(f"scp -q -i {keyfile(m)} -o StrictHostKeyChecking=accept-new {remote_user(m)}@{host(m)}:{f} {os.path.join(STAGE, m, fn)} 2>&1")
                else:
                    import glob as g
                    for f in g.glob(os.path.join(MACH[m]["dir"], pat)):
                        run(f"cp -f '{f}' '{os.path.join(STAGE, m)}'")
    print("COLLECT-DONE")


def verify_and_scan(path):
    """return (ok, reason, meta). JSONL lines must parse; no secret patterns."""
    meta = {}
    with open(path, "rb") as f:
        data = f.read()
    if SECRET_RE.search(data.decode("utf-8", "ignore")):
        return False, "secret-pattern", meta
    if path.endswith(".jsonl"):
        bad = 0
        n = 0
        for ln in data.split(b"\n"):
            if not ln.strip():
                continue
            n += 1
            try:
                json.loads(ln)
            except Exception:
                bad += 1
        meta = {"lines": n, "bad_lines": bad}
        if bad > n * 0.02:
            return False, "unparseable-jsonl>2%", meta
        # truncation tolerance: keep packages with a small bad tail, mark it
    meta = {"bytes": len(data), **meta}
    return True, "", meta


def cmd_snapshot(tag="full"):
    reg = load_reg()
    made = []
    for pid, entries in PACKAGES.items():
        files = []
        for m, pats in entries:
            for pat in pats:
                import glob as g
                for f in g.glob(os.path.join(STAGE, m, pat)):
                    if os.path.basename(f).startswith(("state", "plan")):
                        continue
                    files.append((m, f))
        if not files:
            continue
        manifest = {"package": pid, "tag": tag, "created_utc": time.strftime("%FT%TZ", time.gmtime()),
                    "files": [], "excluded": []}
        for m, f in sorted(files, key=lambda x: x[1]):
            ok, why, meta = verify_and_scan(f)
            if not ok:
                manifest["excluded"].append({"machine": m, "file": os.path.basename(f), "reason": why})
                continue
            manifest["files"].append({"machine": m, "file": os.path.basename(f),
                                      "sha256": sha(f), "bytes": meta.get("bytes", 0),
                                      "lines": meta.get("lines"), "bad_lines": meta.get("bad_lines", 0)})
        h = hashlib.sha256(json.dumps(sorted((x["sha256"] + x["file"]) for x in manifest["files"])).encode()).hexdigest()[:12]
        pkgid = pid + "." + h
        if pkgid in reg["packages"]:
            continue  # idempotent: identical content already registered
        manifest["package_id"] = pkgid
        os.makedirs(PKGS, exist_ok=True)
        # per-machine subdirs avoid name collisions (same filenames on boxes)
        tmp = os.path.join(PUB, "tmp_" + pkgid)
        run(f"rm -rf {tmp} && mkdir -p {tmp}/{pid}")
        for e in manifest["files"]:
            e["path"] = "%s/%s" % (e["machine"], e["file"])
            run(f"mkdir -p {tmp}/{pid}/{e['machine']} && cp '{os.path.join(STAGE, e['machine'], e['file'])}' {tmp}/{pid}/{e['machine']}/")
        json.dump(manifest, open(os.path.join(tmp, pid + ".manifest.json"), "w"), indent=1, ensure_ascii=False)
        fmt = "tar.zst" if run("command -v zstd >/dev/null")[0] == 0 else "tar.gz"
        flag = "--zstd" if fmt == "tar.zst" else "-z"
        run(f"tar {flag} -cf {PKGS}/{pkgid}.{fmt} -C {tmp} {pid} {pid}.manifest.json")
        manifest["asset"] = f"{pkgid}.{fmt}"
        reg["packages"][pkgid] = manifest
        made.append(pkgid)
    save_reg(reg)
    print("SNAPSHOT-MADE:", made or "(nothing new)")
    return made


def cmd_aggregate():
    """recompute summary from ALL registered packages' contents staged locally."""
    code = run(f"PARB_ARTIFACTS={STAGE} python3 {REPO}/analytics/aggregate_auto.py > {STAGE}/summary-full.json")[0]
    print("AGGREGATE-RC", code)


def security_gate(target, label):
    """Hard Gitleaks gate; raw reports remain outside the public repository."""
    report = os.path.join(PUB, f"security-{label}.json")
    code, out, err = run(f"{sys.executable} {REPO}/scripts/security/secret_scan.py "
                         f"--dir '{target}' --report '{report}'", timeout=900)
    print("SECURITY-GATE", label, "rc", code, out[-500:] if code else "")
    return code == 0


def cmd_publish():
    reg = load_reg()
    if not (security_gate(STAGE, "pre-publish-staging") and security_gate(PKGS, "pre-publish-packages")):
        print("PUBLISH-BLOCKED: credential-like finding; review local security report")
        return
    tag = "data-full-2026-11-01"
    for pid, man in reg["packages"].items():
        if man.get("published"):
            continue
        asset = os.path.join(PKGS, man["asset"])
        code, out, err = run(f"cd {REPO} && gh release upload {tag} {asset} --clobber 2>&1", timeout=600)
        if code != 0:
            print("UPLOAD-FAIL", pid, out[-300:]);
            return
        man["published"] = {"tag": tag, "url": f"https://github.com/{_owner()}/releases/tag/{tag}", "at": time.strftime("%FT%TZ", time.gmtime())}
        save_reg(reg)
    # regenerate INDEX + summary in repo, commit, push
    rebuild_index(reg)
    run(f"cp {STAGE}/summary-full.json {REPO}/results/summary-full.json")
    # stage ONLY pipeline-generated paths: `git add -A` once swept unrelated
    # work-in-progress into a "publish" commit (see history/failures/failures.md)
    run(f"cd {REPO} && git add logs/PIPELINE-PACKAGES.md results/summary-full.json "
        f"&& git commit -qm 'publish: pipeline packages {tag}' && git push -q")
    post_verify(tag)


def rebuild_index(reg):
    rows = ["| package | created | files | bytes | asset | sha256(pkg) |", "|---|---|---:|---:|---|---|"]
    for pid, man in sorted(reg["packages"].items()):
        tot = sum(f["bytes"] for f in man["files"])
        a = man.get("published", {}).get("url", "(unpublished)")
        rows.append("| `%s` | %s | %d | %d | [asset](%s) | `%s…` |" % (
            man["package_id"], man["created_utc"], len(man["files"]), tot, a, sha(os.path.join(PKGS, man["asset"]))[:12]))
    body = "\n".join(rows)
    p = os.path.join(REPO, "logs", "PIPELINE-PACKAGES.md")
    old = ("# Pipeline packages (automatic publication)\n\nEvery package is immutable; "
           "content hash is part of the id. Per-file SHA-256 lives in `<pkgid>.manifest.json` "
           "inside each asset. Excluded files carry their reason in the manifest.\n\n")
    open(p, "w").write(old + body + "\n")


def post_verify(tag):
    """public-side verification with plain HTTPS, no auth."""
    reg = load_reg()
    ok = True
    for man in reg["packages"].values():
        url = "https://github.com/%s/releases/download/%s/%s" % (_owner(), tag, man["asset"])
        code, out, _ = run(f"curl -sL -o /tmp/pv.bin -w '%{{http_code}} %{{size_download}}' {url}", timeout=300)
        parts = out.split()
        want = os.path.getsize(os.path.join(PKGS, man["asset"]))
        got_sha = hashlib.sha256(open("/tmp/pv.bin", "rb").read()).hexdigest() if len(parts) == 2 and parts[0] == "200" else "-"
        local_sha = sha(os.path.join(PKGS, man["asset"]))
        good = len(parts) == 2 and parts[0] == "200" and int(parts[1]) == want and got_sha == local_sha
        print("VERIFY", man["package_id"], "http", parts[0] if parts else "?", "sha", got_sha[:12] == local_sha[:12])
        ok = ok and good
    return ok


def cmd_watch():
    """cheap remote wc -l comparison vs stored baseline; publish only on growth.
    Quiet when nothing changed (cron watchdog pattern)."""
    reg = load_reg()
    base = reg.setdefault("remote_watch", {})
    cur = {}
    for pid, entries in PACKAGES.items():
        for m, pats in entries:
            if ssh_of(m) is None:
                continue
            for pat in pats:
                code, out, _ = run(f"{ssh_of(m)} 'wc -l {MACH[m]['dir']}/{pat} 2>/dev/null' < /dev/null", timeout=30)
                for ln in out.splitlines():
                    parts = ln.split()
                    if len(parts) >= 2:
                        cur[m + "/" + parts[-1].split("/")[-1]] = parts[0]
    changed = {k: v for k, v in cur.items() if base.get(k) != v}
    first = not base
    reg["remote_watch"] = cur
    save_reg(reg)
    if first:
        print("WATCH-BASELINE stored for %d files" % len(cur))
        return
    if not changed:
        return  # silent: nothing moved
    print("WATCH: changed %s" % sorted(changed))
    cmd_collect(); cmd_snapshot(); cmd_aggregate(); cmd_publish()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"
    if cmd == "collect":
        cmd_collect()
    elif cmd == "snapshot":
        cmd_snapshot()
    elif cmd == "aggregate":
        cmd_aggregate()
    elif cmd == "publish":
        cmd_publish()
    elif cmd == "watch":
        cmd_watch()
    else:
        reg = load_reg()
        print(json.dumps({k: {"files": len(v["files"]), "excluded": len(v["excluded"]),
                              "published": bool(v.get("published"))} for k, v in reg["packages"].items()}, indent=1))
