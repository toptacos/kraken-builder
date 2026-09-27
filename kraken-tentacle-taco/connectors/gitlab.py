"""GitLab webhook → taco event."""


def parse(payload: dict) -> dict | None:
    kind = payload.get("object_kind") or payload.get("event_type")
    attrs = payload.get("object_attributes") or {}
    user = (payload.get("user") or {}).get("username") or payload.get("user", {}).get("name")
    if kind in {"merge_request", "merge_request_event"} and attrs.get("state") in {"merged", "merged"}:
        return {"user": user, "kind": "pr", "note": f"gitlab:{attrs.get('url')}"}
    if kind in {"issue", "vulnerability"} and attrs.get("state") in {"closed", "resolved"}:
        labels = [str(x).lower() for x in (payload.get("labels") or [])]
        if any("security" in str(x) for x in labels) or kind == "vulnerability":
            return {"user": user, "kind": "security", "note": "gitlab:security"}
    return None
