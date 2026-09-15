"""Named Kraken homes. Share tentacles and config, never keys."""

from __future__ import annotations

import json
import re
import tarfile
from io import BytesIO
from pathlib import Path
from typing import Any

from kraken.core.paths import ensure_user_layout, user_home

SAFE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,62}$")
SKIP_EXPORT = {"keys", "logs", "cache"}


def instances_root() -> Path:
    root = user_home() / ".kraken" / "instances"
    root.mkdir(parents=True, exist_ok=True)
    return root


def instance_home(name: str) -> Path:
    if not SAFE.match(name):
        raise ValueError(
            "instance name must be alphanumeric, dot, underscore, or hyphen"
        )
    return instances_root() / name


def create_instance(name: str, label: str = "") -> dict[str, Any]:
    home = instance_home(name)
    ensure_user_layout(home)
    meta = {"name": name, "label": label or name}
    (home / ".kraken" / "instance.json").write_text(json.dumps(meta, indent=2) + "\n")
    return {"ok": True, "name": name, "home": str(home), "kraken_home": str(home)}


def list_instances() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(instances_root().iterdir()):
        if not path.is_dir():
            continue
        meta_path = path / ".kraken" / "instance.json"
        meta = (
            json.loads(meta_path.read_text())
            if meta_path.exists()
            else {"name": path.name}
        )
        tentacles = path / ".kraken" / "tentacles"
        count = len(list(tentacles.iterdir())) if tentacles.is_dir() else 0
        rows.append({**meta, "home": str(path), "tentacles": count})
    return rows


def export_bundle(name: str) -> bytes:
    home = instance_home(name)
    kraken = home / ".kraken"
    if not kraken.is_dir():
        raise FileNotFoundError(f"instance {name} has no .kraken")
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for path in kraken.rglob("*"):
            rel = path.relative_to(kraken)
            if rel.parts and rel.parts[0] in SKIP_EXPORT:
                continue
            if path.is_file() and path.name in {"licenses.json", ".env"}:
                continue
            tar.add(path, arcname=str(Path(name) / ".kraken" / rel), recursive=False)
        info = tarfile.TarInfo(name=f"{name}/README.txt")
        body = (
            f"Kraken instance '{name}'.\n"
            "Set KRAKEN_HOME to this folder after extract.\n"
            "Keys were not exported. Run kraken license set on the new box.\n"
        ).encode()
        info.size = len(body)
        tar.addfile(info, BytesIO(body))
    return buf.getvalue()


def import_bundle(archive: Path, name: str | None = None) -> dict[str, Any]:
    with tarfile.open(archive, mode="r:gz") as tar:
        members = [m for m in tar.getmembers() if m.name and not m.name.startswith("/")]
        top = members[0].name.split("/")[0] if members else (name or "imported")
        dest_name = name or top
        home = instance_home(dest_name)
        ensure_user_layout(home)
        for member in members:
            parts = Path(member.name).parts
            if len(parts) < 2:
                continue
            rel = Path(*parts[1:])
            if rel.parts and rel.parts[0] in SKIP_EXPORT:
                continue
            target = home / rel
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            extracted = tar.extractfile(member)
            if extracted is None:
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(extracted.read())
            target.chmod(0o600 if target.suffix in {".yaml", ".json"} else 0o644)
    return {"ok": True, "name": dest_name, "home": str(instance_home(dest_name))}
