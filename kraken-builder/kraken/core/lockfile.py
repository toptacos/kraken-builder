"""~/.kraken/tentacles.lock — one version per name."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout


def lock_path(home: Path | None = None) -> Path:
    return ensure_user_layout(home) / "tentacles.lock"


def load_lock(home: Path | None = None) -> dict[str, Any]:
    path = lock_path(home)
    if not path.exists():
        return {"v": 1, "tentacles": {}}
    return json.loads(path.read_text() or "{}")


def record(name: str, version: str, source: str = "", home: Path | None = None) -> dict[str, Any]:
    data = load_lock(home)
    data.setdefault("v", 1)
    data.setdefault("tentacles", {})
    data["tentacles"][name] = {"version": version, "source": source}
    lock_path(home).write_text(json.dumps(data, indent=2) + "\n")
    return data
