#!/usr/bin/env python3
"""Plan a C compile, dry-run without Docker, finish after suckers patch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    from kraken.core.network import resolve_docker

    net = resolve_docker(p)
    dockerfile = str(
        p.get("dockerfile") or (ROOT.parent / "hello-world" / "c" / "Dockerfile")
    )
    image = str(p.get("image") or "kraken-hello-c:local")
    inner = p.get("inner") or {"name": "kraken"}

    if action == "finish":
        raw = p.get("result") or p.get("raw") or {}
        inner_res = raw.get("result") if isinstance(raw.get("result"), dict) else raw
        patch = p.get("patch") or {}
        merged = {**inner_res, **patch, "finished": True}
        return _ok(req, merged)

    if action == "plan":
        return _ok(
            req,
            {
                "dockerfile": dockerfile,
                "image": image,
                "network": net["name"],
                "docker": net,
                "needs_docker": True,
                "inner": inner,
                "next": [
                    "kraken tentacle add examples/tentacles/runtime",
                    "kraken tentacle add examples/tentacles/docker-env",
                    'kraken run docker-env plan --payload \'{"name":"dev"}\'',
                    f"kraken run runtime build --payload '{json.dumps({'dockerfile': dockerfile, 'image': image})}'",
                    f"kraken run runtime invoke --payload '{json.dumps({'image': image, 'network': net['name'], 'inner': inner})}'",
                ],
            },
        )

    if action in {"build", "invoke"}:
        from kraken.core.runner import run_named
        from pathlib import Path as P

        root = P(__file__).resolve().parents[3]
        out = run_named(
            root,
            "runtime",
            action,
            {
                "dockerfile": dockerfile,
                "image": image,
                "network": net["name"],
                "inner": inner,
                **p,
            },
        )
        result = out.get("result") or out
        result["docker"] = net
        return _ok(req, result, ok=bool(out.get("ok", True)))

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
