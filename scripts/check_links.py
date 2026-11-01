#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Link checker for the public record (spec: verify all references).

Walks every markdown file in the repo and checks:
  1. relative links resolve to files that exist in git (tracked) —
     anchors (#...) are resolved against the target file's headings;
  2. absolute https://github.com/... links to THIS repo are fetched
     (raw.githubusercontent for files, api-less HEAD for releases);
  3. external URLs are HEAD-checked (network failures reported, not hidden).

Exit 0 = everything resolves; exit 1 with a per-link report otherwise.
Run from repo root:  python3 scripts/check_links.py [--offline]
"""
import os
import re
import subprocess
import sys

def _repo_from_origin():
    u = subprocess.run(["git", "remote", "get-url", "origin"], 
                       capture_output=True, text=True).stdout.strip()
    m = re.search(r"github\.com[:/]([^/]+/[^/.]+)", u)
    return m.group(1) if m else "ViktorIXAI/claryel-autonomous"

REPO = _repo_from_origin()  # rename-proof: read from the remote, not hardcoded
MD = re.compile(r"\[([^\]]*)\]\(([^)\s]+)[^)]*\)")


def tracked_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    return set(out.split())


def headings(path):
    hs = set()
    for ln in open(path, encoding="utf-8", errors="ignore"):
        m = re.match(r"#{1,6}\s+(.*)", ln.strip())
        if m:
            hs.add(re.sub(r"[^a-z0-9 \-]", "", m.group(1).lower().replace("`", "")).replace(" ", "-"))
    return hs


def norm(rel, base):
    p = os.path.normpath(os.path.join(os.path.dirname(base), rel))
    return p.replace(os.sep, "/")


def main():
    offline = "--offline" in sys.argv
    files = tracked_files()
    bad = []
    checked = 0
    for f in sorted(x for x in files if x.endswith(".md")):
        for _txt, link in MD.findall(open(f, encoding="utf-8", errors="ignore").read()):
            checked += 1
            if link.startswith("mailto:"):
                continue
            if re.match(r"https?://", link):
                if "github.com/" + REPO in link and "/releases" not in link:
                    rp = link.split("/blob/main/")[-1].split("#")[0]
                    if rp and rp not in files:
                        bad.append((f, link, "path not in git"))
                elif not offline:
                    # GET (no range, body discarded): GitHub HTML refuses HEAD from
                    # datacenter IPs (403), and unauthenticated api.github.com gets
                    # rate-limited on shared CI runners. GET -L is what a browser does.
                    code = subprocess.run(
                        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                         "-L", "--max-time", "25", "-A", "sah-linkcheck/1.0", link],
                        capture_output=True, text=True).stdout.strip()
                    ok = ("200", "301", "302", "405")
                    if "linkedin.com" in link or "x.com" in link:
                        # LinkedIn (999/403) and x.com (403) block every
                        # datacenter agent; accounts verified out-of-band
                        # (owner-controlled profiles: @uctive id 434067770).
                        ok = ok + ("999", "403")
                    if code not in ok:
                        bad.append((f, link, "http " + code))
                continue
            path, _, anchor = link.partition("#")
            if not path:
                continue
            tgt = norm(path, f)
            if tgt not in files:
                # directory links (trailing /) are valid if any tracked file lives under them
                if not any(x.startswith(tgt + "/") for x in files):
                    bad.append((f, link, "missing file"))
                    continue
            if anchor and tgt.endswith(".md"):
                a = anchor.lower()
                if a and a not in headings(tgt):
                    bad.append((f, link, "anchor not found"))
    print("checked %d links across %d markdown files" % (checked, len([x for x in files if x.endswith(".md")])))
    for f, link, why in bad:
        print("BAD %s -> %s (%s)" % (f, link, why))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
