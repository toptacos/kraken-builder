"""User-facing permission grants. Default deny."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout, user_kraken

KNOWN = ("tunnel", "remote_config", "scourge", "llm", "expose")


def _cfg(home: Path | None = None) -> Path:
    return ensure_user_layout(home) / "config.yaml"


def read_allow(home: Path | None = None) -> dict[str, bool]:
    text = _cfg(home).read_text() if _cfg(home).exists() else ""
    out = {k: False for k in KNOWN}
    for k in KNOWN:
        if f"{k}: true" in text:
            out[k] = True
    return out


def grant(name: str, yes: bool = True, home: Path | None = None) -> dict[str, Any]:
    if name not in KNOWN:
        return {"ok": False, "error": f"unknown grant {name}", "known": list(KNOWN)}
    path = _cfg(home)
    text = path.read_text() if path.exists() else "version: 1\n"
    if "allow:\n" not in text:
        text += "\nallow:\n"
    line = f"  {name}: {'true' if yes else 'false'}\n"
    # replace existing
    import re

    if re.search(rf"  {name}: (true|false)", text):
        text = re.sub(rf"  {name}: (true|false)", line.strip(), text)
    else:
        text += line
    path.write_text(text)
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return {"ok": True, "grant": name, "allowed": yes, "config": str(path)}
