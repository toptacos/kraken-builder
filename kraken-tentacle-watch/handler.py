#!/usr/bin/env python3
"""Fallback watch tentacle. Same contract as the Go binary. No kraken.core import."""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path


def home() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    return Path(raw) if raw else Path.home()


def data_dir() -> Path:
    d = home() / ".kraken" / "data" / "watch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def ok(req: dict, result: dict, success: bool = True, error: dict | None = None) -> int:
    body: dict = {"v": 1, "id": req.get("id"), "ok": success}
    if success:
        body["result"] = result
    else:
        body["error"] = error or {"code": "error", "message": "failed"}
    sys.stdout.write(json.dumps(body))
    return 0


def fixture_browse(url: str) -> dict:
    title = "Kraken CLI · One binary. Many tentacles."
    raw = f"{url}|{title}".encode()
    return {
        "arm": "watch",
        "engine": "fixture",
        "url": url,
        "status": 200,
        "title": title,
        "hash": hashlib.sha256(raw).hexdigest(),
        "ok": True,
        "live": False,
        "note": "Python fallback. Build the Go binary with ./build.sh for the full watcher.",
    }


def main() -> int:
    raw = sys.stdin.read()
    try:
        req = json.loads(raw or "{}")
        if not isinstance(req, dict):
            raise ValueError("request must be an object")
    except (json.JSONDecodeError, ValueError) as exc:
        # The envelope is the contract: never let bad stdin raise.
        return ok(
            {"id": None},
            {},
            success=False,
            error={"code": "bad_json", "message": str(exc)[:200]},
        )
    action = req.get("action") or "ping"
    p = req.get("payload") or {}
    name = str(p.get("name") or "default")
    live = os.environ.get("KRAKEN_WATCH_LIVE") == "1" or p.get("live") is True

    if action == "ping":
        return ok(
            req,
            {
                "arm": "watch",
                "version": "0.1.0",
                "action": "ping",
                "platform": f"{sys.platform}-{platform.machine()}",
                "engine": "python-fallback",
                "protocol": 1,
            },
        )
    if action == "plan":
        return ok(
            req,
            {
                "arm": "watch",
                "mode": "plan",
                "engine": "python-fallback",
                "config_path": str(data_dir() / f"{name}.json"),
                "hint": "./build.sh && kraken tentacle add .",
            },
        )
    if action == "build":
        script = Path(__file__).resolve().parent / "build.sh"
        if script.exists() and shutil.which("bash") and shutil.which("go"):
            proc = subprocess.run(
                ["bash", str(script), "--host"], capture_output=True, text=True
            )
            return ok(
                req,
                {
                    "arm": "watch",
                    "mode": "build",
                    "ok": proc.returncode == 0,
                    "stdout": (proc.stdout or "")[-2000:],
                    "stderr": (proc.stderr or "")[-500:],
                },
            )
        return ok(req, {"arm": "watch", "mode": "dry-run", "argv": ["./build.sh"]})
    if action == "browse":
        return ok(req, fixture_browse(str(p.get("url") or "https://kraken.topta.co")))
    if action == "capture":
        path = data_dir() / "media"
        path.mkdir(exist_ok=True)
        dest = path / "fixture.txt"
        dest.write_text("python fallback fixture\n", encoding="utf-8")
        return ok(
            req,
            {
                "arm": "watch",
                "engine": "fixture",
                "kind": "screenshot",
                "path": str(dest),
                "hash": hashlib.sha256(dest.read_bytes()).hexdigest(),
                "ok": True,
                "live": live,
            },
        )
    if action == "notify":
        return ok(
            req,
            {
                "arm": "watch",
                "notify": [{"channel": "stdout", "ok": True}],
                "summary": p.get("summary") or "manual notify",
            },
        )
    if action == "snapshot":
        return ok(
            req,
            {
                "arm": "watch",
                "snapshot": {
                    "hostname": platform.node(),
                    "os": platform.system().lower(),
                    "arch": platform.machine(),
                },
            },
        )
    if action == "finish":
        raw = p.get("raw") if isinstance(p.get("raw"), dict) else {}
        patch = p.get("patch") if isinstance(p.get("patch"), dict) else {}
        merged = {**raw, **patch, "arm": "watch", "finished": True}
        return ok(req, merged)
    if action in {
        "tick",
        "status",
        "apply",
        "start",
        "stop",
        "list",
        "add",
        "remove",
        "task",
        "clear",
    }:
        state_path = data_dir() / f"{name}.state.json"
        state = {}
        if state_path.exists():
            try:
                state = json.loads(state_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                state = {}
        if action == "clear":
            if state_path.exists():
                state_path.unlink()
            return ok(req, {"cleared": name})
        state.update(
            {
                "name": name,
                "engine": "python-fallback",
                "last": time.time(),
                "action": action,
            }
        )
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return ok(req, {"arm": "watch", "action": action, "state": state, "live": live})
    return ok(
        req, {}, success=False, error={"code": "unknown_action", "message": action}
    )


if __name__ == "__main__":
    raise SystemExit(main())
