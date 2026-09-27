#!/usr/bin/env python3
import json
import sys

from kraken.billing.hooks import after_install, on_denied


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "ping"
    payload = req.get("payload") or {}
    tentacle = str(payload.get("target") or payload.get("tentacle") or "unknown")
    if action == "denied":
        result = on_denied(tentacle, str(payload.get("error") or "denied"))
    else:
        result = after_install(tentacle, payload.get("spec"))
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
