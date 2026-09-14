#!/usr/bin/env python3
"""Docker environment tentacle. Dry-runs when docker is missing."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _home() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    return base / ".kraken" / "data" / "docker-env"


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _bind_port(raw: str, public: bool) -> str:
    text = str(raw).strip()
    if public:
        return text
    if text.startswith("127.0.0.1:") or text.startswith("localhost:"):
        return text
    if text.startswith("0.0.0.0:"):
        return "127.0.0.1:" + text.split(":", 1)[1]
    if text.count(":") == 1:
        return f"127.0.0.1:{text}"
    return f"127.0.0.1:{text}"


def _compose_yaml(name: str, services: list, public: bool = False, isolated: bool = False) -> str:
    lines = ["services:"]
    for svc in services:
        sid = str(svc.get("name") or "app")
        image = str(svc.get("image") or "alpine:3.20")
        lines.append(f"  {sid}:")
        lines.append(f"    image: {image}")
        lines.append(f"    container_name: kraken_{name}_{sid}")
        ports = svc.get("ports") or []
        if ports:
            lines.append("    ports:")
            for p in ports:
                lines.append(f'      - "{_bind_port(p, public)}"')
        env = svc.get("env") or {}
        if env:
            lines.append("    environment:")
            for k, v in env.items():
                lines.append(f"      {k}: \"{v}\"")
        lines.append(f"    networks: [kraken_{name}]")
        lines.append(f"    labels:")
        lines.append(f"      kraken.tentacle: docker-env")
        lines.append(f"      kraken.env: {name}")
    lines.append("networks:")
    lines.append(f"  kraken_{name}:")
    lines.append("    name: kraken_" + name)
    if isolated:
        lines.append("    internal: true")
    lines.append("    labels:")
    lines.append("      kraken.tentacle: docker-env")
    lines.append(f"      kraken.env: {name}")
    return "\n".join(lines) + "\n"


def _docker() -> str | None:
    return shutil.which("docker")


def _run_docker(args: list[str], cwd: Path) -> tuple[int, str]:
    exe = _docker()
    if not exe:
        return 127, "docker not installed"
    proc = subprocess.run([exe, *args], cwd=cwd, capture_output=True, text=True)
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    name = str(p.get("name") or "dev")
    services = list(p.get("services") or [{"name": "redis", "image": "redis:7-alpine", "ports": ["6379:6379"]}])
    public = bool(p.get("public"))
    isolated = bool(p.get("isolated"))
    root = Path(p.get("dir") or (_home() / name))
    root.mkdir(parents=True, exist_ok=True)
    compose_path = root / "docker-compose.yml"
    yaml_text = _compose_yaml(name, services, public=public, isolated=isolated)
    compose_path.write_text(yaml_text)
    state_path = root / "state.json"

    if action == "plan":
        return _ok(req, {"name": name, "compose": str(compose_path), "yaml": yaml_text, "mode": "plan"})

    if action == "up":
        code, out = _run_docker(["compose", "up", "-d"], root)
        mode = "docker" if code == 0 else "dry-run"
        state = {"name": name, "mode": mode, "up": code == 0, "log": out[-2000:]}
        state_path.write_text(json.dumps(state, indent=2))
        return _ok(req, {**state, "compose": str(compose_path), "yaml": yaml_text})

    if action == "status":
        code, out = _run_docker(["compose", "ps"], root)
        saved = json.loads(state_path.read_text()) if state_path.exists() else {}
        return _ok(req, {"name": name, "docker": bool(_docker()), "ps": out[-2000:], "saved": saved})

    if action == "share":
        ports = []
        for svc in services:
            for pval in svc.get("ports") or []:
                ports.append({"service": svc.get("name"), "publish": _bind_port(pval, public)})
        spec = {
            "kind": "kraken.docker-share.v1",
            "env": name,
            "network": f"kraken_{name}",
            "compose": str(compose_path),
            "ports": ports,
            "bind": "127.0.0.1" if not public else "0.0.0.0",
            "isolated": isolated,
            "join": f"docker network connect kraken_{name} <container>",
        }
        (root / "share.json").write_text(json.dumps(spec, indent=2))
        return _ok(req, spec)

    if action == "down":
        code, out = _run_docker(["compose", "down"], root)
        return _ok(req, {"name": name, "stopped": code == 0, "log": out[-1000:]})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
