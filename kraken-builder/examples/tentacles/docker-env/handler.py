#!/usr/bin/env python3
"""Docker environment tentacle. Dry-runs when docker is missing."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from typing import Any

# Arms must not import core — the contract is JSON in, JSON out. A hardcoded
# core version here would silently rot, so this example names no version.
USER_AGENT = "kraken-cli/example-arm"


DEFAULT: dict[str, Any] = {
    "enabled": False,
    "name": "kraken_dev",
    "public": False,
    "isolated": False,
    "provider": "local",
    "config_url": "",
}


def _normalize_name(name: str) -> str:
    text = str(name or "dev").strip() or "dev"
    return text if text.startswith("kraken_") else f"kraken_{text}"


def _fetch(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", "replace")
    if url.endswith((".yaml", ".yml")) or text.lstrip().startswith(("---", "enabled:", "name:")):
        import yaml

        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    return data if isinstance(data, dict) else {}


def resolve_docker(payload: dict[str, Any] | None = None, root=None) -> dict[str, Any]:
    """Merge config.yaml docker.*, env, payload, then optional URL. Fail closed on fetch error."""
    try:
        from kraken.core.config import load_config

        cfg = load_config(root).get("docker") or {}
    except Exception:
        cfg = {}
    out = dict(DEFAULT)
    for key in DEFAULT:
        if key in cfg:
            out[key] = cfg[key]
    env_net = os.environ.get("KRAKEN_DOCKER_NETWORK")
    env_url = os.environ.get("KRAKEN_DOCKER_CONFIG_URL")
    if env_net:
        out["enabled"] = True
        out["name"] = _normalize_name(env_net)
    if env_url:
        out["config_url"] = env_url
        out["provider"] = "url"
    p = payload or {}
    if p.get("network"):
        out["name"] = _normalize_name(str(p["network"]))
        out["enabled"] = True
    if "public" in p:
        out["public"] = bool(p["public"])
    if "isolated" in p:
        out["isolated"] = bool(p["isolated"])
    if p.get("config_url"):
        out["config_url"] = str(p["config_url"])
        out["provider"] = "url"
    if p.get("enabled") is False:
        out["enabled"] = False
    url = str(out.get("config_url") or "")
    if url and out.get("provider") == "url":
        try:
            remote = _fetch(url)
            for key in ("enabled", "name", "public", "isolated", "provider"):
                if key in remote:
                    out[key] = remote[key]
            if remote.get("name"):
                out["name"] = _normalize_name(str(remote["name"]))
            out["source"] = url
        except Exception as exc:
            out["fetch_error"] = str(exc)[:300]
            out["source"] = url
    out["name"] = _normalize_name(str(out.get("name") or "dev"))
    out["enabled"] = bool(out.get("enabled"))
    out["public"] = bool(out.get("public"))
    out["isolated"] = bool(out.get("isolated"))
    return out


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


def _compose_yaml(
    name: str, services: list, public: bool = False, isolated: bool = False
) -> str:
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
                lines.append(f'      {k}: "{v}"')
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

    net = resolve_docker(p)
    name = str(
        p.get("name")
        or (net["name"].removeprefix("kraken_") if net.get("name") else "dev")
    )
    services = list(
        p.get("services")
        or [{"name": "redis", "image": "redis:7-alpine", "ports": ["6379:6379"]}]
    )
    public = bool(p["public"]) if "public" in p else bool(net.get("public"))
    isolated = bool(p["isolated"]) if "isolated" in p else bool(net.get("isolated"))
    root = Path(p.get("dir") or (_home() / name))
    root.mkdir(parents=True, exist_ok=True)
    compose_path = root / "docker-compose.yml"
    yaml_text = _compose_yaml(name, services, public=public, isolated=isolated)
    compose_path.write_text(yaml_text)
    state_path = root / "state.json"

    if action == "plan":
        return _ok(
            req,
            {
                "name": name,
                "compose": str(compose_path),
                "yaml": yaml_text,
                "mode": "plan",
                "docker": net,
            },
        )

    if action == "up":
        code, out = _run_docker(["compose", "up", "-d"], root)
        mode = "docker" if code == 0 else "dry-run"
        state = {"name": name, "mode": mode, "up": code == 0, "log": out[-2000:]}
        state_path.write_text(json.dumps(state, indent=2))
        return _ok(req, {**state, "compose": str(compose_path), "yaml": yaml_text})

    if action == "status":
        code, out = _run_docker(["compose", "ps"], root)
        saved = json.loads(state_path.read_text()) if state_path.exists() else {}
        return _ok(
            req,
            {
                "name": name,
                "docker": bool(_docker()),
                "ps": out[-2000:],
                "saved": saved,
            },
        )

    if action == "share":
        ports = []
        for svc in services:
            for pval in svc.get("ports") or []:
                ports.append(
                    {"service": svc.get("name"), "publish": _bind_port(pval, public)}
                )
        spec = {
            "kind": "kraken.docker-share.v1",
            "env": name,
            "network": f"kraken_{name}",
            "compose": str(compose_path),
            "ports": ports,
            "bind": "127.0.0.1" if not public else "0.0.0.0",
            "isolated": isolated,
            "join": f"docker network connect kraken_{name} <container>",
            "docker": net,
            "optional": not net.get("enabled"),
        }
        (root / "share.json").write_text(json.dumps(spec, indent=2))
        return _ok(req, spec)

    if action == "down":
        code, out = _run_docker(["compose", "down"], root)
        return _ok(req, {"name": name, "stopped": code == 0, "log": out[-1000:]})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())