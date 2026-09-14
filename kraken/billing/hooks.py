"""Hook adapters. Wire from tentacle.yaml hooks.after_install if you sell an arm.

Example tentacle.yaml:

  hooks:
    after_install:
      - tentacle: billing-log
        action: ping
        optional: true
    on_error:
      - tentacle: billing-log
        action: denied
        optional: true
"""

from __future__ import annotations

from typing import Any

from kraken.billing.client import log
from kraken.core.license import is_premium


def after_install(tentacle: str, spec: dict[str, Any] | None) -> dict[str, Any]:
    premium = is_premium(spec)
    log("hook.after_install", tentacle=tentacle, premium=premium)
    return {
        "ok": True,
        "premium": premium,
        "hint": None if not premium else "kraken license set",
    }


def on_denied(tentacle: str, error: str) -> dict[str, Any]:
    log("hook.denied", tentacle=tentacle, error=error)
    return {"ok": False, "tentacle": tentacle, "error": error}
