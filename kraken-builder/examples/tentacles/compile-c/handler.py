#!/usr/bin/env python3
"""Plan a C compile, dry-run without Docker, finish after suckers patch."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

#: compile-c shells out to `runtime`, which shells out to Docker. Its own
#: manifest declares timeout_sec: 180 so core allows the delegation to finish;
#: the inner deadline stays under that so a slow inner call still reports its
#: own error instead of being killed by core with no message at all.
DELEGATE_TIMEOUT_SEC = 150


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0

def _delegate(req: dict, arm: str, action: str, payload: dict, net: dict | None = None) -> int:
    """Run another tentacle as a subprocess and relay its answer.

    A missing arm, a non-zero exit, or unparseable output are all answered as
    "ok": false with exit 0 -- an application failure with a usable message,
    never a transport failure that hides the reason.
    """
    import os
    import subprocess

    env = dict(os.environ)
    here = Path(__file__).resolve().parent
    # Find a kraken runner: the checkout this example lives in, if any.
    for base in (here.parents[3], here.parents[2], ROOT.parent):
        if (base / "kraken" / "core" / "cli.py").exists():
            env["PYTHONPATH"] = str(base) + os.pathsep + env.get("PYTHONPATH", "")
            break

    cmd = [sys.executable, "-m", "kraken", "run", arm, action,
           "--payload", json.dumps(payload)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=DELEGATE_TIMEOUT_SEC, env=env)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return _ok(req, {"error": f"cannot run {arm}: {exc}"}, ok=False)

    line = next((ln for ln in reversed(proc.stdout.splitlines()) if ln.startswith("{")), None)
    if line is None:
        detail = (proc.stderr or proc.stdout).strip()[-300:]
        return _ok(
            req,
            {
                "error": f"{arm} {action} produced no JSON (exit {proc.returncode})",
                "detail": detail,
                "hint": f"kraken tentacle add examples/tentacles/{arm}",
            },
            ok=False,
        )
    try:
        out = json.loads(line)
    except json.JSONDecodeError as exc:
        return _ok(req, {"error": f"{arm} {action} wrote invalid JSON: {exc}"}, ok=False)

    result = out.get("result") or {}
    if not isinstance(result, dict):
        result = {"value": result}
    if net is not None:
        result["docker"] = net
    if out.get("ok") is False:
        return _ok(req, result or {"error": f"{arm} {action} failed"}, ok=False)
    return _ok(req, result)


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
        # Shell out to the runner rather than importing it.
        # docs/CONTRACT.md: "It must not depend on kraken-core source." This
        # imported kraken.core.runner and called run_named() in-process, which
        # broke twice over -- `parents[3]` resolves against wherever the
        # tentacle happens to be installed, so `runtime` was looked up under the
        # wrong root, and an unresolved arm escaped as a traceback and exit 1
        # instead of a v1 answer.
        return _delegate(req, "runtime", action, {
            "dockerfile": dockerfile,
            "image": image,
            "network": net["name"],
            "inner": inner,
            **p,
        }, net)

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
