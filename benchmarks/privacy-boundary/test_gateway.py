#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Synthetic privacy-boundary tests. ALL fixtures are invented — no real
person, machine or credential appears here, on purpose.

Run: python benchmarks/privacy-boundary/test_gateway.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gateway import decide, redact, scan

POLICY = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
json.dump({"lanes": {"cloud_assist_code_help": {"allow": True, "max_chars": 2000}}}, POLICY)
POLICY.close()
P = POLICY.name

passed = failed = 0


def check(name, cond):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        print("FAIL:", name)


# 1. default-deny: any lane without policy -> deny even for clean text
d = decide("please review this python function for bugs", "default")
check("default lane denies", d["decision"] == "deny" and "lane_not_enabled" in d["reasons"][0])

# 2. each category must be caught (synthetic fixtures)
LEAKS = {
    "email": "contact jane.doe@example.org for the results",
    "phone_russian": "call me at +7 000 000-00-00",
    "lan_ip": "the endpoint is at 192.168.0.10:8080",
    "home_path": "edit /home/jdoe/project/main.py",
    "ssh_material": "use ssh-rsa [REDACTED] to log in",
    "credential": "api_key = 'supersecret123'",
    "machine_identity": "wake it via mac aa:bb:cc:dd:ee:ff",
    "russian_person_fullname": "письмо от Ивана Петрова",
    "lab_machine_labels": "run it on B2003 first",
    "public_ip_v4": "server 203.0.113.77 is down",
    "hostname_dotlocal": "site http://mysite.localhost/admin",
}
for cat, txt in LEAKS.items():
    d = decide(txt, "cloud_assist_code_help", P)
    check("deny leaks: " + cat, d["decision"] == "deny" and any(cat in r for r in d["reasons"]))

# 3. clean technical text allowed on an enabled lane
d = decide("TypeError: unsupported operand in quantize.py line 42, here is the snippet",
           "cloud_assist_code_help", P)
check("clean text allowed", d["decision"] == "allow")

# 4. redaction neutralizes all categories (then allow on enabled lane)
r = redact(LEAKS["email"] + " " + LEAKS["lan_ip"] + " " + LEAKS["credential"])
check("redact clean", not scan(r))
d = decide(r, "cloud_assist_code_help", P)
check("redacted allowed", d["decision"] == "allow")

# 5. lane size cap enforced
d = decide("x" * 2500, "cloud_assist_code_help", P)
check("size cap", d["decision"] == "deny" and d["reasons"] == ["payload_too_large"])

# 6. combined payload: one leak poisons the whole payload
d = decide("perfectly normal code, oh and 10.1.2.3 is the box", "cloud_assist_code_help", P)
check("poisoned payload denied", d["decision"] == "deny")

# 7. missing policy file -> everything denied
d = decide("clean text", "cloud_assist_code_help", "/nonexistent-policy.json")
check("no policy -> deny", d["decision"] == "deny")

os.unlink(P)
print("GATEWAY TESTS: %d passed, %d failed" % (passed, failed))
raise SystemExit(1 if failed else 0)
