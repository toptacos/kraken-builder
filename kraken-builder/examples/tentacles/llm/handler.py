#!/usr/bin/env python3
"""Plan an optional local LLM. Does not pull weights in tests."""
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
    home = Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken"
    image = str(p.get("image") or "kraken-llm:local")
    if image.endswith(":latest"):
        image = image.rsplit(":", 1)[0] + ":local"
    network = str(p.get("network") or "kraken_llm")
    if not network.startswith("kraken_"):
        network = "kraken_llm"
    ingest = list(p.get("ingest") or ["notes", "media", "backups"])
    mounts = []
    for name in ingest:
        src = home / "data" / name
        src.mkdir(parents=True, exist_ok=True)
        mounts.append(f"{src}:/ingest/{name}:ro")
    argv = [
        "docker", "run", "--rm",
        "--network", network,
        "--security-opt", "no-new-privileges",
        "-p", "127.0.0.1:11434:11434",
    ]
    for m in mounts:
        argv += ["-v", m]
    argv += [image]
    plan = {
        "enabled": bool(p.get("enabled")),
        "image": image,
        "network": network,
        "bind": "127.0.0.1:11434",
        "mounts": mounts,
        "argv": argv,
        "docker": bool(shutil.which("docker")),
        "note": "Weights stay on disk you provide. Core never ships a model.",
    }
    if action in {"plan", "status"}:
        return _ok(req, plan)
    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
