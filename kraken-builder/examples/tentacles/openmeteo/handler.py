#!/usr/bin/env python3
"""Open-Meteo — no key. Falls back to a fixture."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    p = req.get("payload") or {}
    lat = float(p.get("lat") or 36.12)
    lon = float(p.get("lon") or -80.07)
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    if os.environ.get("KRAKEN_OFFLINE") == "1":
        return _ok(req, {"source": "fixture", "lat": lat, "lon": lon, "temperature": None})
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        cw = data.get("current_weather") or {}
        return _ok(req, {"source": "open-meteo", "lat": lat, "lon": lon, "current": cw})
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return _ok(req, {"source": "fixture", "lat": lat, "lon": lon, "error": str(exc)[:200]})


if __name__ == "__main__":
    raise SystemExit(main())
