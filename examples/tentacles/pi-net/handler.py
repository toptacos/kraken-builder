#!/usr/bin/env python3
"""Pi discovery / management. Probe is TCP connect only; no GPIO."""
from __future__ import annotations

import json
import os
import socket
import sys
from pathlib import Path


def _data() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    d = base / ".kraken" / "data" / "pi-net"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _probe(host: str, port: int, timeout: float = 0.15) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "discover"
    p = req.get("payload") or {}
    known = _data() / "hosts.json"
    saved = json.loads(known.read_text()) if known.exists() else {"hosts": []}

    if action == "add":
        row = {
            "host": p.get("host") or p.get("ip"),
            "user": p.get("user") or "pi",
            "port": int(p.get("port") or 22),
            "key": p.get("key") or "",
        }
        if not row["host"]:
            return _ok(req, {"error": "host required"}, ok=False)
        saved["hosts"] = [h for h in saved["hosts"] if h.get("host") != row["host"]]
        saved["hosts"].append(row)
        known.write_text(json.dumps(saved, indent=2))
        return _ok(req, {"added": row["host"], "auth": "key" if row["key"] else "none"})

    if action == "discover":
        candidates = list(p.get("hosts") or [])
        if not candidates:
            candidates = [h.get("host") for h in saved.get("hosts") or [] if h.get("host")]
        if not candidates:
            candidates = ["raspberrypi.local", "127.0.0.1"]
        port = int(p.get("port") or 22)
        found = []
        for host in candidates:
            up = host in {"127.0.0.1", "localhost"} or _probe(str(host), port)
            found.append({"host": host, "port": port, "reachable": bool(up)})
        return _ok(req, {"found": found, "method": "hosts-or-saved"})

    if action == "status":
        host = p.get("host") or (saved.get("hosts") or [{}])[0].get("host")
        if not host:
            return _ok(req, {"error": "no host"}, ok=False)
        port = int(p.get("port") or 22)
        return _ok(req, {"host": host, "sshd": _probe(str(host), port) or host in {"127.0.0.1", "localhost"}})

    return _ok(req, {"error": action}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
