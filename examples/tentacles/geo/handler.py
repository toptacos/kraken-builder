#!/usr/bin/env python3
import json
import sys

CITIES = {
    "1.1.1.1": {"city": "Los Angeles", "lat": 34.05, "lon": -118.24},
    "1.0.0.1": {"city": "Los Angeles", "lat": 34.05, "lon": -118.24},
    "8.8.8.8": {"city": "Mountain View", "lat": 37.39, "lon": -122.08},
}


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    payload = req.get("payload") or {}
    zip_code = str(payload.get("zip") or "00000")
    ip = str(payload.get("ip") or "")
    geo = CITIES.get(ip, {"city": "Kernersville", "lat": 36.12, "lon": -80.07})
    result = {
        "arm": "geo",
        "zip": zip_code,
        "city": geo["city"],
        "lat": geo["lat"],
        "lon": geo["lon"],
    }
    if ip:
        result["ip"] = ip
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": True, "result": result})
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
