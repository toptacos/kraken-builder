#!/usr/bin/env python3
"""Content-addressed store. local | s3-mirror | pack for another Kraken box."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path


def _base() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    home = Path(raw) if raw else Path.home()
    d = home / ".kraken" / "data" / "store"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _blob_dir(root: Path) -> Path:
    d = root / "blobs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _manifest(root: Path) -> Path:
    return root / "manifest.json"


def _load(root: Path) -> dict:
    p = _manifest(root)
    if p.exists():
        return json.loads(p.read_text())
    return {"objects": {}}


def _save(root: Path, man: dict) -> None:
    _manifest(root).write_text(json.dumps(man, indent=2, sort_keys=True))


def _put_bytes(root: Path, name: str, data: bytes) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    dest = _blob_dir(root) / digest
    if not dest.exists():
        dest.write_bytes(data)
    man = _load(root)
    man["objects"][name] = {"sha256": digest, "bytes": len(data)}
    _save(root, man)
    return {"name": name, "sha256": digest, "bytes": len(data), "dedup": dest.exists()}


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "list"
    p = req.get("payload") or {}
    root = Path(p.get("dir") or _base())
    root.mkdir(parents=True, exist_ok=True)
    backend = str(p.get("backend") or "local")

    if action == "put":
        if p.get("path"):
            data = Path(p["path"]).read_bytes()
            name = str(p.get("name") or Path(p["path"]).name)
        else:
            name = str(p.get("name") or "object")
            data = str(p.get("value") or "").encode("utf-8")
        meta = _put_bytes(root, name, data)
        if backend == "s3":
            bucket = str(p.get("bucket") or "kraken-local")
            mirror = root / "s3" / bucket
            mirror.mkdir(parents=True, exist_ok=True)
            target = mirror / meta["sha256"]
            src = _blob_dir(root) / meta["sha256"]
            if not target.exists():
                shutil.copy2(src, target)
            meta["s3"] = str(target)
            meta["backend"] = "s3-mirror"
        else:
            meta["backend"] = "local"
        return _ok(req, meta)

    if action == "get":
        name = str(p.get("name") or "")
        man = _load(root)
        obj = (man.get("objects") or {}).get(name)
        if not obj:
            return _ok(req, {"error": f"missing {name}"}, ok=False)
        data = (_blob_dir(root) / obj["sha256"]).read_bytes()
        return _ok(req, {"name": name, "sha256": obj["sha256"], "value": data.decode("utf-8", "replace"), "bytes": len(data)})

    if action == "list":
        man = _load(root)
        return _ok(req, {"dir": str(root), "backend": backend, "objects": man.get("objects") or {}})

    if action == "export-pack":
        out = Path(p.get("out") or (root / "kraken.pack.json"))
        man = _load(root)
        pack = {"kind": "kraken.store.pack.v1", "objects": {}, "blobs": {}}
        for name, obj in (man.get("objects") or {}).items():
            digest = obj["sha256"]
            raw = (_blob_dir(root) / digest).read_bytes()
            pack["objects"][name] = obj
            pack["blobs"][digest] = base64.b64encode(raw).decode("ascii")
        out.write_text(json.dumps(pack))
        return _ok(req, {"pack": str(out), "count": len(pack["objects"]), "kind": pack["kind"]})

    if action == "import-pack":
        src = Path(p.get("pack") or "")
        pack = json.loads(src.read_text())
        if pack.get("kind") != "kraken.store.pack.v1":
            return _ok(req, {"error": "not a kraken store pack"}, ok=False)
        imported = 0
        for digest, b64 in (pack.get("blobs") or {}).items():
            dest = _blob_dir(root) / digest
            data = base64.b64decode(b64)
            if hashlib.sha256(data).hexdigest() != digest:
                return _ok(req, {"error": f"blob mismatch {digest}"}, ok=False)
            if not dest.exists():
                dest.write_bytes(data)
            imported += 1
        man = _load(root)
        man.setdefault("objects", {}).update(pack.get("objects") or {})
        _save(root, man)
        return _ok(req, {"imported_blobs": imported, "objects": man["objects"]})

    if action == "sync":
        # Copy local blobs into the s3-mirror folder (offline stand-in for aws s3 sync).
        bucket = str(p.get("bucket") or "kraken-local")
        mirror = root / "s3" / bucket
        mirror.mkdir(parents=True, exist_ok=True)
        copied = 0
        for blob in _blob_dir(root).iterdir():
            target = mirror / blob.name
            if blob.is_file() and not target.exists():
                shutil.copy2(blob, target)
                copied += 1
        return _ok(req, {"synced": copied, "mirror": str(mirror)})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
