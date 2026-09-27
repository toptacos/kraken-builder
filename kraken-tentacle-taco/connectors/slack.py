"""Slack: /kraken taco @user — never bare /taco."""
from .command import peer_grant


def parse(payload: dict) -> dict | None:
    text = payload.get("text") or ""
    cmd = payload.get("command") or ""
    if cmd in {"/kraken", "/tt"}:
        text = f"{cmd} {text}".strip()
    src = payload.get("user_name") or payload.get("user_id") or payload.get("from")
    hit = peer_grant(text, src)
    if hit:
        hit["note"] = "slack"
    return hit
