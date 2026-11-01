#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security scanner built around Gitleaks plus archive-aware checks.

The scanner intentionally keeps raw reports outside the repository by default.
Console output contains paths, rule IDs and counts only, never secret values.

Modes:
  --dir PATH        scan files, recursing into nested archives
  --git [PATH]      scan all branches and tags in git history
  --pre-publish     scan the configured publication staging and package trees
  --selftest        verify scanner behavior with synthetic values
"""
import argparse
import collections
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HOME = Path.home()
REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO / ".gitleaks.toml"
PUB = HOME / ".hermes/bench/parb/publish"
DEFAULT_GITLEAKS = shutil.which("gitleaks") or str(HOME / ".local/bin/gitleaks")
VERSION = "8.30.1"
MAX_MB = 300

# Audit patterns. These are deliberately generic and do not include account
# or host values. They supplement Gitleaks for infrastructure metadata.
INFRA_PATTERNS = {
    "private_ip": re.compile(r"\b(?:10(?:\.[0-9]{1,3}){3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b"),
    "absolute_local_path": re.compile(r"/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+"),
    "ssh_material": re.compile(r"ssh\s+-i\s+\S+|\.ssh/[A-Za-z0-9_.-]+\.key|[A-Za-z0-9_.-]+@(?:[0-9]{1,3}\.){3}[0-9]{1,3}"),
    "credential_assignment": re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|password|authorization)\s*[:=]\s*[A-Za-z0-9._~+/-]{12,}"),
    "email_like": re.compile(r"\b[A-Za-z0-9._%+-]+@(?!example\.(?:com|org|net)|[A-Za-z0-9.-]+\.example|invalid|test)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}

CREDENTIAL_RULES = {
    "aws-access-token", "github-pat", "github-fine-grained-pat", "github-oauth",
    "gitlab-pat", "slack-token", "stripe-api-key", "openai-api-key",
    "anthropic-api-key", "private-key", "generic-api-key", "generic-secret",
    "jsonwebtoken", "discord-api-key", "telegram-bot-token", "npm-token",
    "pypi-token", "dockerhub-token", "huggingface-access-token",
}

def parse_report(path):
    data = json.load(open(path, encoding="utf-8"))
    rows = []
    for x in data:
        rows.append({
            "rule": x.get("RuleID") or x.get("ruleId") or "",
            "description": x.get("Description") or x.get("description") or "",
            "file": x.get("File") or x.get("path") or "",
            "commit": (x.get("Commit") or "")[:12],
            "line": x.get("StartLine") or x.get("startLine") or 0,
            "entropy": x.get("Entropy") or x.get("entropy") or 0,
            "secret": x.get("Secret") or "",
        })
    return rows


def run_gitleaks(mode, target, report, extra=None):
    if not os.path.exists(DEFAULT_GITLEAKS):
        raise SystemExit(f"gitleaks not found: install {VERSION} into ~/.local/bin/gitleaks")
    cmd = [DEFAULT_GITLEAKS, mode, str(target), "-c", str(CONFIG), "--redact",
           "--no-banner", "--exit-code", "0", "--max-target-megabytes", str(MAX_MB)]
    if mode == "dir":
        cmd += ["--max-archive-depth", "5", "--max-decode-depth", "5"]
    cmd += extra or []
    cmd += ["-f", "json", "-r", report]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        # Redact possible secrets from tool stderr too.
        err = re.sub(r"(?i)(secret|token|password|key)\s*[:=].*", r"\1=[REDACTED]", r.stderr)
        raise SystemExit(f"gitleaks failed ({r.returncode}): {err[:1200]}")
    return parse_report(report)


def scan_infra_text(target):
    findings = []
    p = Path(target)
    skip = {".git", ".venv", "__pycache__"}
    paths = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and not (skip & set(f.parts))]
    for f in paths:
        try:
            data = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, pat in INFRA_PATTERNS.items():
            for lineno, line in enumerate(data.splitlines(), 1):
                if pat.search(line) and "gitleaks:allow" not in line:
                    findings.append({"rule": name, "file": str(f), "line": lineno})
                    break
    return findings


def merge(rows):
    counts = collections.Counter(f"{r['rule']}|{'credential' if r['rule'] in CREDENTIAL_RULES or re.search(r'api|token|key|secret|password', r['rule'], re.I) else 'metadata'}" for r in rows)
    files = collections.Counter()
    for r in rows:
        # For history reports File may be blob path; keep commit separately.
        files[r["file"]] += 1
    credential = [r for r in rows if "credential" in str(r.get("kind", "")) or r["rule"] in CREDENTIAL_RULES or re.search(r"api|token|key|secret|password", r["rule"], re.I)]
    return {
        "total_findings": len(rows),
        "by_rule": dict(counts),
        "credential_like": len(credential),
        "top_files": files.most_common(20),
    }


def emit(report_path, rows):
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        # Secret field from Gitleaks should already be redacted; defensively remove.
        safe = [{k: v for k, v in r.items() if k != "secret"} for r in rows]
        json.dump(safe, open(report_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(merge(rows), indent=1, ensure_ascii=False))


def selftest(tmp):
    d = Path(tmp) / "canaries"
    d.mkdir()
    # Synthetic values only; never real credentials.
    (d / "aws.txt").write_text("aws_access_key_id=AKIAXYZQ12ABCD34EFGH\naws_secret_access_key=abcdEFGH1234ijklMNOP5678qrstUVWX90yzAB1234\n")  # gitleaks:allow scanner self-test canary
    (d / "ip.txt").write_text("ssh -i ~/.ssh/example-host.key user@192.168.1.10\n")  # gitleaks:allow scanner self-test canary
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir")
    ap.add_argument("--git", nargs="?", const=".", default=None)
    ap.add_argument("--pre-publish", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--report", help="JSON report path outside the repository")
    ap.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="sah-secret-scan-")
    rows = []
    try:
        if args.selftest:
            target = selftest(tmp)
            rows += run_gitleaks("dir", target, os.path.join(tmp, "canary.json"))
            rows += scan_infra_text(target)
            emit(args.report, rows)
            return 0 if rows else 1

        if args.dir:
            rows += run_gitleaks("dir", args.dir, os.path.join(tmp, "dir.json"))
            rows += scan_infra_text(args.dir)
        if args.git:
            rows += run_gitleaks("git", args.git, os.path.join(tmp, "git.json"))
        if args.pre_publish:
            for name in ("staging", "staging-visual", "pkgs"):
                p = PUB / name
                if p.exists():
                    rows += run_gitleaks("dir", p, os.path.join(tmp, f"pub-{name}.json"))
                    rows += scan_infra_text(p)
        if not (args.dir or args.git or args.pre_publish):
            rows += run_gitleaks("dir", ".", os.path.join(tmp, "repo.json"))
            rows += scan_infra_text(".")
        emit(args.report, rows)
        bad = any(r["rule"] in CREDENTIAL_RULES or re.search(r"api|token|key|secret|password", r["rule"], re.I) for r in rows)
        if args.strict and rows:
            return 1
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
