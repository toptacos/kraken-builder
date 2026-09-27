"""User-facing effects. Tentacles return data; core notifies."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any


def notify_stdout(event: str, payload: dict[str, Any]) -> None:
    line = json.dumps({"notify": event, **payload})
    if os.environ.get("KRAKEN_NOTIFY_STDOUT") == "1":
        print(line)


def notify_webhook(event: str, payload: dict[str, Any]) -> None:
    url = os.environ.get("KRAKEN_NOTIFY_WEBHOOK")
    if not url:
        return
    body = json.dumps({"event": event, "payload": payload, "product": "kraken"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        urllib.request.urlopen(req, timeout=4)
    except OSError:
        return


def notify_ntfy(event: str, payload: dict[str, Any]) -> None:
    """Free: public ntfy.sh or your own ntfy container. No Firebase."""
    topic = os.environ.get("KRAKEN_NTFY_TOPIC")
    if not topic:
        return
    base = os.environ.get("KRAKEN_NTFY_URL", "https://ntfy.sh").rstrip("/")
    title = f"kraken {event}"
    body = json.dumps(payload)[:400]
    req = urllib.request.Request(
        f"{base}/{topic}",
        data=body.encode(),
        headers={"Title": title, "Content-Type": "text/plain"},
        method="POST",
    )
    try:
        urllib.request.urlopen(req, timeout=4)
    except OSError:
        return


def emit(event: str, payload: dict[str, Any] | None = None) -> None:
    data = payload or {}
    notify_stdout(event, data)
    notify_webhook(event, data)
    notify_ntfy(event, data)
