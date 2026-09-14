#!/usr/bin/env python3
"""Sucker: patch wx forecast units. Does not fetch. Does not re-enter."""

from __future__ import annotations

import json
import sys


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    payload = req.get("payload") or {}
    raw = payload.get("result") or {}
    inner = raw.get("result") if isinstance(raw.get("result"), dict) else raw
    c = inner.get("temperature_c")
    patch: dict = {}
    if isinstance(c, (int, float)):
        f = round((float(c) * 9 / 5) + 32, 1)
        patch["temperature_f"] = f
        patch["summary"] = f"{c} C / {f} F at {inner.get('lat')},{inner.get('lon')}"
    patch["windspeed"] = inner.get("windspeed")
    return _ok(req, {"patch": patch, "target": payload.get("target")})


if __name__ == "__main__":
    raise SystemExit(main())
