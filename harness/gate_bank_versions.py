#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bank version identity (release 0.0.2.49, tooling-only).

Every published number in this repo must name its bank version next to the bank
sha16. Run records carried `bank_sha16` since 2.45, but `stack.bank_version` was
an empty label fed only by `PARB_BANK_VERSION`, which no runner ever set. This
module is the single resolution point, mirroring the 2.46 `HARNESS_GIT_SHA`
pattern: the builder stamps the identity INTO the generated workspace, and the
runner reads it back. Resolution order, all fail-closed (never a guess):

  1. `bank-version.json` marker written by `scripts/build_hard_v6_ws.py`,
     VALIDATED against the live `bank.json` bytes (marker drift => empty label);
  2. content match: ws `bank.json` parsed and compared byte-for-byte in
     normalized form against the published files in `BANK-VERSIONS.json`
     (works from a repo checkout; a workspace never carries the published
     files, so in a ws this step is simply skipped);
  3. explicit `PARB_BANK_VERSION` env (manual/ad-hoc runs only);
  4. empty label + source reason for the caller to log loudly.

The registry itself is the immutability guard: `check_registry()` fails closed
if any published bank file's current bytes disagree with the sha16 registered
for its version — a published version's bytes may only change by being
superseded by a NEW file + NEW version, which is the standing version rule.

Zero model calls; pure bytes. Named `gate_*` deliberately: the ws builder copies
every `gate_*.py` harness sibling and fails closed on an uncopied import, so
this module lands in every generated workspace without a hand-kept list.
"""
import hashlib
import json
import os

REGISTRY_REL = ("benchmarks", "hard", "BANK-VERSIONS.json")
MARKER_NAME = "bank-version.json"
BANK_NAME = "bank.json"


class BankIdentityError(RuntimeError):
    """A published bank byte moved without a new version, or the registry lies."""


def sha16(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:16]


def file_sha16(path: str) -> str:
    with open(path, "rb") as fh:
        return sha16(fh.read())


def registry_path(repo_root: str) -> str:
    return os.path.join(repo_root, *REGISTRY_REL)


def load_registry(repo_root: str) -> list:
    """Registry entries, schema-checked. Raises on a missing/corrupt registry."""
    p = registry_path(repo_root)
    if not os.path.exists(p):
        raise BankIdentityError("bank registry missing: %s" % p)
    doc = json.load(open(p, encoding="utf-8"))
    entries = doc.get("banks")
    if not isinstance(entries, list) or not entries:
        raise BankIdentityError("bank registry has no `banks` list: %s" % p)
    seen = set()
    for e in entries:
        for k in ("file", "version", "published_sha16"):
            if not str(e.get(k, "")).strip():
                raise BankIdentityError("bank registry entry missing %r: %s" % (k, e))
        if len(str(e["published_sha16"])) != 16:
            raise BankIdentityError("published_sha16 must be 16 hex chars: %s" % e)
        if e["version"] in seen:
            raise BankIdentityError("duplicate bank version %r in registry" % e["version"])
        seen.add(e["version"])
    return entries


def check_registry(repo_root: str) -> list:
    """Fail closed if any published bank file disagrees with its registered bytes."""
    bad = []
    for e in load_registry(repo_root):
        p = os.path.join(repo_root, e["file"])
        if not os.path.exists(p):
            bad.append("%s (%s): file missing" % (e["file"], e["version"]))
            continue
        got = file_sha16(p)
        if got != e["published_sha16"]:
            bad.append("%s (%s): published bytes moved (registered %s, on disk %s) — "
                       "a correction must ship as a NEW file + NEW version, never an "
                       "in-place edit" % (e["file"], e["version"],
                                          e["published_sha16"], got))
    if bad:
        raise BankIdentityError("BANK REGISTRY DRIFT:\n  " + "\n  ".join(bad))
    return load_registry(repo_root)


def resolve_for_file(bank_src: str, repo_root: str):
    """Registry entry for a bank file, matched by name AND exact bytes."""
    try:
        got = file_sha16(bank_src)
    except OSError:
        return None
    base = os.path.basename(bank_src)
    for e in load_registry(repo_root):
        if os.path.basename(e["file"]) == base and e["published_sha16"] == got:
            return e
    return None


def write_marker(ws_out: str, entry: dict, ws_bank_sha16: str, built_utc: str = "") -> str:
    """Stamp the bank version into a generated workspace next to its bank.json."""
    doc = {
        "bank_version": entry["version"],
        "bank_file": os.path.basename(entry["file"]),
        "published_sha16": entry["published_sha16"],
        "ws_bank_sha16": ws_bank_sha16,
        "status": entry.get("status", ""),
        "written_by": "scripts/build_hard_v6_ws.py",
        "built_utc": built_utc,
    }
    path = os.path.join(ws_out, MARKER_NAME)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(doc, fh, ensure_ascii=False, indent=2)
    return path


def read_marker(ws_root: str):
    """Marker dict, or None when absent/malformed (malformed behaves as absent)."""
    p = os.path.join(ws_root, MARKER_NAME)
    if not os.path.exists(p):
        return None
    try:
        doc = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(doc, dict) or not str(doc.get("bank_version", "")).strip():
        return None
    return doc


def version_for_bank_bytes(ws_root: str, repo_root: str):
    """Normalize-match ws bank.json against the published registered files.

    A ws copy is re-serialized (`json.dump`), so hashing never matches the
    published file; identity is in the parsed content. Only exact matches count.
    """
    p = os.path.join(ws_root, BANK_NAME)
    if not repo_root or not os.path.exists(p):
        return None
    try:
        want = json.dumps(json.load(open(p, encoding="utf-8")),
                          ensure_ascii=False, sort_keys=True)
    except Exception:
        return None
    for e in load_registry(repo_root):
        pub = os.path.join(repo_root, e["file"])
        if not os.path.exists(pub):
            continue
        try:
            got = json.dumps(json.load(open(pub, encoding="utf-8")),
                             ensure_ascii=False, sort_keys=True)
        except Exception:
            continue
        if got == want:
            return e
    return None


def run_record_bank_version(ws_root: str, bank_sha16, repo_root: str | None = None):
    """(label, source) for the run record. Never guesses; empty means no identity."""
    m = read_marker(ws_root)
    if m is not None:
        if bank_sha16 and m.get("ws_bank_sha16") == bank_sha16:
            return str(m["bank_version"]).strip(), "marker"
        # marker says one bank, live bank.json bytes say otherwise: the workspace
        # was edited under the marker — the exact identity trap this guards.
        return "", "marker-drift"
    if repo_root is None:
        cand = (os.environ.get("PARB_REPO_ROOT") or "").strip()
        if cand and os.path.exists(registry_path(cand)):
            repo_root = cand
        elif os.path.exists(registry_path(ws_root)):
            repo_root = ws_root
    if repo_root:
        try:
            e = version_for_bank_bytes(ws_root, repo_root)
        except BankIdentityError:
            e = None
        if e:
            return e["version"], "content"
    env = os.environ.get("PARB_BANK_VERSION", "").strip()
    if env:
        return env, "env"
    return "", "none"
