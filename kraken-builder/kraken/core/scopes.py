"""Global vs organization API keys. Keys never leave ~/.kraken/keys/scopes.json."""

from __future__ import annotations

import json
import secrets
from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout


def _path(home: Path | None = None) -> Path:
    return ensure_user_layout(home) / "keys" / "scopes.json"


def load_scopes(home: Path | None = None) -> dict[str, Any]:
    path = _path(home)
    if not path.exists():
        return {"active": "global", "orgs": {}}
    data = json.loads(path.read_text() or "{}")
    data.setdefault("active", "global")
    data.setdefault("orgs", {})
    return data


def save_scopes(store: dict[str, Any], home: Path | None = None) -> Path:
    path = _path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(store, indent=2) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def set_scope(org: str, key: str = "", sites: list[str] | None = None, home: Path | None = None) -> dict[str, Any]:
    store = load_scopes(home)
    token = key or ("kk_" + secrets.token_urlsafe(24))
    store["orgs"][org] = {
        "key": token,
        "sites": list(sites or []),
    }
    store["active"] = org
    save_scopes(store, home)
    return {"ok": True, "org": org, "active": org, "sites": store["orgs"][org]["sites"]}


def use_scope(org: str, home: Path | None = None) -> dict[str, Any]:
    store = load_scopes(home)
    if org != "global" and org not in store["orgs"]:
        return {"ok": False, "error": f"unknown org {org}"}
    store["active"] = org
    save_scopes(store, home)
    return {"ok": True, "active": org, "sites": (store["orgs"].get(org) or {}).get("sites") or []}


def active_catalog(home: Path | None = None) -> dict[str, Any]:
    store = load_scopes(home)
    org = store.get("active") or "global"
    if org == "global":
        return {"ok": True, "active": "global", "filter": None, "note": "global lists everything installed locally"}
    row = store["orgs"].get(org) or {}
    return {
        "ok": True,
        "active": org,
        "filter": row.get("sites") or [],
        "has_key": bool(row.get("key")),
    }
