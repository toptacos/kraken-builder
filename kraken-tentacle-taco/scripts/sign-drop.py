#!/usr/bin/env python3
"""Sign or verify a taco zip. minisign if present, else HMAC fixture (not Ed25519)."""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def tree_zip(dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in ROOT.rglob("*"):
            if path.is_file() and ".git" not in path.parts and path.name != dest.name:
                zf.write(path, path.relative_to(ROOT))
    return dest


def hmac_sign(blob: Path, keyfile: Path) -> Path:
    if not keyfile.exists():
        keyfile.write_bytes(os.urandom(32))
        keyfile.chmod(0o600)
    digest = hmac.new(keyfile.read_bytes(), blob.read_bytes(), hashlib.sha256).hexdigest()
    sig = blob.with_suffix(blob.suffix + ".sig")
    sig.write_text(json.dumps({"scheme": "taco-hmac", "sha256": digest, "file": blob.name}) + "\n")
    return sig


def hmac_verify(blob: Path, sig: Path, keyfile: Path) -> bool:
    body = json.loads(sig.read_text(encoding="utf-8"))
    expect = hmac.new(keyfile.read_bytes(), blob.read_bytes(), hashlib.sha256).hexdigest()
    return body.get("scheme") == "taco-hmac" and body.get("sha256") == expect


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "dist" / "taco.zip"))
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()
    out = Path(args.out)
    key = Path(os.environ.get("KRAKEN_HOME") or Path.home()) / ".kraken" / "data" / "taco" / "drop.key"
    key.parent.mkdir(parents=True, exist_ok=True)
    if args.verify:
        sig = out.with_suffix(out.suffix + ".sig")
        if not out.exists() or not sig.exists() or not key.exists():
            print("missing zip, sig, or key")
            return 2
        ok = hmac_verify(out, sig, key)
        print("ok" if ok else "fail")
        return 0 if ok else 3
    tree_zip(out)
    if shutil.which("minisign"):
        subprocess.run(["minisign", "-Sm", str(out)], check=False)
    hmac_sign(out, key)
    print(out)
    print(out.with_suffix(out.suffix + ".sig"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
