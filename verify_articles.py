#!/usr/bin/env python3
"""Execute every article step and keep the published output true.

An article that shows a command and its output is a test that rots: the
output was real the afternoon it was written, and nothing re-runs it. This
harness makes that impossible to forget. Convention, per fenced block:

    ```run,sh
    python -m kraken run hello ping
    ```
    ```output
    ...whatever the command actually printed...
    ```

- A block tagged `run,sh` is executed, in order, in one isolated workspace
  with one isolated `KRAKEN_HOME`, so articles can build state (install a
  tentacle, then run it).
- The block immediately after it, tagged `output`, is REPLACED with the real
  stdout+stderr. Nothing in it is hand-written.
- `run,expect-fail` asserts a non-zero exit (for the articles that need to
  show a refusal), which is the contract: exit 0 + ok:false, or exit 2 for a
  transport failure.
- Temp paths, which differ per machine, are rewritten to <tmp> so the
  committed article reads the same on CI as on a laptop.

Usage:
    python3 scripts/verify_articles.py            # execute + rewrite
    python3 scripts/verify_articles.py --check    # CI: fail on drift, no writes
"""

from __future__ import annotations

import os
import re
import shutil
import sysconfig
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARTICLES_DIR = ROOT / "docs" / "articles"

FENCE = re.compile(r"```(?P<info>[^\n`]*)\n(?P<body>.*?)```", re.DOTALL)

#: Every path a reader should not see machine-specific values from.
NORMALIZE_SUBSTRINGS = [
    "/private/var/folders/",  # macOS temp
    "/var/folders/",  # macOS temp symlink target
    "/tmp/",
]


def shell() -> tuple[str, list[str]]:
    if os.name == "nt":
        return "cmd.exe", ["/c"]
    return "/bin/sh", ["-c"]


def normalize(text: str, replacements: list[tuple[str, str]]) -> str:
    for real, fake in replacements:
        text = text.replace(real, fake)
    # Windows and POSIX separators disagree; articles are sh either way.
    text = text.replace("\\", "/")
    return text


def truncate(text: str, limit: int = 60) -> str:
    lines = text.splitlines()
    if len(lines) <= limit:
        return text
    kept = lines[: limit - 1]
    kept.append(f"... ({len(lines) - limit + 1} more lines cut by verify_articles.py)")
    return "\n".join(kept)


def verify_article(path: Path, work: Path, check_only: bool) -> tuple[int, list[str]]:
    src = path.read_text()
    blocks = list(FENCE.finditer(src))
    # Longest first: on macOS the resolved /private/var/... form contains the
    # unresolved /var/... form, so replacing the short one first would leave
    # a "/private<work>" franken-path in the output. The repo root and the
    # stdlib path are normalized too: a traceback printed by a failing
    # tentacle names both, and an article that embeds them only verifies on
    # the machine it was written on.
    stdlib = sysconfig.get_paths()["stdlib"]
    replacements: list[tuple[str, str]] = [
        (str(work.resolve()), "<work>"),
        (str(work), "<work>"),
        (str(ROOT.resolve()), "<repo>"),
        (str(ROOT), "<repo>"),
        (stdlib, "<stdlib>"),
        (str(Path(sys.executable).resolve()), "<python>"),
    ]

    # Article-local state: one home, one workspace, shared by every block.
    home = work / "home"
    cwd = work / "ws"
    home.mkdir(parents=True, exist_ok=True)
    cwd.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env.update(
        KRAKEN_HOME=str(home),
        KRAKEN_OFFLINE="1",
        PYTHONPATH=str(ROOT),
        HOME=str(home),
        # Articles may need a repo file (a bundled tentacle to install);
        # they must never hard-code an absolute path from the author's mac.
        KRAKEN_REPO_ROOT=str(ROOT),
        GIT_CONFIG_NOSYSTEM="1",
    )
    env.pop("KRAKEN_ROOT", None)
    env.pop("KRAKEN_SRC", None)

    exe, dash = shell()
    problems: list[str] = []
    out_parts: list[str] = []
    cursor = 0
    ran = 0

    for i, m in enumerate(blocks):
        info = m.group("info").strip()
        if not info.startswith("run"):
            continue
        # set -e: a block is a demonstration, not a tolerant script. Without
        # it, a failing line in the middle is invisible unless it happens to
        # be the last one -- which is how a "proof" block once shipped three
        # grep errors as its published output.
        body = "set -e\n" + m.group("body")
        expect_fail = "expect-fail" in info
        proc = subprocess.run(
            [exe, *dash, body],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )
        ran += 1
        if expect_fail and proc.returncode == 0:
            problems.append(
                f"{path.name}: block {i} was expected to fail but exited 0:\n{indent(body)}"
            )
        if not expect_fail and proc.returncode != 0:
            problems.append(
                f"{path.name}: block {i} exited {proc.returncode}:\n{indent(body)}\n{indent(proc.stderr[-400:])}"
            )
        observed = truncate(normalize(proc.stdout + proc.stderr, replacements)).strip(
            "\n"
        )

        # The next block must be the output slot.
        nxt = blocks[i + 1] if i + 1 < len(blocks) else None
        if nxt is None or nxt.group("info").strip() != "output":
            problems.append(
                f"{path.name}: run block {i} has no ```output block after it"
            )
            continue
        if nxt.group("body").strip() != observed:
            if check_only:
                problems.append(
                    f"{path.name}: output block {i + 1} is stale\n"
                    f"  published:\n{indent(nxt.group('body'))}\n  actual:\n{indent(observed)}"
                )
            out_parts.append(src[cursor : nxt.start()])
            out_parts.append(make_fence("output", observed))
            cursor = nxt.end()

    if check_only:
        return ran, problems
    out_parts.append(src[cursor:])
    path.write_text("".join(out_parts))
    return ran, problems


def make_fence(info: str, body: str) -> str:
    return f"```{info}\n{body}\n```"


def indent(text: str, prefix: str = "    ") -> str:
    return "\n".join(prefix + line for line in text.splitlines())


def main() -> int:
    check_only = "--check" in sys.argv
    if not ARTICLES_DIR.is_dir():
        print(f"no articles directory at {ARTICLES_DIR}")
        return 0
    articles = sorted(ARTICLES_DIR.glob("*.md"))
    failures = 0
    for path in articles:
        work = Path(tempfile.mkdtemp(prefix=f"kraken-art-{path.stem}-"))
        try:
            ran, problems = verify_article(path, work, check_only)
            status = "OK" if not problems else "FAIL"
            print(f"{status:>4}  {path.name:<40} {ran:>3} steps")
            for p in problems:
                print(p)
            failures += len(problems)
        finally:
            shutil.rmtree(work, ignore_errors=True)
    print()
    if check_only and failures:
        print(f"{failures} problem(s): run scripts/verify_articles.py to refresh")
        return 1
    print(f"{len(articles)} article(s), {failures} problem(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
