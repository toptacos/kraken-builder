#!/usr/bin/env python3
"""Plan a loopback hostname. Never binds 0.0.0.0."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def _home() -> Path:
    return Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken"


def _granted() -> bool:
    text = (
        (_home() / "config.yaml").read_text()
        if (_home() / "config.yaml").exists()
        else ""
    )
    return "expose: true" in text


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    if not _granted():
        return _ok(req, {"error": "grant expose first: kraken grant expose"}, ok=False)
    host = str(p.get("host") or "panel.kraken.localhost")
    if not host.endswith(".kraken.localhost") and host != "kraken.localhost":
        host = "panel.kraken.localhost"
    port = int(p.get("port") or 18181)
    bind = f"127.0.0.1:{port}"
    plan = {
        "host": host,
        "bind": bind,
        "public": False,
        "argv": ["python3", "-m", "http.server", "--bind", "127.0.0.1", str(port)],
        "note": "Loopback only. Pair with ca for HTTPS. Not 0.0.0.0.",
    }
    if "0.0.0.0" in bind:
        return _ok(req, {"error": "refusing 0.0.0.0"}, ok=False)
    if action in {"plan", "status"}:
        return _ok(req, plan)
    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
