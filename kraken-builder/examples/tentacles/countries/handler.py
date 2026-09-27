#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    name = str((req.get("payload") or {}).get("name") or "united states")
    result = {"source": "fixture", "name": name, "capital": ["Washington, D.C."]}
    if os.environ.get("KRAKEN_OFFLINE") != "1":
        q = urllib.parse.quote(name)
        url = f"https://restcountries.com/v3.1/name/{q}?fields=name,capital,population,cca2"
        try:
            with urllib.request.urlopen(url, timeout=8) as resp:
                rows = json.loads(resp.read().decode())
            row = rows[0] if rows else {}
            result = {
                "source": "restcountries",
                "name": (row.get("name") or {}).get("common"),
                "capital": row.get("capital"),
                "population": row.get("population"),
                "cca2": row.get("cca2"),
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)[:200]
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
