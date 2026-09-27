"""Google Chat: kraken taco @user."""
from .command import peer_grant


def parse(payload: dict) -> dict | None:
    text = (payload.get("message") or {}).get("text") or payload.get("text") or ""
    sender = (
        ((payload.get("message") or {}).get("sender") or {}).get("displayName")
        or payload.get("from")
        or ""
    )
    hit = peer_grant(text, sender)
    if hit:
        hit["note"] = "gchat"
    return hit
