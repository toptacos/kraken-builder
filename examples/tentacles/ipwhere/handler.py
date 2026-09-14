#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    ip = (req.get("payload") or {}).get("ip") or "1.1.1.1"
    result = {"ip": ip, "source": "fixture", "city": None}
    if os.environ.get("KRAKEN_OFFLINE") != "1":
        try:
            with urllib.request.urlopen(f"http://ip-api.com/json/{ip}", timeout=6) as resp:
                result = json.loads(resp.read().decode())
                result["source"] = "ip-api"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)[:200]
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
