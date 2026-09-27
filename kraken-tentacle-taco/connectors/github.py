"""GitHub webhook → taco event. Expects the JSON body, not an API token."""


def parse(payload: dict) -> dict | None:
    action = payload.get("action")
    pr = payload.get("pull_request") or {}
    if pr and action in {"closed", "merged"} and (pr.get("merged") or action == "merged"):
        user = ((pr.get("user") or {}).get("login")) or payload.get("sender", {}).get("login")
        return {"user": user, "kind": "pr", "note": f"github:{pr.get('html_url') or pr.get('url')}"}
    alert = payload.get("alert") or {}
    if payload.get("action") in {"closed", "fixed"} and (alert.get("state") in {"fixed", "dismissed"} or "security" in str(payload.get("zen") or "")):
        user = (payload.get("sender") or {}).get("login")
        if user:
            return {"user": user, "kind": "security", "note": "github:security"}
    if payload.get("kind") == "security" and payload.get("user"):
        return {"user": payload["user"], "kind": "security", "note": "github:security"}
    return None
