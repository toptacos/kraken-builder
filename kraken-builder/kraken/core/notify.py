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


#: channel name -> sender
CHANNELS = {
    "stdout": notify_stdout,
    "webhook": notify_webhook,
    "ntfy": notify_ntfy,
}


def enabled_channels() -> list[str]:
    """Which channels the config asks for.

    Defaults to stdout only. The config chooses the channels; the environment
    still supplies each one's credentials, so a channel with no variable set
    is skipped rather than failing the run. An outbound channel here is the
    one place Kraken talks to something that is not the machine it runs on —
    which is why 'local' means stdout and nothing else.
    """
    import os

    from kraken.core.config import load_config

    try:
        cfg = (load_config() or {}).get("notify")
    except Exception:
        cfg = None

    if isinstance(cfg, dict):
        channels = cfg.get("channels", ["stdout"])
    elif isinstance(cfg, str):
        from kraken.core.config_schema import NOTIFY_SHORTHAND

        # An explicit `notify: none` means no channels, not "fall back to
        # stdout". Only a missing config defaults to stdout.
        channels = NOTIFY_SHORTHAND.get(cfg, ["stdout"])
    else:
        channels = ["stdout"]

    if not isinstance(channels, list):
        return ["stdout"]
    return [c for c in channels if c in CHANNELS]


def emit(event: str, payload: dict[str, Any] | None = None) -> None:
    data = payload or {}
    for name in enabled_channels():
        try:
            CHANNELS[name](event, data)
        except Exception:
            # A notification must never fail the action that triggered it.
            continue
