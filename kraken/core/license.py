"""Premium tentacle licenses. Free tools never call home.

Local store: ~/.kraken/keys/licenses.json
Remote (optional): POST {api_base}/api/kraken/licenses/verify
Default api_base: https://api.topta.co
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout

DEFAULT_API = "https://api.topta.co"


class LicenseError(PermissionError):
    pass


def _store_path(home: Path | None = None) -> Path:
    root = ensure_user_layout(home)
    return root / "keys" / "licenses.json"


def load_store(home: Path | None = None) -> dict[str, Any]:
    path = _store_path(home)
    if not path.exists():
        return {"api_base": os.environ.get("KRAKEN_API_BASE", DEFAULT_API), "keys": {}}
    data = json.loads(path.read_text() or "{}")
    data.setdefault("api_base", os.environ.get("KRAKEN_API_BASE", DEFAULT_API))
    data.setdefault("keys", {})
    return data


def save_store(store: dict[str, Any], home: Path | None = None) -> Path:
    path = _store_path(home)
    path.write_text(json.dumps(store, indent=2) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def issue_remote(tentacle: str, plan: str = "beta", api_base: str | None = None, email: str = "") -> dict[str, Any]:
    """Ask the control plane for a key. Offline tests mock this."""
    base = (api_base or os.environ.get("KRAKEN_API_BASE") or DEFAULT_API).rstrip("/")
    url = f"{base}/api/kraken/licenses/issue"
    body = json.dumps({"tentacle": tentacle, "plan": plan, "email": email, "product": "kraken"}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            payload = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        raise LicenseError(f"issue API {exc.code}: {exc.read().decode(errors='replace')}") from exc
    except urllib.error.URLError as exc:
        raise LicenseError(f"issue API unreachable ({base}): {exc.reason}") from exc
    if not payload.get("ok") or not payload.get("key"):
        raise LicenseError(payload.get("error") or "no key issued")
    return payload


def upgrade(tentacle: str, plan: str = "beta", email: str = "", home: Path | None = None) -> dict[str, Any]:
    issued = issue_remote(tentacle, plan=plan, email=email)
    set_key(tentacle, str(issued["key"]), home=home)
    store = load_store(home)
    store["keys"][tentacle]["plan"] = plan
    store["keys"][tentacle]["verified"] = True
    save_store(store, home)
    return {"ok": True, "tentacle": tentacle, "plan": plan, "key": issued["key"]}


def set_key(tentacle: str, key: str, home: Path | None = None) -> dict[str, Any]:
    store = load_store(home)
    store["keys"][tentacle] = {"key": key.strip(), "verified": False}
    save_store(store, home)
    return store["keys"][tentacle]


def is_premium(spec: dict[str, Any] | None) -> bool:
    if not spec:
        return False
    tier = str(spec.get("license") or spec.get("tier") or "free").lower()
    return tier in {"premium", "paid", "pro"}


def has_local_key(tentacle: str, home: Path | None = None) -> bool:
    key = load_store(home).get("keys", {}).get(tentacle, {}).get("key")
    return bool(key)


def verify_remote(tentacle: str, key: str, api_base: str | None = None, timeout: int = 8) -> dict[str, Any]:
    base = (api_base or os.environ.get("KRAKEN_API_BASE") or DEFAULT_API).rstrip("/")
    url = f"{base}/api/kraken/licenses/verify"
    body = json.dumps({"tentacle": tentacle, "key": key, "product": "kraken"}).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")
        raise LicenseError(f"license API {exc.code} for {tentacle}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LicenseError(f"license API unreachable ({base}): {exc.reason}") from exc
    if not payload.get("ok"):
        raise LicenseError(payload.get("error", {}).get("message") or "license rejected")
    return payload


def assert_licensed(tentacle: str, spec: dict[str, Any] | None = None, home: Path | None = None) -> None:
    if not is_premium(spec):
        return
    store = load_store(home)
    entry = store.get("keys", {}).get(tentacle) or {}
    key = entry.get("key")
    if not key:
        raise LicenseError(
            f"premium tentacle '{tentacle}' needs a license. "
            f"kraken license set {tentacle} <key>"
        )
    if os.environ.get("KRAKEN_LICENSE_OFFLINE") == "1":
        return
    if os.environ.get("KRAKEN_LICENSE_REMOTE") == "1":
        verify_remote(tentacle, key, store.get("api_base"), timeout=8)
        entry["verified"] = True
        store["keys"][tentacle] = entry
        save_store(store, home)
