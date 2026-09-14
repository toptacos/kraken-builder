"""Bundled free tentacles. No Docker."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout, user_home
from kraken.core.tentacle import install_local

VANILLA = (
    "geo",
    "filesort",
    "pi-net",
    "vault",
    "store",
    "hotreload",
    "notes",
    "tunnel",
)


def source_root(repo: Path | None = None, home: Path | None = None) -> Path:
    candidates = []
    if repo:
        candidates.append(Path(repo))
    src = os.environ.get("KRAKEN_ROOT") or os.environ.get("KRAKEN_SRC")
    if src:
        candidates.append(Path(src))
    base = Path(home) if home is not None else user_home()
    candidates.append(base / ".kraken" / "src")
    candidates.append(Path(__file__).resolve().parents[2])
    for cand in candidates:
        if (cand / "examples" / "tentacles").is_dir():
            return cand
        nested = cand / "src"
        if (nested / "examples" / "tentacles").is_dir():
            return nested
    return Path(repo or Path.cwd())


def install_vanilla(repo: Path, home: Path | None = None) -> dict[str, Any]:
    ensure_user_layout(home)
    installed = []
    missing = []
    examples = source_root(repo, home) / "examples" / "tentacles"
    for name in VANILLA:
        src = examples / name
        if not src.is_dir():
            missing.append(name)
            continue
        spec = install_local(src, home=home)
        installed.append(spec.get("name") or name)
    return {
        "ok": True,
        "installed": installed,
        "missing": missing,
        "needs_docker": False,
    }
