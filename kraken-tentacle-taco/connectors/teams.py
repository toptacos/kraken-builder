"""Teams: kraken taco @user."""
from .command import peer_grant


def parse(payload: dict) -> dict | None:
    text = payload.get("text") or (payload.get("message") or {}).get("text") or ""
    src = (payload.get("from") or {}).get("name") or payload.get("from") or ""
    if isinstance(src, dict):
        src = src.get("name") or ""
    hit = peer_grant(text, src)
    if hit:
        hit["note"] = "teams"
    return hit
