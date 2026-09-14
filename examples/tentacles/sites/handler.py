#!/usr/bin/env python3
"""Local dev sites from .kraken/config.yaml. Docker only when action is up."""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _load(project: Path) -> dict:
    for name in ("config.yaml", "config.yml", "config.json"):
        p = project / ".kraken" / name
        if p.exists():
            text = p.read_text()
            if name.endswith(".json"):
                return json.loads(text)
            if yaml:
                return yaml.safe_load(text) or {}
            return {}
    return {}


def _compose(sites: list) -> str:
    lines = ["services:"]
    for i, site in enumerate(sites):
        name = str(site.get("name") or f"site{i}")
        image = str(site.get("image") or "nginx:alpine")
        uri = str(site.get("uri") or f"http://127.0.0.1:{8080 + i}")
        port = uri.rsplit(":", 1)[-1].split("/")[0]
        if not port.isdigit():
            port = str(8080 + i)
        root = site.get("root") or "./"
        lines += [
            f"  {name}:",
            f"    image: {image}",
            f"    container_name: kraken_site_{name}",
            f"    ports:",
            f'      - "127.0.0.1:{port}:80"',
            f"    volumes:",
            f"      - {root}:/usr/share/nginx/html:ro",
            f"    networks: [kraken_sites]",
            f"    labels:",
            f"      kraken.tentacle: sites",
            f"      kraken.uri: {uri}",
        ]
    lines += [
        "networks:",
        "  kraken_sites:",
        "    name: kraken_sites",
        "    internal: false",
        "    labels:",
        "      kraken.tentacle: sites",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    project = Path(p.get("project") or ".").resolve()
    cfg = _load(project)
    sites = list((cfg.get("sites") or p.get("sites") or []))
    if not sites:
        sites = [{"name": "app", "uri": "http://127.0.0.1:8080", "root": str(project)}]
    yaml_text = _compose(sites)

    if action == "list":
        return _ok(req, {"project": str(project), "sites": sites})

    if action == "plan":
        out = project / ".kraken" / "sites-compose.yml"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(yaml_text)
        return _ok(req, {"compose": str(out), "yaml": yaml_text, "count": len(sites), "needs_docker": False})

    if action == "up":
        return _ok(
            req,
            {
                "mode": "dry-run",
                "hint": "docker compose -f .kraken/sites-compose.yml up -d",
                "network": "kraken_sites",
                "yaml": yaml_text,
                "needs_docker": True,
            },
        )

    return _ok(req, {"error": action}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
