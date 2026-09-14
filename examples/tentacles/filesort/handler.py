#!/usr/bin/env python3
"""Duplicate + tag indexer. SQLite, no Docker."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path


CATS = {
    ".jpg": "image", ".png": "image", ".webp": "image",
    ".mp4": "video", ".mov": "video",
    ".mp3": "audio",
    ".py": "code", ".js": "code", ".go": "code", ".rs": "code",
    ".md": "docs", ".txt": "docs", ".pdf": "docs",
}


def _db() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    d = base / ".kraken" / "data" / "filesort"
    d.mkdir(parents=True, exist_ok=True)
    return d / "index.sqlite"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(_db())
    c.execute(
        "CREATE TABLE IF NOT EXISTS files (path TEXT PRIMARY KEY, sha256 TEXT, bytes INTEGER, ext TEXT, category TEXT)"
    )
    return c


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "scan"
    p = req.get("payload") or {}
    root = Path(p.get("path") or ".").resolve()
    cx = _conn()

    if action == "scan":
        n = 0
        for f in root.rglob("*"):
            if not f.is_file() or f.name.startswith("."):
                continue
            digest = hashlib.sha256(f.read_bytes()).hexdigest()
            ext = f.suffix.lower()
            cx.execute(
                "INSERT OR REPLACE INTO files VALUES (?,?,?,?,?)",
                (str(f), digest, f.stat().st_size, ext, CATS.get(ext, "other")),
            )
            n += 1
        cx.commit()
        cats = {r[0]: r[1] for r in cx.execute("SELECT category, COUNT(*) FROM files GROUP BY category")}
        return _ok(req, {"indexed": n, "db": str(_db()), "categories": cats})

    if action == "dups":
        groups: dict[str, list] = defaultdict(list)
        for path, sha in cx.execute("SELECT path, sha256 FROM files"):
            groups[sha].append(path)
        dups = [{"sha256": k, "paths": v} for k, v in groups.items() if len(v) > 1]
        return _ok(req, {"duplicates": dups, "count": len(dups)})

    if action == "tag":
        rows = [{"path": a, "ext": b, "category": c} for a, b, c in cx.execute("SELECT path, ext, category FROM files")]
        return _ok(req, {"files": rows, "count": len(rows)})

    return _ok(req, {"error": action}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
