#!/usr/bin/env python3
"""Contract test for scripts/check_links.py URL classification (issue: red CI).

Regression this pins: a github.com/<repo>/commit/<sha> or /issues/<n> link is a
repo OBJECT, not a tracked path. The old checker ran `link.split("/blob/main/")`
on every same-repo link, so a perfectly valid commit reference was reported as
"path not in git" and the whole link gate went red on real documentation.

The test builds throwaway git repos in a temp dir, so it needs no network and
never touches this repository. Run:  python3 scripts/qa/check_links_test.py
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
# SAH_LINK_CHECKER lets a reviewer prove this test actually catches the old
# classifier bug by pointing it at a previous revision of the checker.
CHECKER = Path(os.environ.get("SAH_LINK_CHECKER", str(HERE.parent / "check_links.py")))
OWNER_REPO = "testowner/testrepo"


def _git(cwd: Path, *args: str) -> str:
    r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit("git %s failed: %s" % (" ".join(args), r.stderr.strip()))
    return r.stdout.strip()


def build_repo(tmp: Path, links_md: str) -> str:
    """Throwaway repo: commit first, then write the links (which may cite the
    commit sha, only knowable after the commit) and stage them."""
    (tmp / "docs").mkdir(parents=True, exist_ok=True)
    (tmp / "docs" / "a.md").write_text("# Target Heading\n\nbody\n", encoding="utf-8")
    (tmp / "docs" / "b.md").write_text("# B\n", encoding="utf-8")
    (tmp / "README.md").write_text("# seed\n", encoding="utf-8")
    _git(tmp, "init", "-q", "-b", "main")
    _git(tmp, "remote", "add", "origin", "https://github.com/%s.git" % OWNER_REPO)
    _git(tmp, "add", "-A")
    _git(tmp, "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "seed")
    sha = _git(tmp, "rev-parse", "HEAD")
    (tmp / "README.md").write_text(links_md.replace("%SHA%", sha), encoding="utf-8")
    _git(tmp, "add", "-A")
    return sha


def run_checker(tmp: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(CHECKER), "--offline"], cwd=tmp,
                       capture_output=True, text=True)
    return r.returncode, r.stdout


def bad_links(stdout: str) -> set[str]:
    return {ln.split(" -> ", 1)[1].split(" (")[0]
            for ln in stdout.splitlines() if ln.startswith("BAD ")}


def main() -> int:
    fails: list[str] = []
    base = OWNER_REPO

    # --- case 1: every reference kind that must resolve -----------------------
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sha = build_repo(tmp, "\n".join([
            "[blob ok](https://github.com/%s/blob/main/docs/a.md)" % base,
            "[tree ok](https://github.com/%s/tree/main/docs)" % base,
            "[anchor ok](https://github.com/%s/blob/main/docs/a.md#target-heading)" % base,
            f"[commit ok](https://github.com/{base}/commit/%SHA%)",
            "[issue ok offline](https://github.com/%s/issues/25)" % base,
            "[release offline](https://github.com/%s/releases/tag/data-full-2026-11-01)" % base,
            "[external](https://example.com/whatever)",
        ]))
        code, out = run_checker(tmp)
        if code != 0:
            fails.append("case1 exit=%d (expected 0):\n%s" % (code, out))
        if "issues/25" not in out or "releases/tag" not in out:
            fails.append("case1: offline object links must be reported as SKIP, "
                         "never passed silently:\n%s" % out)
        if bad_links(out):
            fails.append("case1: no link may be BAD, got: %s" % sorted(bad_links(out)))

    # --- case 2: the reference kinds that must fail ---------------------------
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        sha = build_repo(tmp, "\n".join([
            f"[commit ok](https://github.com/{base}/commit/%SHA%)",
            "[bad blob](https://github.com/%s/blob/main/docs/missing.md)" % base,
            "[bad tree](https://github.com/%s/tree/main/nope)" % base,
            "[ghost commit](https://github.com/%s/commit/deadbeefdeadbeefdeadbeefdeadbeefdeadbeef)" % base,
            "[malformed commit](https://github.com/%s/commit/not-a-sha)" % base,
            "[other repo path](https://github.com/someone/else/blob/main/x.md)",
        ]))
        code, out = run_checker(tmp)
        bad = bad_links(out)
        if code != 1:
            fails.append("case2 exit=%d (expected 1):\n%s" % (code, out))
        expected_bad = [
            "https://github.com/%s/blob/main/docs/missing.md" % base,
            "https://github.com/%s/tree/main/nope" % base,
            "https://github.com/%s/commit/deadbeefdeadbeefdeadbeefdeadbeefdeadbeef" % base,
            "https://github.com/%s/commit/not-a-sha" % base,
        ]
        for u in expected_bad:
            if u not in bad:
                fails.append("case2: expected BAD for %s, got: %s" % (u, sorted(bad)))
        for u in ["https://github.com/%s/commit/%s" % (base, sha),
                  "https://github.com/someone/else/blob/main/x.md"]:
            if u in bad:
                fails.append("case2: %s must NOT be BAD (offline): %s" % (u, sorted(bad)))

    # --- case 3: classifier unit (anchors, refs, schemes) ---------------------
    sys.path.insert(0, str(HERE.parent))
    import check_links as cl  # noqa: E402  (REPO here is THIS repo's remote)
    this = cl.REPO
    cases = {
        "https://github.com/%s/blob/main/a.md" % this: ("blob", "main/a.md"),
        "https://github.com/%s/blob/main/a.md#heading" % this: ("blob", "main/a.md"),
        "https://github.com/%s/tree/main/dir" % this: ("tree", "main/dir"),
        "https://github.com/%s/commit/abc1234" % this: ("commit", "abc1234"),
        "https://github.com/%s/issues/25" % this: ("issues", "25"),
        "https://github.com/%s/pull/7" % this: ("pull", "7"),
    }
    for link, want in cases.items():
        got = cl.classify_repo_link(link)
        if got != want:
            fails.append("classify(%s) = %r, expected %r" % (link, got, want))
    for other in ("https://github.com/someone/else/blob/main/x.md",
                  "https://example.com/%s/commit/abc" % this):
        if cl.classify_repo_link(other) is not None:
            fails.append("classify(%s) must be None (not this repo)" % other)

    # --- case 4: the shipped documentation links still resolve ----------------
    # Honour the static-QA link mode: SAH_LINK_MODE=offline means the runner has
    # no egress, so the repository pass is asserted in offline mode too.
    repo = Path(__file__).resolve().parents[2]
    args = [sys.executable, str(CHECKER)]
    if os.environ.get("SAH_LINK_MODE", "online") == "offline":
        args.append("--offline")
    r = subprocess.run(args, cwd=repo, capture_output=True, text=True)
    if r.returncode != 0:
        fails.append("the real repository must pass the checker (%s): exit=%d\n%s"
                     % ("offline" if "--offline" in args else "online",
                        r.returncode, r.stdout))

    print("check_links contract: %d case group(s), %d failure(s)" % (4, len(fails)))
    for f in fails:
        print("FAIL " + f)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
