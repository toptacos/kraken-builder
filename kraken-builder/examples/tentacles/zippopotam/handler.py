#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    p = req.get("payload") or {}
    country = str(p.get("country") or "us")
    code = str(p.get("zip") or "27284")
    result = {"source": "fixture", "country": country, "zip": code, "places": [{"place name": "Kernersville", "state": "North Carolina"}]}
    if os.environ.get("KRAKEN_OFFLINE") != "1":
        try:
            url = f"https://api.zippopotam.us/{country}/{code}"
            with urllib.request.urlopen(url, timeout=6) as resp:
                result = json.loads(resp.read().decode())
                result["source"] = "zippopotam"
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)[:200]
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
