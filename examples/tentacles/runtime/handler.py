#!/usr/bin/env python3
"""Lean compile/run sandbox. Core never ships a compiler."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _docker() -> str | None:
    return shutil.which("docker")


def _plan(p: dict) -> dict:
    work = Path(p.get("work") or ".").resolve()
    dockerfile = Path(p.get("dockerfile") or (work / "Dockerfile"))
    image = str(p.get("image") or "kraken-runtime:local")
    if image.endswith(":latest") and not p.get("allow_latest"):
        image = image.rsplit(":", 1)[0] + ":local"
    network = str(p.get("network") or "kraken_dev")
    if not network.startswith("kraken_"):
        network = "kraken_dev"
    services = p.get("services") or {}
    mounts = list(p.get("mounts") or [])
    write_data = bool((services.get("data") or {}).get("write") or p.get("write_data"))
    ssh_key = str((services.get("ssh") or {}).get("key") or "")
    use_ssh = bool(ssh_key) and bool(p.get("use_ssh") or (services.get("ssh") or {}).get("use"))
    defaults = {
        "data": str(Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken" / "data"),
        "store": services.get("store", {}).get("path") or "local://store",
        "vault": services.get("vault", {}).get("path") or "local://vault",
        "s3": services.get("s3", {}).get("uri") or "",
        "ssh": ssh_key if use_ssh else "",
        "upload": services.get("upload", {}).get("uri") or "",
        "write_data": write_data,
    }
    argv = [
        "docker", "run", "--rm", "-i",
        "--network", network,
        "--security-opt", "no-new-privileges",
        "-v", f"{work}:/work",
        "-w", "/work",
    ]
    data = defaults["data"]
    argv += ["-v", f"{data}:/kraken/data" + ("" if write_data else ":ro")]
    if use_ssh:
        argv += ["-v", f"{ssh_key}:/kraken/ssh/key:ro"]
    for m in mounts:
        src, dest = m.get("src"), m.get("dest", "/extra")
        if not src or ".." in str(src):
            continue
        mode = "" if m.get("ro") is False else ":ro"
        argv += ["-v", f"{src}:{dest}{mode}"]
    argv += ["-e", "KRAKEN_STORE=" + str(defaults["store"])]
    argv += ["-e", "KRAKEN_UPLOAD=" + str(defaults["upload"])]
    argv += [image]
    entry = p.get("entry") or ["cat"]  # user image should read stdin JSON
    if isinstance(entry, str):
        entry = ["sh", "-lc", entry]
    argv.extend(entry)
    return {
        "image": image,
        "dockerfile": str(dockerfile),
        "network": network,
        "argv": argv,
        "services": defaults,
        "docker": bool(_docker()),
    }


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    plan = _plan(p)

    if action == "plan":
        return _ok(req, plan)

    if action == "build":
        df = Path(plan["dockerfile"])
        if not df.exists():
            return _ok(req, {"error": f"missing Dockerfile {df}", "plan": plan}, ok=False)
        exe = _docker()
        if not exe:
            return _ok(req, {"mode": "dry-run", "would": [exe or "docker", "build", "-t", plan["image"], "-f", str(df), str(df.parent)], "plan": plan})
        proc = subprocess.run([exe, "build", "-t", plan["image"], "-f", str(df), str(df.parent)], capture_output=True, text=True)
        return _ok(req, {"mode": "docker", "code": proc.returncode, "log": (proc.stdout + proc.stderr)[-2000:], "image": plan["image"]}, ok=proc.returncode == 0)

    if action == "invoke":
        exe = _docker()
        body = json.dumps({"v": 1, "op": "invoke", "action": p.get("target_action") or "hello", "payload": p.get("inner") or {}})
        if not exe:
            return _ok(req, {"mode": "dry-run", "argv": plan["argv"], "stdin": body, "services": plan["services"]})
        proc = subprocess.run(plan["argv"], input=body, capture_output=True, text=True)
        raw = (proc.stdout or "").strip()
        parsed = None
        try:
            parsed = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            parsed = None
        return _ok(req, {"mode": "docker", "code": proc.returncode, "stdout": raw[-4000:], "parsed": parsed}, ok=proc.returncode == 0)

    if action == "publish":
        # Hand off to store/upload URI. Actual bytes live in payload.result or path.
        dest = (p.get("services") or {}).get("upload", {}).get("uri") or plan["services"].get("upload") or "local://store"
        return _ok(req, {"published": dest, "hint": "kraken run store put --payload path=… backend=s3|local", "plan": plan})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
