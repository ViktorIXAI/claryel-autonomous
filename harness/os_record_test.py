#!/usr/bin/env python3
"""Behaviour contracts for the OS record used in gates and logs."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import os_record as R


def check(name, ok):
    print(("ok " if ok else "FAIL ") + name)
    return 0 if ok else 1


fails = 0

text = '''NAME="Ubuntu"
VERSION_ID="24.04.5"
VERSION="24.04.5 LTS (Noble Numbat)"
VERSION_CODENAME=noble
ID=ubuntu
'''
parsed = R.parse_os_release(text)
fails += check("os release parsed", parsed["VERSION_CODENAME"] == "noble")
fails += check("os release quoted", parsed["VERSION_ID"] == "24.04.5")

fails += check("ubuntu desktop package",
    R.classify_flavor(parsed, {"ubuntu-desktop": "ii", "ubuntu-server": "un"}) == ("desktop", "ubuntu-desktop metapackage"))

fails += check("ubuntu server package",
    R.classify_flavor(parsed, {"ubuntu-desktop": "ab", "ubuntu-server": "ii", "gnome-shell": "un"}) == ("server", "ubuntu-server metapackage"))

fails += check("headless without ubuntu metapackages",
    R.classify_flavor(parsed, {"ubuntu-desktop": "ab", "ubuntu-server": "ab"}) == ("server", "headless default"))

fails += check("active GNOME without desktop metapackage",
    R.classify_flavor(parsed, {"ubuntu-desktop": "ab", "ubuntu-server": "ab", "gnome-shell": "ii"}, active_display=True) == ("desktop", "desktop session or display manager"))

fails += check("variant wins",
    R.classify_flavor({"VARIANT_ID": "server"}, {"ubuntu-desktop": "ii"}) == ("server", "VARIANT_ID=server"))

print("GATE OS RECORD:", "PASS" if fails == 0 else "FAIL")
sys.exit(fails)
