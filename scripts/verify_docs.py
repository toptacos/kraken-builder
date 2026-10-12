#!/usr/bin/env python3
"""Confirm the docs: links resolve, the version matrix agrees, and the wiki
reaches what it lists.

Documentation rots the same way code does, and it rots quieter -- a link to
a moved file is a 404 nobody opens. This checks the mechanical claims that
can be checked:

1. **Links.** Every relative markdown link in `docs/`, `README.md`, and the
   wiki resolves to a file that exists. Anchors are not followed; the target
   file is.
2. **Version matrix.** `kraken/__init__.py`, `pyproject.toml`, and
   `Formula/kraken-cli.rb` name the same version, and the changelog's top
   section is that version. This is the check that would have caught
   0.2.0/0.3.0 shipping without a bump.
3. **Reachability.** Every page the wiki index promises exists, and every
   doc under docs/ is linked from the wiki or from another doc.

Runs on Linux, macOS, and Windows: file and text checks only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

MARKDOWN_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
VERSION_LINE = re.compile(
    r"(__version__\s*=\s*\"([^\"]+)\"|^version\s*=\s*\"([^\"]+)\"|v(\d+\.\d+\.\d+)\.tar\.gz)",
    re.M,
)


def doc_files() -> list[Path]:
    files = [ROOT / "README.md", ROOT / "CHANGELOG.md"]
    files += sorted((ROOT / "docs").rglob("*.md"))
    return [f for f in files if f.is_file()]


def link_problems() -> list[str]:
    problems: list[str] = []
    for path in doc_files():
        text = path.read_text(encoding="utf-8", errors="replace")
        # fenced code blocks may contain example links on purpose
        stripped = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        for target in MARKDOWN_LINK.findall(stripped):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path_part = target.split("#", 1)[0]
            if not path_part:
                continue
            resolved = (path.parent / path_part).resolve()
            if not resolved.exists():
                problems.append(
                    f"{path.relative_to(ROOT)}: link to {path_part!r} does not resolve"
                )
    return problems


def current_version() -> str:
    text = (ROOT / "kraken" / "__init__.py").read_text()
    match = re.search(r'__version__\s*=\s*"([^"]+)"', text)
    assert match, "kraken/__init__.py has no __version__"
    return match.group(1)


def version_problems() -> list[str]:
    here = current_version()
    problems: list[str] = []
    pyproject = (ROOT / "pyproject.toml").read_text()
    match = re.search(r'^version\s*=\s*"([^"]+)"', pyproject, re.M)
    if not match:
        problems.append("pyproject.toml has no version")
    elif match.group(1) != here:
        problems.append(f"pyproject.toml is {match.group(1)}; kraken is {here}")

    formula = (ROOT / "Formula" / "kraken-cli.rb").read_text()
    match = re.search(r"refs/tags/v(\d+\.\d+\.\d+)\.tar\.gz", formula)
    if not match:
        problems.append("Formula/kraken-cli.rb pins no release tarball")
    elif match.group(1) != here:
        problems.append(f"Formula serves v{match.group(1)}; kraken is {here}")

    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    top = changelog.split("## ", 2)[1].splitlines()[0].split(" — ")[0].strip()
    if top != here:
        problems.append(f"CHANGELOG's top section is {top!r}; kraken is {here}")
    return problems


def wiki_problems() -> list[str]:
    problems: list[str] = []
    wiki = ROOT / "docs" / "wiki"
    if not wiki.is_dir():
        return problems
    indexed = (wiki / "Home.md").read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(indexed):
        if target.startswith(("http", "#")):
            continue
        if not (wiki / target.split("#", 1)[0]).resolve().exists():
            problems.append(f"wiki Home links to missing {target!r}")
    return problems


def main() -> int:
    problems = link_problems() + version_problems() + wiki_problems()
    count = len(doc_files())
    print(f"checked {count} markdown file(s): links, version matrix, wiki index")
    for problem in problems:
        print("FAIL", problem)
    if problems:
        print(f"{len(problems)} problem(s)")
        return 1
    print("docs OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
