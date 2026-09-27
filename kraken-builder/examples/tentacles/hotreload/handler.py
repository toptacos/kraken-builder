#!/usr/bin/env python3
"""Hot-reload tentacle. One tick per invoke so tests stay deterministic."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


def _state_dir() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    d = base / ".kraken" / "data" / "hotreload"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _hash_tree(root: Path, patterns: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    if not root.exists():
        return files
    suffixes = tuple(p.replace("*", "") for p in patterns if p.startswith("*."))
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if suffixes and not path.name.endswith(suffixes):
            continue
        if path.name.startswith("."):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        files[str(path.relative_to(root))] = digest
    return files


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "status"
    p = req.get("payload") or {}
    name = str(p.get("name") or "dev")
    state_path = _state_dir() / f"{name}.json"

    if action == "clear":
        if state_path.exists():
            state_path.unlink()
        return _ok(req, {"cleared": name})

    if action == "watch":
        root = Path(p.get("root") or ".").resolve()
        patterns = list(p.get("patterns") or ["*.py", "*.js", "*.go"])
        command = p.get("command") or ["true"]
        if isinstance(command, str):
            command = ["bash", "-lc", command]
        hashes = _hash_tree(root, patterns)
        state = {
            "name": name,
            "root": str(root),
            "patterns": patterns,
            "command": command,
            "hashes": hashes,
            "fires": 0,
            "last_changed": [],
        }
        state_path.write_text(json.dumps(state, indent=2))
        return _ok(req, {"watching": str(root), "files": len(hashes), "command": command})

    if not state_path.exists():
        return _ok(req, {"error": "call watch first"}, ok=False)

    state = json.loads(state_path.read_text())
    if action == "status":
        return _ok(req, {k: state[k] for k in state if k != "hashes"} | {"files": len(state.get("hashes") or {})})

    if action == "tick":
        root = Path(state["root"])
        current = _hash_tree(root, state["patterns"])
        old = state.get("hashes") or {}
        changed = sorted(set(current) | set(old))
        changed = [f for f in changed if current.get(f) != old.get(f)]
        ran = False
        output = ""
        if changed:
            cmd = list(state["command"])
            proc = subprocess.run(cmd, cwd=root, capture_output=True, text=True)
            ran = True
            output = ((proc.stdout or "") + (proc.stderr or ""))[-2000:]
            state["fires"] = int(state.get("fires") or 0) + 1
            state["last_exit"] = proc.returncode
        state["hashes"] = current
        state["last_changed"] = changed
        state_path.write_text(json.dumps(state, indent=2))
        return _ok(
            req,
            {
                "changed": changed,
                "ran": ran,
                "fires": state["fires"],
                "output": output,
                "files": len(current),
            },
        )

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
