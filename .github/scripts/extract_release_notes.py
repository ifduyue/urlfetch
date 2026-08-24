#!/usr/bin/env python3
"""Extract changelog notes for a version tag into release-notes.md."""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HEADING = re.compile(
    r"^(?P<ver>\S+)\s+\((?P<date>[^)]+)\)\s*\n(?P<underline>[+=~-]+)\s*\n",
    re.MULTILINE,
)


def extract(changelog: str, version: str) -> tuple[str, str] | None:
    matches = list(HEADING.finditer(changelog))
    for i, match in enumerate(matches):
        if match.group("ver") == version:
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(changelog)
            body = changelog[start:end].strip()
            return match.group("date"), body
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tag", help="git tag, e.g. v2.0.1")
    parser.add_argument(
        "-c",
        "--changelog",
        default="doc/changelog.rst",
        type=Path,
        help="path to changelog",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="release-notes.md",
        type=Path,
        help="path to write notes",
    )
    args = parser.parse_args(argv)

    version = args.tag[1:] if args.tag.startswith("v") else args.tag
    changelog = args.changelog.read_text(encoding="utf-8")
    found = extract(changelog, version)
    if found:
        date, body = found
        notes = f"## urlfetch {version} ({date})\n\n{body}\n"
    else:
        notes = (
            f"## urlfetch {version}\n\n"
            "No matching section found in ``doc/changelog.rst``.\n"
        )

    args.output.write_text(notes, encoding="utf-8")
    sys.stdout.write(notes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
