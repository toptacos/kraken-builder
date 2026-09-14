#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request

FEED = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    result = {"source": "fixture", "count": 0, "titles": []}
    if os.environ.get("KRAKEN_OFFLINE") != "1":
        try:
            with urllib.request.urlopen(FEED, timeout=8) as resp:
                data = json.loads(resp.read().decode())
            feats = data.get("features") or []
            result = {
                "source": "usgs",
                "count": len(feats),
                "titles": [f.get("properties", {}).get("title") for f in feats[:5]],
            }
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            result["error"] = str(exc)[:200]
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
