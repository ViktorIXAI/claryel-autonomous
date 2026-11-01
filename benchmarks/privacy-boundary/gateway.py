#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Privacy boundary gateway — PROTOTYPE (design: docs/privacy-architecture.md).

Purpose: if/when a local agent ever consults a cloud model, every outbound
payload passes this gate first. Defaults: DENY EVERYTHING. A payload is
allowed only when (a) the policy file explicitly enables a lane and (b) no
deny-pattern matches after token substitution. This file contains NO real
user data; all tests use synthetic fixtures.

It is a prototype boundary for research, NOT a finished anonymity tool:
regex categories miss paraphrased leaks (an assistant can reconstruct a
person from three facts). The documented mitigation is the local-only
default plus minimal-lane policy, not cleverer regexes.
"""
import json
import os
import re

LANE_DEFAULT = "deny"

# category -> regex; broad by intent (false positives acceptable: deny is cheap)
DENY_PATTERNS = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "phone_russian": r"(?:\+7|8)[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}",
    "lan_ip": r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b",
    "hostname_dotlocal": r"\b[\w-]+\.localhost\b",
    "home_path": r"/home/\w+|[A-Z]:\\Users\\\w+|/Users/\w+",
    "ssh_material": r"ssh-(?:rsa|ed25519)|BEGIN .*PRIVATE KEY|\.ssh/",
    "credential": r"(?i)(api[_-]?key|token|password|secret)\s*[:=]\s*\S{6,}",
    "machine_identity": r"\b(?:[0-9a-f]{2}:){5}[0-9a-f]{2}\b",  # MAC
    "russian_person_fullname": r"\b[А-Я][а-я]{2,}\s+[А-Я][а-я]{2,}\b",
    "lab_machine_labels": r"\b(?:B2003|P2005\w*|P100\d|P3001|mac-studio|claryel\w*)\b",
    "ipv6": r"(?:[0-9a-f]{1,4}:){3,}[0-9a-f]{1,4}:(?:[0-9a-f:]{1,39})",
    "public_ip_v4": r"\b(?!127\.|10\.|192\.168\.)(?:\d{1,3}\.){3}\d{1,3}\b",
}

# lane examples in policy files (explicit operator opt-in per task class)
# {"lanes": {"cloud_assist_code_help": {"allow": true, "max_chars": 4000}}}


def load_policy(path=None):
    if not path or not os.path.exists(path):
        return {"lanes": {}}
    return json.load(open(path, encoding="utf-8"))


def scan(text):
    hits = {}
    for cat, rx in DENY_PATTERNS.items():
        m = re.search(rx, text)
        if m:
            hits[cat] = m.group(0)[:40]
    return hits


def redact(text):
    """replace matched spans with typed placeholders (for synthetic-safe help)."""
    out = text
    for cat, rx in DENY_PATTERNS.items():
        out = re.sub(rx, "<%s>" % cat, out)
    return out


def decide(payload, lane="default", policy_path=None):
    """Return dict(decision, reasons). deny unless lane enabled AND scan clean."""
    pol = load_policy(policy_path)
    lane_cfg = pol.get("lanes", {}).get(lane) or {}
    if LANE_DEFAULT == "deny" and not lane_cfg.get("allow"):
        return {"decision": "deny", "reasons": ["lane_not_enabled:" + lane]}
    hits = scan(payload)
    if hits:
        return {"decision": "deny", "reasons": ["pattern:" + c for c in hits],
                "categories": list(hits)}
    if lane_cfg.get("max_chars") and len(payload) > lane_cfg["max_chars"]:
        return {"decision": "deny", "reasons": ["payload_too_large"]}
    return {"decision": "allow", "reasons": ["lane_enabled", "scan_clean"]}


if __name__ == "__main__":
    import sys
    # tiny CLI demo (synthetic only)
    for p in sys.argv[1:]:
        print(p, "->", decide(p, "cloud_assist_code_help"))
