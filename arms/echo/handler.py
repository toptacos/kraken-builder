def handle(action: str, payload: dict | None = None, manifest=None) -> dict:
    body = payload or {}
    if action == "ping":
        return {"ok": True, "arm": "echo", "pong": True, "echo": body}
    return {"ok": True, "arm": "echo", "echo": body, "action": action}