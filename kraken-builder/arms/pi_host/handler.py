import platform
import sys


def handle(action: str, payload: dict | None = None, manifest=None) -> dict:
    body = payload or {}
    if action == "status":
        return {
            "ok": True,
            "arm": "pi-host",
            "system": {
                "platform": platform.platform(),
                "python": sys.version.split()[0],
                "machine": platform.machine(),
            },
        }
    if action == "discover":
        return {"ok": True, "arm": "pi-host", "hosts": []}
    if action == "add":
        host = body.get("host", "")
        return {"ok": True, "arm": "pi-host", "added": host}
    return {"ok": True, "arm": "pi-host", "action": action}