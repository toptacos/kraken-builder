"""Resolve the .kraken chain: system → user → walked project dirs → cwd."""

from __future__ import annotations

import os
import sys
from pathlib import Path


MARKER = ".kraken"

_WARNED_HOME: set[str] = set()


def user_home() -> Path:
    """KRAKEN_HOME is the home directory, not the .kraken directory.

    Setting it to `~/.kraken` is the natural mistake and it is silent: the
    resolver appends .kraken, so every tentacle lands in `~/.kraken/.kraken`
    and nothing complains. Warn once rather than fail -- pointing KRAKEN_HOME at
    a directory that happens to be named .kraken is legitimate, just unlikely.
    """
    raw = os.environ.get("KRAKEN_HOME")
    if raw and Path(raw).name == MARKER and raw not in _WARNED_HOME:
        _WARNED_HOME.add(raw)
        print(
            f"kraken: KRAKEN_HOME={raw} looks like the .kraken directory, but "
            f"KRAKEN_HOME is the home directory and .kraken is appended to it. "
            f"Expect {Path(raw) / MARKER}; set KRAKEN_HOME to its parent to write "
            f"into {raw} directly.",
            file=sys.stderr,
        )
    return Path(raw) if raw else Path.home()


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


#: Directories created under the Kraken home. The first four are configurable
#: (data_dir, log_dir, cache_dir, key_dir); the rest are structural.
STRUCTURAL_DIRS = ("tentacles",)


def layout_dirs() -> dict[str, str]:
    """Configured directory names, falling back to the schema defaults."""
    from kraken.core.config import load_config
    from kraken.core.config_schema import BY_KEY

    cfg = load_config()
    out: dict[str, str] = {}
    for key in ("data_dir", "log_dir", "cache_dir", "key_dir"):
        value = cfg.get(key)
        out[key.removesuffix("_dir")] = (
            str(value) if isinstance(value, str) and value else BY_KEY[key].default
        )
    return out


def data_root(home: Path | None = None) -> Path:
    """Where arms keep their data. Honours `data_dir`."""
    return (home or user_home()) / MARKER / layout_dirs()["data"]


def ensure_user_layout(home: Path | None = None) -> Path:
    root = (home or user_home()) / MARKER
    names = set(layout_dirs().values()) | set(STRUCTURAL_DIRS)
    for name in names:
        (root / name).mkdir(parents=True, exist_ok=True)
    cfg = root / "config.yaml"
    if not cfg.exists():
        cfg.write_text("version: 1\nnotify: local\ndata_dir: data\ntentacles: []\n")
    return root


def first_run_init(home: Path | None = None) -> Path:
    """Idempotent. Every CLI command can call this."""
    return ensure_user_layout(home)
