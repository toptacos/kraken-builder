"""Language-agnostic tentacle contract: JSON request in, JSON response out."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = 1
KINDS = ("json", "text", "file", "media", "params")


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


def invoke_binary(
    binary: Path, action: str, payload: dict[str, Any] | None = None, timeout: int = 30
) -> dict[str, Any]:
    proc = subprocess.run(
        _argv(binary),
        input=encode_request(action, payload),
        capture_output=True,
        timeout=timeout,
        check=False,
    )
    if proc.returncode != 0:
        err = proc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"{binary} exited {proc.returncode}: {err or 'no stderr'}")
    return decode_response(proc.stdout)
