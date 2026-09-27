#!/usr/bin/env python3
import json
import sys


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    payload = req.get("payload") or {}
    zip_code = payload.get("zip", "00000")
    sys.stdout.write(
        json.dumps(
            {
                "v": 1,
                "id": req.get("id"),
                "ok": True,
                "result": {
                    "arm": "weather-pro",
                    "action": req.get("action"),
                    "zip": zip_code,
                    "demo": True,
                    "deps": payload.get("_deps"),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
