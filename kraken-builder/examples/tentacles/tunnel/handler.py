#!/usr/bin/env python3
"""Describe an SSH jump you already own. Never opens a listener on 0.0.0.0."""
from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    host = str(p.get("host") or "")
    user = str(p.get("user") or os.environ.get("USER") or "user")
    key = str(p.get("key") or "")
    jump = str(p.get("jump") or "")
    if not host:
        return _ok(req, {"error": "host required"}, ok=False)
    if key and not Path(key).expanduser().exists():
        return _ok(req, {"error": "key file not found", "key": key}, ok=False)
    argv = ["ssh", "-N", "-o", "ExitOnForwardFailure=yes", "-o", "StrictHostKeyChecking=accept-new"]
    if key:
        argv += ["-i", str(Path(key).expanduser())]
    local = int(p.get("local_port") or 18080)
    remote = int(p.get("remote_port") or 22)
    argv += ["-L", f"127.0.0.1:{local}:{host}:{remote}"]
    if jump:
        argv += ["-J", jump]
    argv += [f"{user}@{host}"]
    plan = {
        "argv": argv,
        "bind": "127.0.0.1",
        "local_port": local,
        "note": "Local forward only. You must already have the key. Kraken does not store the key in the payload.",
        "ssh": bool(shutil.which("ssh")),
    }
    if action == "plan":
        return _ok(req, plan)
    if action == "status":
        return _ok(req, {**plan, "running": False, "reason": "status is advisory; core does not daemonize ssh"})
    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
