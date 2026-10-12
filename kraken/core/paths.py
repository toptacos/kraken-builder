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
    # The override wins on every platform. It used to be POSIX-only, which
    # made the system scope invisible on Windows -- tests could not point it
    # anywhere, and an admin could not move it off ProgramData.
    override = os.environ.get("KRAKEN_SYSTEM_DIR")
    if override:
        return Path(override)
    if os.name == "nt":
        base = Path(os.environ.get("PROGRAMDATA", r"C:\ProgramData"))
        return base / "kraken"
    return Path("/etc/kraken")


def user_kraken() -> Path:
    return user_home() / MARKER


def _key(path: Path) -> str:
    text = str(path)
    return text.lower() if os.name == "nt" else text


def walk_kraken_dirs(start: Path | None = None) -> list[Path]:
    """Closest project .kraken last so it wins on merge.

    The system and user scopes are first-class entries in the chain already,
    so they are skipped here. Without that, running from anywhere under the
    home directory -- which is most invocations -- finds ~/.kraken twice:
    once as the user scope and again as a "project" scope that outranks it.

    The walk also stops at the home directory. Climbing all the way to the
    filesystem root picks up .kraken directories that belong to nobody's
    project: on a CI runner, ~/.kraken is created by the CLI smoke steps and
    every later "sandboxed" config test then read it as project config,
    silently overriding the user scope. A project lives below the home, or
    it is not a project.
    """
    here = (start or Path.cwd()).resolve()
    reserved = set()
    for scope in (system_kraken(), user_kraken()):
        reserved.add(_key(scope))
        try:
            reserved.add(_key(scope.resolve()))
        except OSError:
            pass
    home = user_home()
    home_keys = {_key(home)}
    try:
        home_keys.add(_key(home.resolve()))
    except OSError:
        pass
    found: list[Path] = []
    seen: set[str] = set()
    for parent in [here, *here.parents]:
        if _key(parent) in home_keys:
            break
        candidate = parent / MARKER
        if not candidate.is_dir() or _key(candidate) in reserved:
            continue
        # Windows paths are case-insensitive, so the same directory can be
        # reached under two spellings; one entry per directory, not per
        # spelling, or the chain reports duplicate scopes.
        if _key(candidate) not in seen:
            seen.add(_key(candidate))
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
