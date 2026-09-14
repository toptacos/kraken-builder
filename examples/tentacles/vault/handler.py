#!/usr/bin/env python3
"""Encrypted credential / file vault. Uses openssl when present, else HMAC+XOR fallback for tests."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _root() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    d = base / ".kraken" / "data" / "vault"
    d.mkdir(parents=True, exist_ok=True)
    try:
        d.chmod(0o700)
    except OSError:
        pass
    return d


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result}))
    return 0


def _passphrase(p: dict) -> str:
    return str(p.get("passphrase") or os.environ.get("KRAKEN_VAULT_PASS") or "kraken-dev-pass")


def _openssl_crypt(data: bytes, password: str, decrypt: bool) -> bytes:
    exe = shutil.which("openssl")
    if not exe:
        raise FileNotFoundError("openssl")
    args = [exe, "enc", "-aes-256-cbc", "-pbkdf2", "-salt", "-pass", "env:KRAKEN_V"]
    if decrypt:
        args.append("-d")
    env = os.environ.copy()
    env["KRAKEN_V"] = password
    proc = subprocess.run(args, input=data, capture_output=True, check=False, env=env)
    if proc.returncode != 0:
        raise RuntimeError((proc.stderr or b"").decode("utf-8", "replace")[:400])
    return proc.stdout


def _fallback_crypt(data: bytes, password: str, decrypt: bool) -> bytes:
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), b"kraken-vault", 100_000, dklen=32)
    if decrypt:
        raw = data
        mac, blob = raw[:32], raw[32:]
        expect = hmac.new(key, blob, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expect):
            raise RuntimeError("bad mac")
        return bytes(b ^ key[i % 32] for i, b in enumerate(blob))
    blob = bytes(b ^ key[i % 32] for i, b in enumerate(data))
    mac = hmac.new(key, blob, hashlib.sha256).digest()
    return mac + blob


def crypt(data: bytes, password: str, decrypt: bool = False) -> bytes:
    try:
        return _openssl_crypt(data, password, decrypt)
    except (FileNotFoundError, RuntimeError):
        return _fallback_crypt(data, password, decrypt)


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "list"
    p = req.get("payload") or {}
    root = Path(p.get("dir") or _root())
    root.mkdir(parents=True, exist_ok=True)
    index_path = root / "index.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {"items": []}
    password = _passphrase(p)

    if action == "init":
        marker = root / ".init"
        marker.write_text("ok")
        index_path.write_text(json.dumps(index, indent=2))
        return _ok(req, {"dir": str(root), "ready": True, "openssl": bool(shutil.which("openssl"))})

    if action == "put":
        name = str(p.get("name") or "secret")
        if p.get("path"):
            raw = Path(p["path"]).read_bytes()
        else:
            raw = str(p.get("value") or "").encode("utf-8")
        token = crypt(raw, password, decrypt=False)
        dest = root / f"{name}.enc"
        dest.write_bytes(token)
        try:
            dest.chmod(0o600)
        except OSError:
            pass
        items = [i for i in index["items"] if i.get("name") != name]
        items.append({"name": name, "bytes": len(raw), "file": dest.name})
        index["items"] = items
        index_path.write_text(json.dumps(index, indent=2))
        return _ok(req, {"name": name, "stored": dest.name, "path": str(dest), "bytes": len(raw)})

    if action == "get":
        name = str(p.get("name") or "")
        dest = root / f"{name}.enc"
        if not dest.exists():
            return _ok(req, {"error": f"missing {name}"}, ok=False)
        plain = crypt(dest.read_bytes(), password, decrypt=True)
        return _ok(req, {"name": name, "value": plain.decode("utf-8", "replace"), "bytes": len(plain)})

    if action == "list":
        return _ok(req, {"dir": str(root), "items": index.get("items") or []})

    if action == "export-bundle":
        out = Path(p.get("out") or (root / "vault.bundle"))
        blob = {
            "kind": "kraken.vault.v1",
            "items": [],
        }
        for item in index.get("items") or []:
            dest = root / item["file"]
            if dest.exists():
                blob["items"].append(
                    {
                        "name": item["name"],
                        "enc": base64.b64encode(dest.read_bytes()).decode("ascii"),
                    }
                )
        out.write_text(json.dumps(blob))
        return _ok(req, {"bundle": str(out), "count": len(blob["items"])})

    if action == "import-bundle":
        src = Path(p.get("bundle") or "")
        blob = json.loads(src.read_text())
        count = 0
        for item in blob.get("items") or []:
            name = item["name"]
            dest = root / f"{name}.enc"
            dest.write_bytes(base64.b64decode(item["enc"]))
            index["items"] = [i for i in index["items"] if i.get("name") != name]
            index["items"].append({"name": name, "file": dest.name, "bytes": dest.stat().st_size})
            count += 1
        index_path.write_text(json.dumps(index, indent=2))
        return _ok(req, {"imported": count, "dir": str(root)})

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
