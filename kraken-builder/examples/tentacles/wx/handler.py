#!/usr/bin/env python3
"""Fetch Open-Meteo, then finish a report after a sucker patches units."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def _forecast(payload: dict) -> dict:
    lat = float(payload.get("lat") or 36.8508)
    lon = float(payload.get("lon") or -76.2859)
    if os.environ.get("KRAKEN_OFFLINE") == "1":
        return {
            "source": "fixture",
            "lat": lat,
            "lon": lon,
            "temperature_c": 20.0,
            "windspeed": 8.0,
            "weathercode": 1,
        }
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}&current_weather=true"
    )
    try:
        with urllib.request.urlopen(url, timeout=6) as resp:
            data = json.loads(resp.read().decode())
        cw = data.get("current_weather") or {}
        return {
            "source": "open-meteo",
            "lat": lat,
            "lon": lon,
            "temperature_c": cw.get("temperature"),
            "windspeed": cw.get("windspeed"),
            "weathercode": cw.get("weathercode"),
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return {
            "source": "fixture",
            "lat": lat,
            "lon": lon,
            "temperature_c": 20.0,
            "error": str(exc)[:200],
        }


def _finish(payload: dict) -> dict:
    raw = payload.get("raw") if isinstance(payload.get("raw"), dict) else {}
    patch = payload.get("patch") if isinstance(payload.get("patch"), dict) else {}
    c = raw.get("temperature_c")
    f = patch.get("temperature_f")
    if f is None and isinstance(c, (int, float)):
        f = round((float(c) * 9 / 5) + 32, 1)
    return {
        "source": raw.get("source"),
        "lat": raw.get("lat"),
        "lon": raw.get("lon"),
        "temperature_c": c,
        "temperature_f": f,
        "windspeed": patch.get("windspeed", raw.get("windspeed")),
        "summary": patch.get("summary") or f"{c} C",
        "finished": True,
    }


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "forecast"
    payload = req.get("payload") or {}
    if action == "forecast":
        return _ok(req, _forecast(payload))
    if action == "finish":
        return _ok(req, _finish(payload))
    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
