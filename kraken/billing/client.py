"""Thin client around license store + api.topta.co. Core stays lean."""

from __future__ import annotations

import json
import os
import sys
from typing import Any

from kraken.core.license import (
    LicenseError,
    assert_licensed,
    load_store,
    set_key,
    upgrade,
    verify_remote,
)
from kraken.core.notify import emit


def log(event: str, **payload: Any) -> None:
    data = {"billing": event, **payload}
    if (
        os.environ.get("KRAKEN_BILLING_LOG") == "1"
        or os.environ.get("KRAKEN_NOTIFY_STDOUT") == "1"
    ):
        sys.stderr.write(json.dumps(data) + "\n")
        sys.stderr.flush()
    emit(f"billing.{event}", payload)


class BillingClient:
    """Optional. Construct only when a premium tentacle is in play."""

    def __init__(self, api_base: str | None = None) -> None:
        store = load_store()
        self.api_base = (
            api_base or store.get("api_base") or "https://api.topta.co"
        ).rstrip("/")
        log("init", api_base=self.api_base, keys=len(store.get("keys") or {}))

    def status(self) -> dict[str, Any]:
        store = load_store()
        log("status", keys=list((store.get("keys") or {}).keys()))
        return store

    def set(self, tentacle: str, key: str) -> dict[str, Any]:
        log("set", tentacle=tentacle)
        return set_key(tentacle, key)

    def upgrade(
        self, tentacle: str, plan: str = "beta", email: str = ""
    ) -> dict[str, Any]:
        log("upgrade", tentacle=tentacle, plan=plan)
        return upgrade(tentacle, plan=plan, email=email)

    def verify(self, tentacle: str) -> dict[str, Any]:
        store = load_store()
        entry = (store.get("keys") or {}).get(tentacle) or {}
        key = entry.get("key")
        if not key:
            log("verify_missing", tentacle=tentacle)
            raise LicenseError(f"no local key for {tentacle}")
        log("verify", tentacle=tentacle, api_base=self.api_base)
        return verify_remote(tentacle, key, self.api_base)

    def assert_premium(self, tentacle: str, spec: dict[str, Any] | None = None) -> None:
        log("assert", tentacle=tentacle, premium=True)
        assert_licensed(tentacle, spec)
