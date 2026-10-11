"""Local session + optional api.topta.co account. No push vendor in core.

Supports two auth modes:
- Local session: email + dev_ token (default, offline-first)
- Sanctum: bearer token from TopTacos SSO (KRAKEN_SANCTUM_TOKEN env var)

When a Sanctum token is present, it is used for all API calls and the local
session is synced to the TopTacos user. This lets CLI users authenticate
with their existing TopTacos account instead of creating a separate one.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

from kraken.core.paths import user_kraken
from kraken.core.notify import emit

STALE_SECS = int(os.environ.get("KRAKEN_DEVICE_STALE_SECS", str(30 * 24 * 3600)))

#: Sanctum token from TopTacos SSO. When set, API calls use this instead of
#: the local dev_ token. Get one from https://profile.topta.co or via the
#: SSO token exchange at /api/sso/token.
SANCTUM_TOKEN = os.environ.get("KRAKEN_SANCTUM_TOKEN", "")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nic_fingerprint() -> str:
    """Hashed hardware id. Never store a raw MAC."""
    node = uuid.getnode()
    raw = f"{node:012x}".encode()
    return "nic_" + hashlib.sha256(raw).hexdigest()[:16]


def host_signals() -> dict[str, Any]:
    """Best-effort laptop signals. Phones send these from Capacitor later."""
    out: dict[str, Any] = {"on": True}
    bat = Path("/sys/class/power_supply")
    if bat.is_dir():
        for name in ("BAT0", "BAT1", "battery"):
            cap = bat / name / "capacity"
            st = bat / name / "status"
            if cap.exists():
                out["charge_pct"] = cap.read_text().strip()
            if st.exists():
                status = st.read_text().strip().lower()
                out["plugged_in"] = status in {"charging", "full"}
                out["battery_status"] = status
        for name in ("AC", "ACAD", "ADP1", "mains"):
            online = bat / name / "online"
            if online.exists():
                out["plugged_in"] = online.read_text().strip() == "1"
    return out


def touch_device(sess: dict[str, Any], name: str, kind: str = "cli") -> dict[str, Any]:
    """Update last_seen. Flag stale or new nic on this group."""
    did = sess.get("device_id") or str(uuid.uuid4())
    sess["device_id"] = did
    nic = nic_fingerprint()
    now = _now()
    epoch = int(time.time())
    alerts: list[str] = []
    devices = list(sess.get("devices") or [])
    found = None
    for row in devices:
        if row.get("id") == did:
            found = row
            break
    if found is None:
        found = {"id": did, "kind": kind, "name": name}
        devices.append(found)
        if len(devices) > 1:
            alerts.append("new_device_on_group")
    last = found.get("last_seen_epoch") or 0
    if last and epoch - int(last) > STALE_SECS:
        alerts.append("stale_device_returned")
    prev_nic = found.get("nic")
    if prev_nic and prev_nic != nic:
        alerts.append("nic_changed")
    found.update(
        {
            "name": name,
            "kind": kind,
            "nic": nic,
            "last_seen": now,
            "last_seen_epoch": epoch,
            "signals": host_signals(),
        }
    )
    sess["devices"] = devices
    sess["alerts"] = alerts
    if alerts:
        emit("device.alert", {"device_id": did, "alerts": alerts, "name": name})
    return found


DEFAULT_API = "https://api.topta.co"


def _session_path(home: Path | None = None) -> Path:
    root = home or user_kraken()
    if root.name != ".kraken":
        root = root / ".kraken"
    d = root / "keys"
    d.mkdir(parents=True, exist_ok=True)
    return d / "session.json"


def load_session(home: Path | None = None) -> dict[str, Any]:
    path = _session_path(home)
    if not path.exists():
        return {
            "v": 1,
            "logged_in": False,
            "devices": [],
            "pinboard": {},
            "push": {"opt_in": False},
        }
    return json.loads(path.read_text())


def save_session(data: dict[str, Any], home: Path | None = None) -> Path:
    path = _session_path(home)
    path.write_text(json.dumps(data, indent=2) + "\n")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def login(
    email: str, device_name: str = "cli", home: Path | None = None
) -> dict[str, Any]:
    sess = load_session(home)
    sess.update(
        {
            "v": 1,
            "logged_in": True,
            "email": email,
            "device_id": sess.get("device_id") or str(uuid.uuid4()),
            "device_name": device_name,
            "token": sess.get("token") or "dev_" + uuid.uuid4().hex[:16],
            "api": os.environ.get("KRAKEN_API_BASE") or DEFAULT_API,
            "auth_mode": "local",
        }
    )
    if not sess.get("group_key"):
        sess["group_key"] = "kg_" + uuid.uuid4().hex
    touch_device(sess, device_name)
    save_session(sess, home)
    return {
        "ok": True,
        "mode": "local",
        "device_id": sess["device_id"],
        "email": email,
        "group_key": sess["group_key"],
        "alerts": sess.get("alerts") or [],
        "nic": nic_fingerprint(),
    }


def login_with_sanctum(
    token: str,
    email: str = "",
    device_name: str = "cli",
    home: Path | None = None,
) -> dict[str, Any]:
    """Authenticate with a TopTacos Sanctum token.

    This lets CLI users reuse their existing TopTacos SSO session instead
    of creating a separate local account. The token is stored in the session
    and used for all subsequent API calls.

    Get a token from:
    - https://profile.topta.co (web login)
    - POST /api/sso/token (SSO token exchange)
    - Set KRAKEN_SANCTUM_TOKEN env var
    """
    if not token or not token.strip():
        return {"ok": False, "error": "Sanctum token required"}

    sess = load_session(home)
    sess.update(
        {
            "v": 1,
            "logged_in": True,
            "email": email or sess.get("email") or "",
            "device_id": sess.get("device_id") or str(uuid.uuid4()),
            "device_name": device_name,
            "token": token.strip(),
            "api": os.environ.get("KRAKEN_API_BASE") or DEFAULT_API,
            "auth_mode": "sanctum",
        }
    )
    if not sess.get("group_key"):
        sess["group_key"] = "kg_" + uuid.uuid4().hex
    touch_device(sess, device_name)
    save_session(sess, home)
    return {
        "ok": True,
        "mode": "sanctum",
        "device_id": sess["device_id"],
        "email": sess.get("email") or "",
        "group_key": sess["group_key"],
        "alerts": sess.get("alerts") or [],
        "nic": nic_fingerprint(),
    }


def new_group(home: Path | None = None) -> dict[str, Any]:
    sess = load_session(home)
    sess["group_key"] = "kg_" + uuid.uuid4().hex
    sess["logged_in"] = True
    sess["device_id"] = sess.get("device_id") or str(uuid.uuid4())
    touch_device(sess, sess.get("device_name") or "cli")
    save_session(sess, home)
    return {
        "ok": True,
        "group_key": sess["group_key"],
        "device_id": sess["device_id"],
        "nic": nic_fingerprint(),
    }


def join_group(
    group_key: str, device_name: str = "cli", home: Path | None = None
) -> dict[str, Any]:
    key = group_key.strip()
    if not key.startswith("kg_") or len(key) < 8:
        return {"ok": False, "error": "group_key must look like kg_<hex>"}
    sess = load_session(home)
    sess["group_key"] = key
    sess["logged_in"] = True
    sess["device_id"] = sess.get("device_id") or str(uuid.uuid4())
    sess["device_name"] = device_name
    touch_device(sess, device_name)
    save_session(sess, home)
    return {
        "ok": True,
        "group_key": key,
        "device_id": sess["device_id"],
        "nic": nic_fingerprint(),
        "alerts": sess.get("alerts") or [],
    }


def logout(home: Path | None = None) -> dict[str, Any]:
    sess = load_session(home)
    sess["logged_in"] = False
    sess["token"] = ""
    save_session(sess, home)
    return {"ok": True, "logged_in": False}


def pin(key: str, value: Any, home: Path | None = None) -> dict[str, Any]:
    sess = load_session(home)
    board = dict(sess.get("pinboard") or {})
    board[key] = value
    sess["pinboard"] = board
    save_session(sess, home)
    return {"ok": True, "pinboard": board}


def set_push(
    opt_in: bool, token: str = "", kind: str = "web", home: Path | None = None
) -> dict[str, Any]:
    sess = load_session(home)
    sess["push"] = {"opt_in": bool(opt_in), "token": token, "kind": kind}
    save_session(sess, home)
    return {"ok": True, "push": sess["push"]}


def remote_register(sess: dict[str, Any]) -> dict[str, Any]:
    if os.environ.get("KRAKEN_SYNC_REMOTE") != "1":
        return {"ok": True, "mode": "local-only"}
    base = (sess.get("api") or DEFAULT_API).rstrip("/")
    token = SANCTUM_TOKEN or sess.get("token") or ""
    body = json.dumps(
        {
            "email": sess.get("email"),
            "device_id": sess.get("device_id"),
            "device_name": sess.get("device_name"),
            "token": token,
            "pinboard": sess.get("pinboard") or {},
            "push": sess.get("push") or {},
        }
    ).encode()
    req = request.Request(
        f"{base}/api/kraken/session/sync",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + token,
        },
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=8) as resp:
            return json.loads(resp.read().decode() or "{}")
    except (error.URLError, error.HTTPError, TimeoutError) as exc:
        return {"ok": False, "mode": "local", "error": str(exc)}
