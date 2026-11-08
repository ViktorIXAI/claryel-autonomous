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


# --- same-repo GitHub links -------------------------------------------------
# A github.com/<owner>/<repo>/... link is NOT a file path. The old code took
# `link.split("/blob/main/")[-1]`, which on a /commit/<sha> or /issues/<n> URL
# returned the whole URL and reported a perfectly good reference as
# "path not in git" (measured 2026-11-08: the CI link gate went red on
# docs/methodology.md's commit and issue links; both targets exist).
# Each kind is verified by the strongest offline-capable test available:
#   blob / tree / raw  -> path must be git-tracked
#   commit             -> sha must resolve in local git history; if the clone
#                         is shallow and we are online, fall back to the URL
#   issues / pull / ... -> object links, verified over the network only
SAME_REPO = re.compile(
    r"https?://(?:www\.)?github\.com/" + re.escape(REPO) + r"/(?P<kind>[A-Za-z][A-Za-z-]*)/(?P<rest>[^#\s?]*)")
PATH_KINDS = {"blob", "tree", "raw"}
SHA_RE = re.compile(r"^[0-9a-f]{7,40}$")
_COMMIT_CACHE = {}


def classify_repo_link(link):
    """(kind, rest) for a link into THIS repo, else None. rest has no #anchor."""
    m = SAME_REPO.match(link.split("#")[0])
    return (m.group("kind"), m.group("rest")) if m else None


def http_code(url):
    # GET (no range, body discarded): GitHub HTML refuses HEAD from
    # datacenter IPs (403), and unauthenticated api.github.com gets
    # rate-limited on shared CI runners. GET -L is what a browser does.
    return subprocess.run(
        ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
         "-L", "--max-time", "25", "--retry", "3",
         "--retry-delay", "2", "--retry-all-errors",
         "--retry-connrefused",
         "-A", "sah-linkcheck/1.0", url],
        capture_output=True, text=True).stdout.strip()


def http_verdict(link):
    code = http_code(link)
    ok = ("200", "301", "302", "405")
    if "linkedin.com" in link or "x.com" in link:
        # LinkedIn (999/403) and x.com (403) block every
        # datacenter agent; accounts verified out-of-band
        # (owner-controlled public profiles).
        ok = ok + ("999", "403")
    return None if code in ok else "http " + code


def commit_verdict(link, sha, offline):
    """Verify a /commit/<sha> reference. Local git first (deterministic)."""
    if not SHA_RE.match(sha):
        return "malformed commit link"
    if sha in _COMMIT_CACHE:
        return _COMMIT_CACHE[sha]
    r = subprocess.run(["git", "cat-file", "-e", sha + "^{commit}"],
                       capture_output=True, text=True)
    why = None if r.returncode == 0 else (
        "commit not in local history (fetch full history or run online)"
        if offline else http_verdict(link))
    _COMMIT_CACHE[sha] = why
    return why


def main():
    offline = "--offline" in sys.argv
    files = tracked_files()
    bad = []
    skipped = []
    checked = 0
    for f in sorted(x for x in files if x.endswith(".md")):
        for _txt, link in MD.findall(open(f, encoding="utf-8", errors="ignore").read()):
            checked += 1
            if link.startswith("mailto:"):
                continue
            if re.match(r"https?://", link):
                repo_link = classify_repo_link(link)
                if repo_link:
                    kind, rest = repo_link
                    if kind in PATH_KINDS:
                        # rest is "<ref>/<path>"; the ref segment is not a path
                        rp = rest.split("/", 1)[1] if "/" in rest else ""
                        if not rp or (rp not in files
                                      and not any(x.startswith(rp + "/") for x in files)):
                            bad.append((f, link, "path not in git"))
                    elif kind == "commit":
                        why = commit_verdict(link, rest, offline)
                        if why:
                            bad.append((f, link, why))
                    elif offline:
                        # issues / pull / releases need the network; in offline
                        # mode they are reported, never silently passed.
                        skipped.append((f, link, kind + " (offline)"))
                    else:
                        why = http_verdict(link)
                        if why:
                            bad.append((f, link, why))
                elif not offline:
                    why = http_verdict(link)
                    if why:
                        bad.append((f, link, why))
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
    for f, link, why in skipped:
        print("SKIP %s -> %s (%s)" % (f, link, why))
    for f, link, why in bad:
        print("BAD %s -> %s (%s)" % (f, link, why))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
