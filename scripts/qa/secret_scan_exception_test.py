#!/usr/bin/env python3
"""Contract for the scanner's vendored-file exception (added 2026-11-09).

Why this exists: the IFEval scorer ships the upstream Google Research reference responses
(`gpt4_sample.jsonl`) as byte-pinned vendored data, and those bytes contain third-party
email-like tokens inside generated answer text. The infra scanner's `email_like` rule fired on
them and red the `secret-scan` CI job on every push. The fix must NOT edit the vendored bytes
(the pin is the input to the published reference-band gate), so the scanner carries an explicit,
sha16-bound exception. This test pins that the exception is narrow and non-vacuous:

  * it applies only to the exact path + exact pinned bytes + listed metadata-class rules;
  * a credential-class rule at the same path with the same bytes is NEVER excepted;
  * a byte drift (wrong sha16) removes the exception;
  * the sha16 in the scanner agrees with the published manifest pin;
  * the CALL SITE actually routes the real vendored file through it (a green helper with a
    broken pipeline proves nothing).
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location(
    "secret_scan", ROOT / "scripts" / "security" / "secret_scan.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

VENDOR_REL = "benchmarks/public/vendor/instruction_following_eval/data/gpt4_sample.jsonl"
fails = []
n_checks = 0


def check(name: str, cond: bool, detail: str = "") -> None:
    global n_checks
    n_checks += 1
    print(("PASS " if cond else "FAIL ") + name + ((" :: " + detail) if detail and not cond else ""))
    if not cond:
        fails.append(name)


# 1. rule classification: metadata vs credential
check("email_like_is_metadata", not mod.is_credential_rule("email_like"))
for rule in ("generic-api-key", "private-key", "aws-access-token", "github-oauth", "npm-token"):
    check("credential_rule_%s" % rule, mod.is_credential_rule(rule))
for rule in ("email_like", "private_ip", "absolute_local_path", "ssh_material"):
    check("infra_rule_known_%s" % rule, rule in mod.INFRA_PATTERNS)

# 2. the exception exists and its sha16 matches BOTH the on-disk bytes and the published manifest
excs = {e["path"]: e for e in mod.VENDOR_EXCEPTIONS}
check("one_vendored_exception", VENDOR_REL in excs, "paths=%s" % sorted(excs))
disk = ROOT / VENDOR_REL
disk_sha16 = hashlib.sha1(disk.read_bytes()).hexdigest()[:16] if disk.exists() else ""
check("pinned_bytes_match_disk", bool(disk_sha16) and excs[VENDOR_REL]["sha16"] == disk_sha16,
      "scanner=%s disk=%s" % (excs[VENDOR_REL]["sha16"], disk_sha16))
man = json.loads((ROOT / "benchmarks" / "public" / "MANIFEST.json").read_text(encoding="utf-8"))
man_sha16 = man["benches"]["ifeval"]["reference_response_file"]["sha16"]
check("scanner_pin_matches_manifest", man_sha16 == excs[VENDOR_REL]["sha16"],
      "manifest=%s scanner=%s" % (man_sha16, excs[VENDOR_REL]["sha16"]))

# 2b. no exception record may ever list a credential-class rule (fail-closed invariant)
for e in mod.VENDOR_EXCEPTIONS:
    check("exception_lists_only_metadata_rules_%s" % e["path"].rsplit("/", 1)[-1],
          all(not mod.is_credential_rule(r) for r in e["rules"]), "rules=%s" % (e["rules"],))

# 3. narrowness (tamper controls)
check("excepted_for_pinned_bytes",
      mod.vendored_exception_for(VENDOR_REL, "email_like", disk_sha16) is not None)
check("no_exception_on_byte_drift",
      mod.vendored_exception_for(VENDOR_REL, "email_like", "0" * 16) is None)
check("no_exception_for_credential_rule",
      mod.vendored_exception_for(VENDOR_REL, "generic-api-key", disk_sha16) is None)
check("no_exception_for_other_path",
      mod.vendored_exception_for("benchmarks/public/ifeval.tasks.jsonl", "email_like", disk_sha16) is None)
check("no_exception_for_unlisted_rule",
      mod.vendored_exception_for(VENDOR_REL, "private_ip", disk_sha16) is None)

# 4. call site: the real vendor tree scans clean while the hit is still reported as an exception
findings, excepted = mod.scan_infra_text(ROOT / "benchmarks" / "public" / "vendor")
check("vendor_tree_scans_clean", findings == [], "findings=%s" % findings[:4])
check("call_site_records_exception",
      any(e["file"].endswith("gpt4_sample.jsonl") and e["pinned_sha16"] == disk_sha16
          for e in excepted),
      "excepted=%s" % excepted[:3])

# 5. the scanner summary surfaces suppressed hits instead of dropping them
summary = mod.merge([], excepted)
check("summary_counts_exceptions",
      summary["vendored_metadata_exceptions"] == len(excepted)
      and any(VENDOR_REL in p for p in summary["vendored_exception_pins"]),
      json.dumps(summary)[:200])

print("secret_scan_exception_test: %d checks, %d failures" % (n_checks, len(fails)))
sys.exit(1 if fails else 0)
