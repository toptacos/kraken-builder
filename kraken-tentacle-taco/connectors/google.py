"""Google Cloud Pub/Sub or Cloud Build envelope → taco. No GCP SDK."""


def parse(payload: dict) -> dict | None:
    msg = payload.get("message") or payload
    data = msg.get("attributes") or {}
    user = data.get("user") or payload.get("user")
    status = data.get("status") or payload.get("status")
    if payload.get("kind") == "security" and user:
        return {"user": user, "kind": "security", "note": "google:security"}
    if status in {"SUCCESS", "SUCCESSFUL"} and user:
        return {"user": user, "kind": "custom", "tacos": 2, "note": "google:build"}
    return None
