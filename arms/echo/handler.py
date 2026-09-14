def handle(action: str, payload: dict | None = None, manifest=None) -> dict:
    body = payload or {}
    if action == "ping":
        return {"ok": True, "pong": True, "echo": body}
    return {"ok": True, "echo": body, "action": action}
