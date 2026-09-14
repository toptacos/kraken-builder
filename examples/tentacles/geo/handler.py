#!/usr/bin/env python3
import json
import sys


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    zip_code = (req.get("payload") or {}).get("zip", "00000")
    sys.stdout.write(
        json.dumps(
            {
                "v": 1,
                "id": req.get("id"),
                "ok": True,
                "result": {"arm": "geo", "zip": zip_code, "lat": 36.12, "lon": -80.07},
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
