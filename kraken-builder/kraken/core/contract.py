"""Language-agnostic tentacle contract: JSON request in, JSON response out."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
KINDS = ("json", "text", "file", "media", "params")

# The directory that makes `import kraken` work from a checkout. Tentacle
# handlers (compile-c, runtime, docker-env, billing-log) import core modules,
# so a spawned handler needs this on its path even though the CLI that
# spawned it is already running from there.
_ROOT = Path(__file__).resolve().parent.parent.parent


def envelope(kind: str, value: Any, **meta: Any) -> dict[str, Any]:
    if kind not in KINDS:
        kind = "json"
    return {"kind": kind, "value": value, "meta": meta}


def unwrap(payload: Any) -> dict[str, Any]:
    if isinstance(payload, dict) and payload.get("kind") in KINDS:
        return {
            "kind": payload["kind"],
            "value": payload.get("value"),
            "meta": payload.get("meta") or {},
        }
    return {"kind": "json", "value": payload, "meta": {}}


def encode_request(
    action: str, payload: dict[str, Any] | None = None, req_id: str = "1"
) -> bytes:
    body = {
        "v": PROTOCOL_VERSION,
        "id": req_id,
        "op": "invoke",
        "action": action,
        "payload": payload or {},
    }
    return json.dumps(body).encode("utf-8")


def decode_response(raw: bytes) -> dict[str, Any]:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("tentacle response must be a JSON object")
    return data


def _argv(binary: Path) -> list[str]:
    ext = binary.suffix
    if not ext and binary.name.startswith("."):
        ext = binary.name
    if ext == ".py":
        return [sys.executable, str(binary)]
    if ext == ".sh":
        return ["bash", str(binary)]
    if ext in {".js", ".mjs"}:
        return ["node", str(binary)]
    if ext in {".applescript", ".scpt"}:
        return ["osascript", str(binary)]
    if ext == ".php":
        return ["php", str(binary)]
    if ext == ".rb":
        return ["ruby", str(binary)]
    if ext == ".pl":
        return ["perl", str(binary)]
    if ext == ".go":
        return ["go", "run", str(binary)]
    return [str(binary)]


def _subprocess_env() -> dict[str, str] | None:
    """Env for a handler subprocess. None means "inherit" -- the child gets
    os.environ as-is, which is correct once the kraken root is already
    importable and costs neither an environ copy nor an env rebuild at exec.

    The prepend path runs when a handler would otherwise fail with
    ModuleNotFoundError: `kraken run compile-c` from a bare checkout.
    """
    existing = os.environ.get("PYTHONPATH") or ""
    if str(_ROOT) in existing.split(os.pathsep):
        return None
    parts = [str(_ROOT)] + ([existing] if existing else [])
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def invoke_binary(
    binary: Path,
    action: str,
    payload: dict[str, Any] | None = None,
    timeout: int = 30,
    req_id: str = "1",
) -> dict[str, Any]:
    proc = subprocess.run(
        _argv(binary),
        input=encode_request(action, payload, req_id),
        capture_output=True,
        timeout=timeout,
        check=False,
        env=_subprocess_env(),
    )
    if proc.returncode != 0:
        if not binary.is_file():
            raise FileNotFoundError(f"tentacle binary not found: {binary}")
        if not os.access(binary, os.R_OK):
            raise PermissionError(f"tentacle binary is not readable: {binary}")
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            f"{binary} exited {proc.returncode} on action {action!r}: "
            f"{err or 'no stderr'}"
        )
    return decode_response(proc.stdout)
