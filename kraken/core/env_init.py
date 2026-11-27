"""Write a plan-only compose workstation into a directory."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

TEMPLATE_FILES = (
    Path(".kraken") / "config.yaml",
    Path("compose.yaml"),
    Path("project.yaml"),
    Path("mycelium.toml"),
    Path("README.md"),
)


def template_root() -> Path:
    return Path(__file__).resolve().parents[2] / "examples" / "environments" / "compose"


def write_env_workstation(dest: Path, *, force: bool = False) -> dict[str, Any]:
    src = template_root()
    dest = dest.expanduser().resolve()
    if not src.is_dir():
        msg = f"missing template at {src}"
        return {
            "ok": False,
            "verb": "init",
            "env": True,
            "dir": str(dest),
            "written": [],
            "skipped": [],
            "error": {"code": "no_template", "message": msg},
            "text": msg,
        }

    existing = [str(rel) for rel in TEMPLATE_FILES if (dest / rel).exists()]
    if existing and not force:
        msg = "already present: " + ", ".join(existing) + " (pass --force)"
        return {
            "ok": False,
            "verb": "init",
            "env": True,
            "dir": str(dest),
            "written": [],
            "skipped": existing,
            "error": {"code": "exists", "message": msg},
            "text": msg,
        }

    dest.mkdir(parents=True, exist_ok=True)
    written: list[str] = []
    for rel in TEMPLATE_FILES:
        from_path = src / rel
        if not from_path.exists():
            continue
        to_path = dest / rel
        to_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(from_path, to_path)
        written.append(str(rel))

    if not written:
        msg = f"template empty at {src}"
        return {
            "ok": False,
            "verb": "init",
            "env": True,
            "dir": str(dest),
            "written": [],
            "skipped": [],
            "error": {"code": "no_template", "message": msg},
            "text": msg,
        }

    text = (
        f"wrote env workstation in {dest}: {', '.join(written)}. "
        "next: kraken up --file compose.yaml"
    )
    return {
        "ok": True,
        "verb": "init",
        "env": True,
        "dir": str(dest),
        "written": written,
        "skipped": [],
        "next": "kraken up --file compose.yaml",
        "error": None,
        "text": text,
    }
