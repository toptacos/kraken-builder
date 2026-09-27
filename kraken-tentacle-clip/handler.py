#!/usr/bin/env python3
"""clip — local share-URL index. No Facebook fetch."""
from __future__ import annotations

import json
import os
import platform
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

VERSION = "0.1.0"
PROTOCOL = 1


def data_dir(payload: dict | None = None) -> Path:
    payload = payload or {}
    if payload.get("dir"):
        p = Path(str(payload["dir"]))
        text = str(p).replace("\\", "/").lower()
        if any(x in text for x in ("/keys", "licenses.json", "topta.co", "kraken_catalog")):
            raise PermissionError("forbidden store path")
        p.mkdir(parents=True, exist_ok=True)
        return p
    h = os.environ.get("KRAKEN_HOME") or str(Path.home())
    d = Path(h) / ".kraken" / "data" / "clip"
    d.mkdir(parents=True, exist_ok=True)
    return d


def store_path(payload: dict | None = None) -> Path:
    return data_dir(payload) / "clips.json"


def load(payload: dict | None = None) -> dict:
    p = store_path(payload)
    if not p.exists():
        return {"clips": []}
    return json.loads(p.read_text(encoding="utf-8"))


def save(st: dict, payload: dict | None = None) -> None:
    p = store_path(payload)
    p.write_text(json.dumps(st, indent=2), encoding="utf-8")
    os.chmod(p, 0o600)


def ok(ident, result):
    return {"v": PROTOCOL, "id": ident, "ok": True, "result": result}


def err(ident, code, message):
    return {"v": PROTOCOL, "id": ident, "ok": False, "error": {"code": code, "message": message}}


def clean_url(raw: str) -> str:
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("empty url")
    u = urlparse(raw)
    if u.scheme not in ("http", "https"):
        raise ValueError("only http(s) share urls")
    # keep the link; do not rewrite into an unofficial download endpoint
    return raw


def host_of(url: str) -> str:
    return (urlparse(url).hostname or "").lower()


def add_clip(st: dict, url: str, title: str, note: str, tags: list) -> dict:
    url = clean_url(url)
    now = datetime.now(timezone.utc).isoformat()
    for c in st["clips"]:
        if c.get("url") == url:
            if title:
                c["title"] = title
            if note:
                c["note"] = note
            if tags:
                c["tags"] = sorted(set(c.get("tags") or []) | set(tags))
            c["updated"] = now
            return c
    item = {
        "id": f"c{len(st['clips'])+1:04d}",
        "url": url,
        "host": host_of(url),
        "title": title or host_of(url),
        "note": note,
        "tags": tags,
        "fetched": False,
        "created": now,
        "updated": now,
    }
    st["clips"].append(item)
    return item


def dispatch(req: dict) -> dict:
    action = req.get("action") or "ping"
    ident = req.get("id")
    p = req.get("payload") or {}
    if action in ("", "ping"):
        return ok(ident, {
            "arm": "clip", "version": VERSION, "protocol": PROTOCOL,
            "platform": f"{sys.platform}-{platform.machine()}",
            "fetches": False,
        })
    if action == "finish":
        raw = dict(p.get("raw") or {"arm": "clip"})
        raw.update(p.get("patch") or {})
        raw["finished"] = True
        return ok(ident, raw)
    try:
        st = load(p)
    except PermissionError as exc:
        return err(ident, "forbidden", str(exc))
    if action == "add":
        try:
            item = add_clip(st, p.get("url") or "", p.get("title") or "", p.get("note") or "", list(p.get("tags") or []))
        except ValueError as exc:
            return err(ident, "bad_url", str(exc))
        save(st, p)
        return ok(ident, {"arm": "clip", "clip": item, "count": len(st["clips"])})
    if action == "list":
        return ok(ident, {"arm": "clip", "count": len(st["clips"]), "clips": st["clips"]})
    if action == "get":
        cid = p.get("id") or p.get("url")
        for c in st["clips"]:
            if c.get("id") == cid or c.get("url") == cid:
                return ok(ident, {"arm": "clip", "clip": c})
        return err(ident, "not_found", "no clip")
    if action == "note":
        cid = p.get("id") or p.get("url")
        for c in st["clips"]:
            if c.get("id") == cid or c.get("url") == cid:
                c["note"] = p.get("note") or c.get("note")
                c["updated"] = datetime.now(timezone.utc).isoformat()
                save(st, p)
                return ok(ident, {"arm": "clip", "clip": c})
        return err(ident, "not_found", "no clip")
    if action == "remove":
        cid = p.get("id") or p.get("url")
        before = len(st["clips"])
        st["clips"] = [c for c in st["clips"] if c.get("id") != cid and c.get("url") != cid]
        save(st, p)
        return ok(ident, {"removed": before != len(st["clips"])})
    if action == "clear":
        st["clips"] = []
        save(st, p)
        return ok(ident, {"cleared": True})
    return err(ident, "unknown_action", f"unknown action {action}")


def main() -> int:
    raw = sys.stdin.read()
    req = json.loads(raw) if raw.strip() else {"action": "ping"}
    json.dump(dispatch(req), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
