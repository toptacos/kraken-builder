"""A tentacle may declare the runtime it needs. This answers "is it here?".

A tentacle is any executable, so the runtime it needs is the tentacle's
business -- and core's business to check before running it, the way a
Dockerfile's `FROM node:18` is a contract rather than a hope. Declared
requirements live in the manifest:

    requires:
      python: ">=3.11"
      node: ">=18"

The rule that keeps this free: **a requirement that is not declared is
never probed**. Most tentacles declare nothing, pay nothing, and spawn
nothing. `python` is answered from `sys.version_info` without a process;
anything else shells out once per process and caches, because asking node
for its version twenty times is twenty spawns.

Constraints use the same grammar as every other version bound in core
(>=, <=, >, <, ==, ~, ^, space-separated AND) -- see kraken.core.semver.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from typing import Any

#: tool -> the command that prints its version. python is absent on purpose:
#: it is answered in-process.
_VERSION_CMD: dict[str, tuple[str, ...]] = {
    "node": ("node", "--version"),
    "bash": ("bash", "--version"),
    "sh": ("sh", "--version"),
    "zsh": ("zsh", "--version"),
    "php": ("php", "--version"),
    "ruby": ("ruby", "--version"),
    "perl": ("perl", "-e", "print $]"),
    "go": ("go", "version"),
    "rustc": ("rustc", "--version"),
    "cargo": ("cargo", "--version"),
    "docker": ("docker", "--version"),
    "git": ("git", "--version"),
}

_FIRST_VERSION = re.compile(r"(\d+)\.(\d+)(?:\.(\d+))?")

#: (tool -> version), filled on first ask and never re-asked.
_CACHE: dict[str, str | None] = {}


def python_version() -> str:
    """The interpreter running core, as x.y.z. No process, ever."""
    return "%d.%d.%d" % sys.version_info[:3]


def probe(tool: str) -> str | None:
    """The installed version of `tool`, or None when it is not installed.

    Cached per process: a `kraken run` that resolves five tentacles asking
    about node shells out once, not five times.
    """
    if tool in _CACHE:
        return _CACHE[tool]
    version: str | None = None
    if tool in {"python", "python3"}:
        version = python_version()
    else:
        cmd = _VERSION_CMD.get(tool)
        if cmd is not None:
            exe = shutil.which(cmd[0])
            if exe is None:
                version = None
            else:
                try:
                    proc = subprocess.run(
                        [exe, *cmd[1:]],
                        capture_output=True,
                        text=True,
                        timeout=10,
                        check=False,
                    )
                    match = _FIRST_VERSION.search(proc.stdout or proc.stderr or "")
                    if match:
                        version = "%s.%s.%s" % (
                            match.group(1),
                            match.group(2),
                            match.group(3) or "0",
                        )
                except (OSError, subprocess.SubprocessError):
                    version = None
    _CACHE[tool] = version
    return version


def requirements(spec: dict[str, Any] | None) -> dict[str, Any]:
    raw = (spec or {}).get("requires") or {}
    return raw if isinstance(raw, dict) else {}


#: keys in `requires` that are not toolchains; handled elsewhere.
NON_TOOLS = {"protocol", "core", "tentacles"}


def declared_tools(spec: dict[str, Any] | None) -> dict[str, str]:
    """The toolchain requirements a manifest declares, as {tool: bound}."""
    out: dict[str, str] = {}
    for key, value in requirements(spec).items():
        if key in NON_TOOLS or value in (None, "", "*", "any", "optional"):
            continue
        out[str(key)] = str(value)
    return out


def check(spec: dict[str, Any] | None) -> list[str]:
    """Human sentences for every declared toolchain this box cannot satisfy.

    An empty list means "nothing declared, or everything satisfied" -- the
    caller raises nothing.
    """
    from kraken.core.semver import satisfies

    problems: list[str] = []
    for tool, bound in declared_tools(spec).items():
        have = probe(tool)
        if have is None:
            problems.append(f"requires {tool} {bound}, which is not installed")
        elif not satisfies(have, bound):
            problems.append(f"requires {tool} {bound}; have {have}")
    return problems
