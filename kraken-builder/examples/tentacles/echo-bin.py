#!/usr/bin/env python3
"""External tentacle fixture. Speaks the JSON stdin/stdout contract."""

import json
import sys


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    sys.stdout.write(
        json.dumps(
            {
                "v": 1,
                "id": req.get("id"),
                "ok": True,
                "result": {
                    "arm": "echo-bin",
                    "action": req.get("action"),
                    "echo": req.get("payload"),
                },
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
