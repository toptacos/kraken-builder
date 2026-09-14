"""Bundled free tentacles. No Docker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout
from kraken.core.tentacle import install_local

VANILLA = ("geo", "filesort", "pi-net", "vault", "store", "hotreload", "notes", "tunnel")


def install_vanilla(repo: Path, home: Path | None = None) -> dict[str, Any]:
    ensure_user_layout(home)
    installed = []
    missing = []
    examples = repo / "examples" / "tentacles"
    for name in VANILLA:
        src = examples / name
        if not src.is_dir():
            missing.append(name)
            continue
        spec = install_local(src, home=home)
        installed.append(spec.get("name") or name)
    return {"ok": True, "installed": installed, "missing": missing, "needs_docker": False}
