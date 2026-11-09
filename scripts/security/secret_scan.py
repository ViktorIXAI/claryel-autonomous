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
import hashlib
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
DEFAULT_GITLEAKS = os.environ.get("GITLEAKS_BIN") or shutil.which("gitleaks") or str(HOME / ".local/bin/gitleaks")
VERSION = "8.30.1"
MAX_MB = 300

# Audit patterns. These are deliberately generic and do not include account
# or host values. They supplement Gitleaks for infrastructure metadata.
INFRA_PATTERNS = {
    "private_ip": re.compile(r"\b(?:10(?:\.[0-9]{1,3}){3}|192\.168\.[0-9]{1,3}\.[0-9]{1,3}|172\.(?:1[6-9]|2[0-9]|3[01])\.[0-9]{1,3}\.[0-9]{1,3})\b"),
    "absolute_local_path": re.compile(r"/home/[A-Za-z0-9_.-]+|/Users/[A-Za-z0-9_.-]+"),
    "ssh_material": re.compile(r"ssh\s+-i\s+\S+|\.ssh/[A-Za-z0-9_.-]+\.key|[A-Za-z0-9_.-]+@(?:[0-9]{1,3}\.){3}[0-9]{1,3}"),
    "credential_assignment": re.compile(r"(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|password|authorization)\s*[:=]\s*[A-Za-z0-9._~+/-]{12,}"),
    "email_like": re.compile(r"\b[A-Za-z0-9._%+-]+@(?i:(?!example\.(?:com|org|net|invalid)|[A-Za-z0-9.-]+\.(?:example|invalid|test)))[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
}

CREDENTIAL_RULES = {
    "aws-access-token", "github-pat", "github-fine-grained-pat", "github-oauth",
    "gitlab-pat", "slack-token", "stripe-api-key", "openai-api-key",
    "anthropic-api-key", "private-key", "generic-api-key", "generic-secret",
    "jsonwebtoken", "discord-api-key", "telegram-bot-token", "npm-token",
    "pypi-token", "dockerhub-token", "huggingface-access-token",
}

# Vendored upstream files whose BYTES are pinned in a published manifest and are themselves input
# to a scored gate. Such a file cannot be sanitized: editing it moves the pin and changes the data
# a published reference band is computed from. An exception is therefore admissible only in this
# explicit shape: exact repo-relative path + the exact sha16 the manifest pins + the exact
# metadata-class rules it tolerates. Credential-class rules are never excepted (enforced in
# `vendored_exception_for`), and every suppressed hit is counted in the summary under
# `vendored_metadata_exceptions`, so a scan never silently loses one. A file that drifts from the
# pinned sha16 gets no exception at all: the exception is bound to the bytes, not to the filename.
VENDOR_EXCEPTIONS = [
    {
        "path": "benchmarks/public/vendor/instruction_following_eval/data/gpt4_sample.jsonl",
        "sha16": "ff57ec6d17688771",
        "rules": ("email_like",),
        "pin": "benchmarks/public/MANIFEST.json -> benches.ifeval.reference_response_file",
        "why": "upstream Apache-2.0 GPT-4 reference responses: third-party email-like tokens occur "
               "inside generated answer text, and these exact bytes are what the pub-ifeval-v1 "
               "reference-band gate scores (strict 416/540, loose 431/540)",
    },
    {
        # Not vendored data: a PUBLISHED ARM artifact. The same admission shape applies, because the
        # rule is the same and the bytes are pinned by publication (the sha16 is printed in
        # benchmarks/public/arms/README.md and IFEVAL-RESULT.md as the row's provenance).
        "path": "benchmarks/public/arms/ifeval-basalt-answers.jsonl",
        "sha16": "543eb8621087e552",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `ifeval-basalt-answers.jsonl` "
               "(that index prints SHA-256/16 445dfa2eba3d12aa; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "IFEval answers are model output, and two answers write a fictional resume whose "
               "contact line uses a placeholder mailbox (a 'John Doe' record) because the task asks "
               "for placeholders. These are placeholder tokens inside scored answer bytes: masking "
               "them would edit the exact bytes the pub-ifeval-v1 checker verdicts were computed "
               "from, and no credential-class rule matches them. (This record deliberately does not "
               "quote the token: a scanner exception that itself carries the pattern trips the "
               "rule it documents.)",
    },
    {
        # Not vendored data: a PINNED PUBLIC TASK FILE. Same admission shape: metadata-class
        # rule only, bytes pinned in MANIFEST.json, every suppressed hit counted.
        "path": "benchmarks/public/bfcl.tasks.jsonl",
        "sha16": "068d359eb0af79b1",
        "rules": ("email_like", "absolute_local_path"),
        "pin": "benchmarks/public/MANIFEST.json -> benches.bfcl.tasks_sha1_16 (that entry also "
               "carries the SHA-256/16 the digest rows print; this pin is the SHA-1/16 this "
               "scanner's byte-binding uses - both name the same bytes)",
        "why": "upstream Apache-2.0 BFCL v4 function-calling data (pinned at the gorilla repo "
               "commit 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8): upstream sample function "
               "arguments carry placeholder mailboxes (a 'Jane Doe' contact record) and a fake "
               "dataset path under a home directory. Editing them would break the gold calls the "
               "bfcl-ast-v1 checker matches against these exact bytes, so the file is pinned by "
               "sha16 instead of sanitized. (This record deliberately does not quote the tokens: "
               "a scanner exception that itself carries the pattern trips the rule it documents.)",
    },
    {
        # Published ARM bytes for the BFCL v4 bare arm: model output that echoes the pinned
        # upstream task data. `publish_pub_bare_arm.py --tasks` proved both occurrences of this
        # token also occur in benchmarks/public/bfcl.tasks.jsonl (SHA-1/16 068d359eb0af79b1),
        # i.e. the path is an argument VALUE the bfcl-ast-v1 checker matched, not a machine path.
        "path": "benchmarks/public/arms/bfcl-basalt-answers.jsonl",
        "sha16": "419e9dbcdff4872d",
        "rules": ("absolute_local_path", "email_like"),
        "pin": "benchmarks/public/arms/README.md index row `bfcl-basalt-answers.jsonl` "
               "(that index prints SHA-256/16 4ac238d09babcb45; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "upstream BFCL v4 function-calling data carries placeholder contact records and a "
               "fake dataset path under a home directory, and answers echo those tokens verbatim as "
               "the argument VALUES the gold requires (a 'John Doe' contact record, a 'send email' "
               "request, a dataset path in `parallel_167`). Masking them would edit the exact bytes "
               "the published 1116/1240 verdicts were computed from - and a masked token is not "
               "valid call syntax, so the shipped arm would stop reproducing its own percent "
               "(measured: the scrubbed copy fails to parse). Same token classes already excepted "
               "for the pinned task file at the matching byte hash. No credential-class rule "
               "matches. (Record does not quote the tokens.)",
    },
    {
        # Published ARM bytes (contour leg), same token classes as the bare arm above: model output
        # that echoes the pinned upstream task data verbatim as argument VALUES the checker matched.
        # Added with the BFCL contour publication (2026-11-09): the answers file of that arm re-scores
        # to the published 1122/1240, which is only true because these bytes were NOT sanitized.
        "path": "benchmarks/public/arms/bfcl-contour-matched-answers.jsonl",
        "sha16": "fb457fd029ea0317",
        "rules": ("absolute_local_path", "email_like"),
        "pin": "benchmarks/public/arms/README.md index row `bfcl-contour-matched-answers.jsonl` "
               "(that index prints SHA-256/16 ed8b58a224521f39; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "the contour arm's answers are model output on the same pinned BFCL v4 tasks, so they "
               "carry the same upstream placeholder mailboxes and the same fake dataset path under a "
               "home directory (proved by the publisher's `--tasks` proof: each token also occurs in "
               "benchmarks/public/bfcl.tasks.jsonl, SHA-1/16 068d359eb0af79b1). Masking them would "
               "edit the bytes the published 1122/1240 verdicts were computed from. No "
               "credential-class rule matches. (Record does not quote the tokens.)",
    },
    {
        # Cloud-arm bytes for the same pinned BFCL v4 set (2026-11-09, codex arm, 300-id cross-arm
        # slice). Same admission shape as the two local BFCL arms above: the answers echo the pinned
        # upstream placeholder contact records verbatim as argument VALUES the checker matched -
        # both mailbox tokens occur verbatim in benchmarks/public/bfcl.tasks.jsonl (SHA-1/16
        # 068d359eb0af79b1), and one of them is the gold value of the task it appears in - so
        # masking would edit scored bytes. Only the email-like metadata rule fires here: this arm's
        # answers contain no path-shaped token at all.
        "path": "benchmarks/public/arms/bfcl-codex-answers.jsonl",
        "sha16": "234766f13fea120f",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `bfcl-codex-answers.jsonl` "
               "(that index prints SHA-256/16 08ce765f1f145d7c; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "model output on the pinned upstream BFCL v4 tasks, which carry placeholder contact "
               "records; the answers echo those tokens verbatim as the argument values the "
               "bfcl-ast-v1 checker matched (proved against the pinned task file, where both tokens "
               "occur and one is the entry's own gold). Masking them would edit the exact bytes the "
               "published 281/300 verdicts were computed from. No credential-class rule matches. "
               "(Record does not quote the tokens.)",
    },
    {
        # The same arm's results file: it carries the same answer bytes plus the harness accounting,
        # which is what makes the row's shape auditable, so it ships unsanitized in the answer field.
        "path": "benchmarks/public/arms/bfcl-contour-matched-results.jsonl",
        "sha16": "7a3841a09f723cd5",
        "rules": ("absolute_local_path", "email_like"),
        "pin": "benchmarks/public/arms/README.md index row `bfcl-contour-matched-results.jsonl` "
               "(that index prints SHA-256/16 ce492b95c4565391; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "same token classes as the answers file of the same arm (the results row carries the "
               "answer alongside the gate/token accounting and `gen.request_shape`); the two "
               "occurrences are the pinned upstream placeholder mailbox and the pinned upstream "
               "dataset path. No credential-class rule matches. (Record does not quote the tokens.)",
    },
    {
        # Published ARM bytes (contour leg): model output, not vendored data.
        "path": "benchmarks/public/arms/ifeval-contour-matched-answers.jsonl",
        "sha16": "c947101b813d5da6",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `ifeval-contour-matched-answers.jsonl` "
               "(that index prints SHA-256/16 e611e76ebdd808cf; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "the contour arm's answers are model output on IFEval tasks that ASK for drafted "
               "emails, so placeholder mailboxes appear inside scored answer bytes; masking them "
               "would edit the exact bytes the pub-ifeval-v1 verdicts were computed from. No "
               "credential-class rule matches. (Record does not quote the token.)",
    },
    {
        # Same arm, sibling results file: carries the same answer bytes.
        "path": "benchmarks/public/arms/ifeval-contour-matched-results.jsonl",
        "sha16": "c52ccca353d4c8d9",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `ifeval-contour-matched-results.jsonl` "
               "(that index prints SHA-256/16 d8a519a5f9b07c18; this pin is SHA-1/16, the "
               "convention this scanner uses - both name the same bytes)",
        "why": "the results rows carry the arm's answer bytes for re-scoring; the same placeholder "
               "mailbox token as the answers file, scored bytes untouched. (Record does not quote "
               "the token.)",
    },
    # ---- repair-arm artifacts (added with pub-repair-v1/v2 and pub-repair-lcb-v1 /
    # pub-repair-bfcl-v1). Same admission shape as the arms above: these are ANSWER bytes that
    # re-score to a published percent, so they may not be sanitized, and only metadata-class rules
    # fire on them. Each token's provenance is checked against an already-pinned byte source.
    {
        "path": "benchmarks/public/arms/pub-repair-v1-merged-answers.jsonl",
        "sha16": "639332eea931294f",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `pub-repair-v1-merged-answers.jsonl`",
        "why": "IFEval repair-arm merged answers: the merged file inherits the pinned bare arm's "
               "answer bytes verbatim for every task the repair did not convert, so the same "
               "placeholder mailbox found in the already-excepted `ifeval-basalt-answers.jsonl` "
               "(proved: the token occurs there at the same task id) appears here too. Masking it "
               "would edit the bytes the pub-repair-v1 verdicts were computed from. No "
               "credential-class rule matches. (Record does not quote the token.)",
    },
    {
        "path": "benchmarks/public/arms/pub-repair-v2-merged-answers.jsonl",
        "sha16": "ee4728cc10e4498f",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `pub-repair-v2-merged-answers.jsonl`",
        "why": "same provenance as the pub-repair-v1 merged file (the retry@2400 arm's merged bytes "
               "carry the pinned bare arm's answer for the same task id, where the placeholder "
               "mailbox already exists in the excepted `ifeval-basalt-answers.jsonl`). No "
               "credential-class rule matches. (Record does not quote the token.)",
    },
    {
        "path": "benchmarks/public/arms/pub-repair-pub-repair-bfcl-v1.jsonl",
        "sha16": "3f5376495bf06e6c",
        "rules": ("email_like",),
        "pin": "benchmarks/public/arms/README.md index row `pub-repair-pub-repair-bfcl-v1.jsonl`",
        "why": "the BFCL repair arm's retry rows are model output on the pinned BFCL v4 tasks, and "
               "one retry echoes the pinned upstream placeholder mailbox verbatim as the argument "
               "value the bfcl-ast-v1 checker matched (proved: that token occurs in "
               "benchmarks/public/bfcl.tasks.jsonl, SHA-1/16 068d359eb0af79b1, already excepted at "
               "that hash). Masking it would edit scored bytes. No credential-class rule matches. "
               "(Record does not quote the token.)",
    },
    {
        "path": "benchmarks/public/arms/pub-repair-bfcl-v1-merged-answers.jsonl",
        "sha16": "897462ba2e7c2d58",
        "rules": ("email_like", "absolute_local_path"),
        "pin": "benchmarks/public/arms/README.md index row `pub-repair-bfcl-v1-merged-answers.jsonl`",
        "why": "merged arm bytes: for unconverted tasks they are the pinned bare arm's answer bytes "
               "verbatim (already excepted at SHA-1/16 419e9dbcdff4872d), and the converted retries "
               "carry the same two upstream token classes - the placeholder mailbox and the fake "
               "dataset path under a home directory, both present in "
               "benchmarks/public/bfcl.tasks.jsonl (SHA-1/16 068d359eb0af79b1) as gold argument "
               "values. Masking them would edit the bytes the 1161/1240 verdicts were computed from. "
               "No credential-class rule matches. (Record does not quote the tokens.)",
    },
]


def is_credential_rule(rule):
    return rule in CREDENTIAL_RULES or bool(re.search(r"api|token|key|secret|password", rule, re.I))


def vendored_exception_for(rel_path, rule, file_sha16):
    """Return the exception record if this hit is covered by a byte-pinned vendored file, else None."""
    if is_credential_rule(rule):
        return None
    for e in VENDOR_EXCEPTIONS:
        if e["path"] == rel_path and rule in e["rules"] and e["sha16"] == file_sha16:
            return e
    return None

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
    """Audit-pattern hits (findings) plus hits covered by a byte-pinned vendored exception."""
    findings, excepted = [], []
    p = Path(target)
    skip = {".git", ".venv", "__pycache__"}
    paths = [p] if p.is_file() else [f for f in p.rglob("*") if f.is_file() and not (skip & set(f.parts))]
    for f in paths:
        try:
            data = f.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = sha = None                      # only paid for on an actual hit
        for name, pat in INFRA_PATTERNS.items():
            for lineno, line in enumerate(data.splitlines(), 1):
                if pat.search(line) and "gitleaks:allow" not in line:
                    if rel is None:
                        try:
                            rel = str(f.resolve().relative_to(REPO.resolve()))
                        except (ValueError, OSError):
                            rel = str(f)
                        sha = hashlib.sha1(f.read_bytes()).hexdigest()[:16]
                    exc = vendored_exception_for(rel, name, sha)
                    if exc:
                        # Report path + rule + pinned sha16, never the matched value.
                        excepted.append({"rule": name, "file": rel, "line": lineno,
                                         "pinned_sha16": sha, "pin": exc["pin"]})
                    else:
                        findings.append({"rule": name, "file": str(f), "line": lineno})
                    break
    return findings, excepted


def merge(rows, excepted=None):
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
        # Suppressed hits are counted, never dropped: a reader of the summary can see that a
        # byte-pinned vendored file matched a metadata rule and under which sha16 pin.
        "vendored_metadata_exceptions": len(excepted or []),
        "vendored_exception_pins": sorted({f"{e['file']}@{e['pinned_sha16']}" for e in (excepted or [])}),
        "top_files": files.most_common(20),
    }


def emit(report_path, rows, excepted=None):
    if report_path:
        Path(report_path).parent.mkdir(parents=True, exist_ok=True)
        # Secret field from Gitleaks should already be redacted; defensively remove.
        safe = [{k: v for k, v in r.items() if k != "secret"} for r in rows]
        json.dump({"findings": safe, "vendored_exceptions": list(excepted or [])},
                  open(report_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print(json.dumps(merge(rows, excepted), indent=1, ensure_ascii=False))


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
    rows, excepted = [], []
    try:
        if args.selftest:
            target = selftest(tmp)
            rows += run_gitleaks("dir", target, os.path.join(tmp, "canary.json"))
            f, e = scan_infra_text(target)
            rows += f; excepted += e
            emit(args.report, rows, excepted)
            return 0 if rows else 1

        if args.dir:
            rows += run_gitleaks("dir", args.dir, os.path.join(tmp, "dir.json"))
            f, e = scan_infra_text(args.dir)
            rows += f; excepted += e
        if args.git:
            rows += run_gitleaks("git", args.git, os.path.join(tmp, "git.json"))
        if args.pre_publish:
            for name in ("staging", "staging-visual", "pkgs"):
                p = PUB / name
                if p.exists():
                    rows += run_gitleaks("dir", p, os.path.join(tmp, f"pub-{name}.json"))
                    f, e = scan_infra_text(p)
                    rows += f; excepted += e
        if not (args.dir or args.git or args.pre_publish):
            rows += run_gitleaks("dir", ".", os.path.join(tmp, "repo.json"))
            f, e = scan_infra_text(".")
            rows += f; excepted += e
        emit(args.report, rows, excepted)
        bad = any(r["rule"] in CREDENTIAL_RULES or re.search(r"api|token|key|secret|password", r["rule"], re.I) for r in rows)
        if args.strict and rows:
            return 1
        return 1 if bad else 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
