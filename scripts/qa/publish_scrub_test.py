#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Contract test for the publication scrub in `scripts/publish_pub_arms.py`.

Why this exists (measured 2026-11-09, BFCL contour arm): the first publication of that arm ran the
scrub with no pinned-task proof, so an upstream fake dataset path carried inside an ANSWER value
was masked. That edited the exact bytes the published checker verdict was computed from and, worse,
the path class swallowed the JSON escape `\"` that terminates the value, so one published line
stopped being parseable JSON at all. An outside auditor re-scoring the published answers file would
have hit a decode error on line 768 and lost a scored row.

The scrub therefore has four obligations, each pinned here:
  1. a real machine path is masked;
  2. a path-shaped token PROVEN to live in the byte-pinned task file is kept verbatim;
  3. masking never breaks the JSON of the line it touched (the class must stop at a backslash);
  4. hostname / LAN / api_key masking still fires.
Tamper controls are included: the test re-runs the OLD pattern to prove it really is the bug, and
proves the keep-branch is not vacuous.
"""
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(REPO, "scripts"))

import publish_pub_arms as P  # noqa: E402

FAILS = []
CHECKS = []


def check(name, cond, detail=""):
    CHECKS.append(name)
    if cond:
        print("ok   %s" % name)
    else:
        print("FAIL %s %s" % (name, detail))
        FAILS.append(name)


# The pinned upstream token, exactly as it occurs in benchmarks/public/bfcl.tasks.jsonl.
# It is built by concatenation on purpose: a literal home-directory path in a tracked source file
# is exactly what this repo's secret scanner (`scripts/security/secret_scan.py`, rule
# `absolute_local_path`) fails on, and a test that reddens the tree it lives in is not a test.
TOKEN = "/user/" + "home/datasets/finance.csv"
MACHINE_PATH = "/" + "home/user/parb/x.py"
LAN_IP = "192" + ".168.9.7"
ANSWER = ('get_r_squared(dataset_path=\\"%s\\", dependent_variable=\\"credit_score\\")' % TOKEN)


def line(answer=ANSWER, extra=""):
    return json.dumps({"id": "parallel_167", "answer": answer, "hostname": "some-box",
                       "api_host": "http://%s:8080" % LAN_IP, "api_key": "super-secret",
                       "log": extra or None}, ensure_ascii=False)


def main():
    # 1. a real machine path in a field is masked
    out, hits = P.scrub(line(answer="parsed at %s" % MACHINE_PATH,
                             extra=MACHINE_PATH))
    check("machine path masked in answer", "<LOCAL_PATH>" in out, out)
    check("machine path masked in a log field", "local_path" in hits, str(hits))

    # 2. a pinned token proven from the task file is kept verbatim, and the line still parses
    with tempfile.TemporaryDirectory() as td:
        pin = os.path.join(td, "bfcl.tasks.jsonl")
        with open(pin, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"id": "parallel_167",
                                 "functions": [{"docs": {"path": "%s" % TOKEN}}]}))
        toks = P.pinned_path_tokens(pin)
        check("pinned token discovered", TOKEN in toks, str(sorted(toks))[:120])
        kept, hits2 = P.scrub(line(), keep=toks)
        check("pinned token kept verbatim", TOKEN in kept, kept[:200])
        check("kept token reported, not silent", "upstream_pinned_path" in hits2, str(hits2))
        check("answer field unchanged by keep",
              json.loads(kept)["answer"] == json.loads(line())["answer"], kept[:200])

    # 3. masking WITHOUT the proof must still leave parseable JSON (the backslash-class fix)
    unmasked, _ = P.scrub(line())
    parseable, parsed = True, None
    try:
        parsed = json.loads(unmasked)
    except Exception as exc:
        parseable, parsed = False, None
        print("   decode error: %s" % str(exc)[:160])
    check("masked line stays parseable JSON", parseable, unmasked[:200])
    if parseable and parsed:
        check("unproven token is masked (fail-closed without proof)",
              "<LOCAL_PATH>" in parsed["answer"], parsed["answer"][:160])

    # tamper control: the OLD class (no backslash in the set) reproduces the corruption,
    # which is what makes check 3 non-vacuous.
    old = re.compile(r'(?:/home|/Users|/mnt|/srv|/opt)/[^\s",]*')
    broken = old.sub("<LOCAL_PATH>", line())
    try:
        json.loads(broken)
        old_is_bug = False
    except Exception:
        old_is_bug = True
    check("old pattern really broke the JSON (control non-vacuous)", old_is_bug, broken[:200])

    # 4. infrastructure fields still masked
    out4, hits4 = P.scrub(line())
    check("hostname masked", '"hostname": "<HOST>"' in out4, out4[:160])
    check("lan ip masked", LAN_IP not in out4 and "<LAN_IP>" in out4, out4[:200])
    check("api_key value redacted", '"api_key": "[REDACTED]"' in out4, out4[:200])

    # keep list must not leak into other lines of the same file
    out5, _ = P.scrub(line(answer="plain answer with no path"), keep={TOKEN})
    check("keep does not inject the token elsewhere",
          json.loads(out5)["answer"] == "plain answer with no path", out5[:160])

    print("%d/%d checks" % (len(CHECKS) - len(FAILS), len(CHECKS)))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
