"""Resolve the .kraken chain: system → user → walked project dirs → cwd."""

from __future__ import annotations

import os
from pathlib import Path


MARKER = ".kraken"


def user_home() -> Path:
    return Path(os.environ.get("KRAKEN_HOME", Path.home()))


def system_kraken() -> Path:
    if os.name == "nt":
        base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return base / "kraken"
    return Path(os.environ.get("KRAKEN_SYSTEM_DIR", "/etc/kraken"))


def user_kraken() -> Path:
    return user_home() / MARKER


def walk_kraken_dirs(start: Path | None = None) -> list[Path]:
    """Closest project .kraken last so it wins on merge."""
    here = (start or Path.cwd()).resolve()
    found: list[Path] = []
    for parent in [here, *here.parents]:
        candidate = parent / MARKER
        if candidate.is_dir():
            found.append(candidate)
    found.reverse()
    return found


def config_chain(start: Path | None = None) -> list[Path]:
    chain: list[Path] = []
    sys_dir = system_kraken()
    if sys_dir.is_dir():
        chain.append(sys_dir)
    user_dir = user_kraken()
    if user_dir.is_dir():
        chain.append(user_dir)
    chain.extend(walk_kraken_dirs(start))
    return chain


def ensure_user_layout(home: Path | None = None) -> Path:
    root = (home or user_home()) / MARKER
    for name in ("data", "logs", "tentacles", "cache", "keys"):
        (root / name).mkdir(parents=True, exist_ok=True)
    cfg = root / "config.yaml"
    if not cfg.exists():
        cfg.write_text(
            "version: 1\n"
            "notify: local\n"
            "data_dir: data\n"
            "tentacles: []\n"
        )
    return root


def first_run_init(home: Path | None = None) -> Path:
    """Idempotent. Every CLI command can call this."""
    return ensure_user_layout(home)
