#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a sanitized visual experiment archive for GitHub release publication.

Raw local browser runs contain Chrome profiles, absolute home paths and
machine-specific engine paths. This builder keeps experiment evidence
(prompts, generated artifacts, validation JSON, logs, screenshots, videos)
while excluding browser profile/cache data and replacing local filesystem
paths with portable placeholders.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

HOME = os.path.expanduser("~")
SRC = os.path.join(HOME, ".hermes", "bench", "visbench")
REPO = os.path.join(HOME, "projects", "strata-autonomous-harness")
PUB = os.path.join(HOME, ".hermes", "bench", "parb", "publish")
STAGE = os.path.join(PUB, "staging-visual")
PKGS = os.path.join(PUB, "pkgs")
PUBLISH_ENV = os.path.join(HOME, ".hermes", "bench", "parb", "publish.env")


def load_private_patterns():
    if not os.path.exists(PUBLISH_ENV):
        return []
    for line in open(PUBLISH_ENV, encoding="utf-8"):
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):]
        if line.startswith("SAH_SECRET_PATTERNS_JSON="):
            raw = line.split("=", 1)[1].strip().strip('"').strip("'")
            return json.loads(raw)
    return []


PRIVATE = load_private_patterns()
TEXT_EXT = {"html", "txt", "json", "log", "js", "py", "md", "svg", "css", "jsonl"}
SKIP_DIRS = {
    "Default", "Cache", "Code Cache", "Service Worker", "frames", "vv", "vv2", "vv3",
    "vendor-private",
}


def skip_path(rel):
    parts = rel.split(os.sep)
    if any(part.startswith("chrome-") for part in parts):
        return True
    if any(part in SKIP_DIRS for part in parts):
        return True
    return False


def selected(base):
    files = []
    for dp, dirs, names in os.walk(os.path.join(SRC, base)):
        rel_dir = os.path.relpath(dp, SRC)
        if skip_path(rel_dir):
            continue
        for name in names:
            rel = os.path.join(rel_dir, name)
            if skip_path(rel):
                continue
            ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if base in ("contour-series", "contour1", "contour2"):
                if ext not in TEXT_EXT and ext not in ("png", "mp4", "jpg"):
                    continue
            files.append(rel)
    return files


def top_files():
    names = [
        "all_runs_summary.json", "README.md", "x_posts_en.md",
        "prompt.txt", "pelican_prompt.txt", "pelican_prompt_animated.txt",
        "pelican_prompt_hard.txt", "pagoda_prompt.txt",
        "ball_first_full.html", "ball_first_en.mp4",
        "balls_variant1_square_en.mp4", "pel_showcase_en.mp4", "showcase_en.mp4",
        "showcase_en.jpg", "pel_showcase_en.jpg", "index.html",
        "solo-ball-seed0/index.html",
    ]
    return [n for n in names if os.path.isfile(os.path.join(SRC, n))]


def sanitize_text(rel, data):
    # Keep benchmark evidence readable but portable/private.
    out = data
    out = re.sub(rf"{re.escape(os.path.join(HOME, '.hermes', 'bench', 'visbench'))}", "$VISBENCH", out)
    out = re.sub(rf"{re.escape(os.path.join(HOME, '.hermes', 'bench'))}", "$HOME/.hermes/bench", out)
    out = re.sub(rf"/home/{re.escape('claryel001')}", "$HOME", out)
    out = re.sub(rf"/home/{re.escape('viktor')}", "$HOME", out)
    out = re.sub(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b", "[local-network-redacted]", out)
    for pat in PRIVATE:
        out = re.sub(pat, "[REDACTED]", out)
    return out


def add_file(path, out_dir, manifest):
    rel = os.path.relpath(path, SRC)
    src = os.path.join(SRC, rel)
    dst = os.path.join(out_dir, rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    ext = rel.rsplit(".", 1)[-1].lower() if "." in rel else ""
    if ext in TEXT_EXT:
        text = open(src, encoding="utf-8", errors="replace").read()
        text = sanitize_text(rel, text)
        open(dst, "w", encoding="utf-8").write(text)
    else:
        shutil.copy2(src, dst)
    with open(dst, "rb") as f:
        digest = hashlib.sha256(f.read()).hexdigest()
    manifest["files"].append({
        "path": rel.replace(os.sep, "/"),
        "bytes": os.path.getsize(dst),
        "sha256": digest,
    })


def main():
    tag = "visual-release-2026-11-01-v2"
    out = os.path.join(PUB, "tmp_" + tag)
    if os.path.exists(out):
        shutil.rmtree(out)
    os.makedirs(out, exist_ok=True)
    manifest = {
        "package": tag,
        "created_utc": time.strftime("%FT%TZ", time.gmtime()),
        "source": "~/.hermes/bench/visbench",
        "sanitizer": "browser profiles/cache excluded; local paths and known private patterns redacted",
        "files": [],
        "skipped_categories": ["chrome profile", "cache", "frames", "vv"],
    }
    groups = ["contour1", "contour2", "contour-series", "contour-series2", "solo-ball-seed0"]
    for g in groups:
        for rel in selected(g):
            add_file(os.path.join(SRC, rel), out, manifest)
    for rel in top_files():
        add_file(os.path.join(SRC, rel), out, manifest)
    json.dump(manifest, open(os.path.join(out, tag + ".manifest.json"), "w"), indent=1, ensure_ascii=False)
    os.makedirs(PKGS, exist_ok=True)
    pkg = f"{tag}.tar.zst"
    fmt = "tar.zst"
    if subprocess.run("command -v zstd", shell=True, capture_output=True).returncode != 0:
        fmt = "tar.gz"
        pkg = f"{tag}.tar.gz"
    flag = "--zstd" if fmt == "tar.zst" else "-z"
    r = subprocess.run(f"tar {flag} -cf {PKGS}/{pkg} -C {out} .", shell=True, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stderr)
        sys.exit(1)
    gate = subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts", "security", "secret_scan.py"),
         "--dir", os.path.join(PKGS, pkg),
         "--report", os.path.join(PUB, "security-visual-package.json")],
        capture_output=True, text=True)
    print("SECURITY-GATE visual-package rc", gate.returncode, gate.stdout[-500:] if gate.returncode else "")
    if gate.returncode != 0:
        sys.exit(1)
    shutil.rmtree(out)
    print(json.dumps({
        "package": tag,
        "asset": os.path.join(PKGS, pkg),
        "files": len(manifest["files"]),
        "bytes": sum(x["bytes"] for x in manifest["files"]),
    }, indent=1))


if __name__ == "__main__":
    main()
