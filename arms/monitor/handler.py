import json
import platform
import sys
from pathlib import Path


def handle(action: str, payload: dict | None = None, manifest=None) -> dict:
    body = payload or {}
    if action == "snapshot":
        root = Path(body.get("root", ".")).resolve()
        return {
            "ok": True,
            "arm": "monitor",
            "snapshot": {
                "root": str(root),
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "cwd": str(Path.cwd()),
            },
        }
    if action == "ping":
        url = body.get("url", "")
        return {"ok": True, "arm": "monitor", "ping": {"url": url, "reachable": bool(url)}}
    return {"ok": True, "arm": "monitor", "action": action}