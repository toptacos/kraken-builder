"""Namespaced chat grammar so we do not steal /taco from other apps."""

PREFIXES = (
    ("/kraken", "taco"),
    ("kraken", "taco"),
    ("/tt", "taco"),
)


def peer_grant(text: str, sender: str | None) -> dict | None:
    if not text or not sender:
        return None
    parts = text.replace("<at>", "@").replace("</at>", "").split()
    parts = [p for p in parts if p]
    if len(parts) < 3:
        return None
    head = (parts[0].lower(), parts[1].lower())
    if head not in PREFIXES:
        return None
    target = parts[2].lstrip("@")
    if not target or target.lower() == str(sender).lower():
        return None
    return {"from": sender, "to": target, "kind": "taco"}
