#!/usr/bin/env python3
import json
import sys


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    payload = req.get("payload") or {}
    raw = payload.get("result") or {}
    inner = raw.get("result") if isinstance(raw.get("result"), dict) else raw
    patch = {
        "toolchain": "c",
        "compiled": True,
        "hello": inner.get("hello") or inner.get("result", {}).get("hello"),
    }
    sys.stdout.write(
        json.dumps(
            {"v": 1, "id": req.get("id"), "ok": True, "result": {"patch": patch}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
