#!/usr/bin/env python3
"""Premium fleet plan. Does not open tunnels unless grant + license exist."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


API = os.environ.get("KRAKEN_API_BASE", "https://api.topta.co")


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _home() -> Path:
    return Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken"


def _allow() -> dict:
    path = _home() / "config.yaml"
    text = path.read_text() if path.exists() else ""
    flags = {"tunnel": False, "remote_config": False, "scourge": False}
    for key in flags:
        if f"{key}: true" in text or f"{key}: true" in text.replace("yes", "true"):
            flags[key] = True
        if f"allow_{key}: true" in text:
            flags[key] = True
    return flags


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "status"
    p = req.get("payload") or {}
    allow = _allow()
    if action == "status":
        return _ok(
            req,
            {
                "premium": True,
                "login": f"{API.replace('api.','kraken.')}/account.html"
                if "api." in API
                else "https://kraken.topta.co/account.html",
                "allow": allow,
                "devices_url": f"{API.rstrip('/')}/api/kraken/devices",
            },
        )
    if action == "login-plan":
        return _ok(
            req,
            {
                "browser": "https://kraken.topta.co/account.html",
                "cli": "kraken account login you@example.com && kraken license set scourge KEY",
            },
        )
    if action == "devices":
        if not allow.get("scourge"):
            return _ok(req, {"error": "grant scourge first: kraken grant scourge", "allow": allow}, ok=False)
        return _ok(req, {"devices": [], "note": "list filled after api.topta.co session"})
    if action == "share-plan":
        if not allow.get("remote_config"):
            return _ok(req, {"error": "grant remote_config first", "allow": allow}, ok=False)
        return _ok(
            req,
            {
                "bind": "127.0.0.1",
                "via": "tunnel tentacle + group key",
                "payload_keys": ["path", "hash"],
                "no_raw_secrets": True,
            },
        )
    return _ok(req, {"error": f"unknown {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
