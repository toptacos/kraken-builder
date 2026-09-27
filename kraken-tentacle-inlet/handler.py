#!/usr/bin/env python3
"""inlet — loopback UI + optional cloudflared. No remote shell."""
from __future__ import annotations

import json
import os
import platform
import secrets
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

VERSION = "0.1.0"
PROTOCOL = 1
DENIED = ("/keys", "keys/", "licenses.json", "kraken_catalog", "catalog.json")
LOOPBACK = "127.0.0.1"
DEFAULT_PORT = 7420


def ok(ident, result):
    return {"v": PROTOCOL, "id": ident, "ok": True, "result": result}


def err(ident, code, message):
    return {"v": PROTOCOL, "id": ident, "ok": False, "error": {"code": code, "message": message}}


def data_dir(payload: dict) -> Path:
    if payload.get("dir"):
        p = Path(str(payload["dir"]))
    else:
        h = os.environ.get("KRAKEN_HOME") or str(Path.home())
        p = Path(h) / ".kraken" / "data" / "inlet"
    text = str(p).replace("\\", "/").lower()
    if any(d in text for d in DENIED):
        raise PermissionError("forbidden path")
    p.mkdir(parents=True, exist_ok=True)
    return p


def roster_path(payload: dict) -> Path:
    return data_dir(payload) / "devices.json"


def load_roster(payload: dict) -> dict:
    p = roster_path(payload)
    if not p.exists():
        return {"devices": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save_roster(st: dict, payload: dict) -> None:
    p = roster_path(payload)
    p.write_text(json.dumps(st, indent=2), encoding="utf-8")
    os.chmod(p, 0o600)


def which_bins() -> dict:
    return {
        "cloudflared": bool(shutil.which("cloudflared")),
        "ngrok": bool(shutil.which("ngrok")),
    }


def dispatch(req: dict) -> dict:
    action = req.get("action") or "ping"
    ident = req.get("id")
    p = req.get("payload") or {}
    bins = which_bins()
    if action in ("", "ping"):
        return ok(ident, {
            "arm": "inlet", "version": VERSION, "protocol": PROTOCOL,
            "platform": f"{sys.platform}-{platform.machine()}",
            "brand": "TopTaco", "tagline": "One binary. Many tentacles.",
            "bind": LOOPBACK, "shell": False, **bins,
        })
    if action == "which":
        return ok(ident, {"arm": "inlet", **bins, "bind": LOOPBACK, "shell": False})
    if action == "finish":
        raw = dict(p.get("raw") or {"arm": "inlet"})
        raw.update(p.get("patch") or {})
        raw["finished"] = True
        raw.pop("token", None)
        return ok(ident, raw)
    try:
        st = load_roster(p)
    except PermissionError as exc:
        return err(ident, "forbidden", str(exc))

    if action == "devices":
        public = [{"id": d["id"], "name": d["name"], "created": d["created"]} for d in st["devices"]]
        return ok(ident, {"arm": "inlet", "count": len(public), "devices": public})

    if action == "grant":
        name = (p.get("name") or "device").strip()[:64]
        token = secrets.token_urlsafe(24)
        item = {
            "id": f"d{len(st['devices'])+1:04d}",
            "name": name,
            "token": token,
            "created": datetime.now(timezone.utc).isoformat(),
        }
        st["devices"].append(item)
        save_roster(st, p)
        return ok(ident, {
            "arm": "inlet",
            "device": {"id": item["id"], "name": name, "token": token},
            "note": "token shown once; store on the paired device only",
        })

    if action == "revoke":
        did = p.get("id") or p.get("name")
        before = len(st["devices"])
        st["devices"] = [d for d in st["devices"] if d.get("id") != did and d.get("name") != did]
        save_roster(st, p)
        return ok(ident, {"revoked": before != len(st["devices"])})

    if action == "listen":
        if p.get("bind") and p.get("bind") not in (LOOPBACK, "localhost"):
            return err(ident, "forbidden", "bind must be 127.0.0.1")
        if p.get("tunnel") and not bins["cloudflared"]:
            return err(ident, "need_bin", "cloudflared not installed")
        if p.get("tunnel") and not st["devices"]:
            return err(ident, "no_device", "grant a device before opening a tunnel")
        return ok(ident, {
            "arm": "inlet",
            "listen": f"http://{LOOPBACK}:{int(p.get('port') or DEFAULT_PORT)}",
            "ui": "control-plane",
            "shell": False,
            "tunnel": bool(p.get("tunnel")),
            "tunnel_bin": "cloudflared" if p.get("tunnel") else None,
            "started": False,
            "note": "handler plans the listener; Kraken does not keep a daemon. Run cloudflared yourself: cloudflared tunnel --url http://127.0.0.1:7420",
        })

    if action == "status":
        return ok(ident, {
            "arm": "inlet",
            "listen": f"http://{LOOPBACK}:{DEFAULT_PORT}",
            "devices": len(st["devices"]),
            "shell": False,
            "topta_register": False,
            "note": "api.topta.co device directory is not a control channel; roster is local",
        })

    if action == "stop":
        return ok(ident, {"arm": "inlet", "stopped": True, "shell": False})

    return err(ident, "unknown_action", f"unknown action {action}")


def main() -> int:
    raw = sys.stdin.read()
    req = json.loads(raw) if raw.strip() else {"action": "ping"}
    json.dump(dispatch(req), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
