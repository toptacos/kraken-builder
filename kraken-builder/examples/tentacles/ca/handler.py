#!/usr/bin/env python3
"""Plan local TLS material. Core does not ship a CA."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def _home() -> Path:
    return Path(os.environ.get("KRAKEN_HOME", str(Path.home()))) / ".kraken"


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "plan"
    p = req.get("payload") or {}
    dest = _home() / "data" / "ca"
    dest.mkdir(parents=True, exist_ok=True)
    host = str(p.get("host") or "panel.kraken.localhost")
    cert = dest / "localhost.pem"
    key = dest / "localhost-key.pem"
    if not cert.exists():
        cert.write_text(
            "-----BEGIN CERTIFICATE-----\nPLAN-ONLY\n-----END CERTIFICATE-----\n"
        )
    if not key.exists():
        key.write_text(
            "-----BEGIN PRIVATE KEY-----\nPLAN-ONLY\n-----END PRIVATE KEY-----\n"
        )
        try:
            key.chmod(0o600)
            cert.chmod(0o600)
        except OSError:
            pass
    plan = {
        "dir": str(dest),
        "cert": str(cert),
        "key": str(key),
        "host": host,
        "public": False,
        "note": "Self-signed files for loopback. Core is not a certificate authority.",
    }
    if action in {"plan", "status"}:
        return _ok(req, plan)
    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
