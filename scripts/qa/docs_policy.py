#!/usr/bin/env python3
"""Documentation freshness and clarity checks.

Modes:
* ``--push``   checks structure, links-to-files, forbidden self-labeling.
* ``--daily``  additionally checks that the public status date is recent.

The daily check is intentionally separate from push checks: a branch can be
reviewed without failing because a calendar date moved. The scheduled job is
the part that enforces the "at least once per day" maintenance policy.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PUBLIC_DOCS = [
    Path("README.md"),
    Path("CONTRIBUTING.md"),
    Path("CHANGELOG.md"),
    Path("docs/documentation-policy.md"),
    Path("docs/source-policy.md"),
    Path("docs/methodology.md"),
    Path("docs/reproduction-guide.md"),
    Path("versions/VERSIONS.md"),
]
FORBIDDEN_PUBLIC_PHRASES = [
    "scientific study",
    "scientific evidential",
    "scientific methodology",
    "research history",
    "research infrastructure",
    "research repository",
    "live research infrastructure",
    "research questions",
    "reproducible research",
    "the research runs",
    "study which improvements",
]
REQUIRED_README_MARKERS = [
    "# Claryel Autonomous Harness",
    "Status checked:",
    "Current version",
    "Headline results",
    "How to use",
    "Documentation policy",
    "Source and citation policy",
]


def rel(path: Path) -> Path:
    return path.relative_to(ROOT)


def check_readme(fresh: bool, failures: list[str]) -> None:
    readme = ROOT / "README.md"
    if not readme.exists():
        failures.append("README.md is missing")
        return
    text = readme.read_text(encoding="utf-8")
    for marker in REQUIRED_README_MARKERS:
        if marker not in text:
            failures.append(f"README.md missing marker: {marker!r}")

    if fresh:
        m = re.search(r"Status checked:\s*(\d{4}-\d{2}-\d{2})", text)
        if not m:
            failures.append("README.md missing `Status checked: YYYY-MM-DD`")
        else:
            try:
                checked = dt.date.fromisoformat(m.group(1))
            except ValueError as exc:
                failures.append(f"bad README status date: {exc}")
            else:
                age = (dt.date.today() - checked).days
                if age > 1:
                    failures.append(
                        f"README status date is stale: {checked.isoformat()} "
                        f"is {age} days old"
                    )

    for line in text.splitlines():
        if line.startswith("git clone https://github.com/"):
            continue
        for phrase in FORBIDDEN_PUBLIC_PHRASES:
            if phrase.lower() in line.lower():
                failures.append(f"README.md forbidden phrase: {phrase!r}")


def check_public_docs(failures: list[str]) -> None:
    for path in PUBLIC_DOCS:
        file_path = ROOT / path
        if not file_path.exists():
            failures.append(f"required public doc missing: {path}")
            continue
        for n, line in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith(("git clone", "u=", "url=")):
                continue
            for phrase in FORBIDDEN_PUBLIC_PHRASES:
                if phrase.lower() in line.lower():
                    # Allow quoted examples in the policy itself.
                    if line.strip().startswith(('- "', '- “')):
                        continue
                    failures.append(f"{path}:{n}: forbidden phrase: {phrase!r}")


def check_markdown_links(failures: list[str]) -> None:
    for path in (ROOT / "README.md", ROOT / "docs/documentation-policy.md", ROOT / "docs/source-policy.md"):
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for match in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", text):
            href = match.group(2)
            if href.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = (path.parent / href.split("#", 1)[0]).resolve()
            if not target.exists():
                failures.append(f"{rel(path)} broken local link: {href}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--daily", action="store_true")
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()

    failures: list[str] = []
    check_readme(fresh=args.daily, failures=failures)
    check_public_docs(failures)
    check_markdown_links(failures)

    if failures:
        print("DOCS POLICY: FAIL")
        for f in failures:
            print(" -", f)
        return 1

    mode = "daily" if args.daily else "push"
    print(f"DOCS POLICY: PASS ({mode})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
