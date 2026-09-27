#!/usr/bin/env python3
"""Local notes. Files mode 0600. No network."""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path


def _root() -> Path:
    base = Path(os.environ.get("KRAKEN_HOME", str(Path.home())))
    d = base / ".kraken" / "data" / "notes"
    d.mkdir(parents=True, exist_ok=True)
    try:
        d.chmod(0o700)
    except OSError:
        pass
    return d


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _safe(name: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", name).strip("-") or "note"


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "list"
    p = req.get("payload") or {}
    root = _root()

    if action == "list":
        rows = sorted(p.stem for p in root.glob("*.md"))
        return _ok(req, {"notes": rows, "dir": str(root)})

    if action == "put":
        name = _safe(str(p.get("name") or "untitled"))
        path = root / f"{name}.md"
        path.write_text(str(p.get("body") or ""))
        try:
            path.chmod(0o600)
        except OSError:
            pass
        return _ok(req, {"name": name, "path": str(path)})

    if action == "get":
        name = _safe(str(p.get("name") or ""))
        path = root / f"{name}.md"
        if not path.exists():
            return _ok(req, {"error": "missing"}, ok=False)
        return _ok(req, {"name": name, "body": path.read_text()})

    if action == "search":
        q = str(p.get("q") or "").lower()
        hits = []
        for path in root.glob("*.md"):
            text = path.read_text()
            if q in path.stem.lower() or q in text.lower():
                hits.append(path.stem)
        return _ok(req, {"q": q, "hits": hits})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
