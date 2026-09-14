"""Install and discover external tentacles under ~/.kraken/tentacles/."""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yaml

from kraken.core.config import load_config
from kraken.core.lockfile import record
from kraken.core.paths import ensure_user_layout


def parse_tentacle_yaml(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text()) or {}
    if "name" not in data:
        raise ValueError(f"{path} missing name")
    return data


def installed_dir(home: Path | None = None) -> Path:
    return ensure_user_layout(home) / "tentacles"


def discover_installed(home: Path | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    root = installed_dir(home)
    if not root.is_dir():
        return rows
    for manifest in sorted(root.glob("*/tentacle.yaml")):
        spec = parse_tentacle_yaml(manifest)
        spec["_root"] = str(manifest.parent)
        if "binary" not in spec:
            for candidate in ("handler.py", "echo-bin.py", "tentacle.py"):
                hit = manifest.parent / candidate
                if hit.exists():
                    spec["binary"] = str(hit)
                    break
        elif not Path(str(spec["binary"])).is_absolute():
            spec["binary"] = str((manifest.parent / spec["binary"]).resolve())
        rows.append(spec)
    return rows


def install_local(src: Path, home: Path | None = None) -> dict[str, Any]:
    src = src.resolve()
    manifest_path = src / "tentacle.yaml" if src.is_dir() else src
    if manifest_path.name != "tentacle.yaml":
        if (src / "tentacle.yaml").exists():
            manifest_path = src / "tentacle.yaml"
        else:
            raise FileNotFoundError(f"no tentacle.yaml in {src}")
    spec = parse_tentacle_yaml(manifest_path)
    name = str(spec["name"])
    dest = installed_dir(home) / name
    dest.mkdir(parents=True, exist_ok=True)
    src_dir = manifest_path.parent
    for item in src_dir.iterdir():
        target = dest / item.name
        if item.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(item, target)
        else:
            shutil.copy2(item, target)
    installed = parse_tentacle_yaml(dest / "tentacle.yaml")
    installed["_root"] = str(dest)
    if "binary" in installed and not Path(str(installed["binary"])).is_absolute():
        installed["binary"] = str((dest / installed["binary"]).resolve())
    record(name, str(installed.get("version") or "0.0.0"), source=str(src), home=home)
    return installed


def _git_url(raw: str) -> str | None:
    text = raw.strip()
    if text.startswith("https://") or text.startswith("git@"):
        return text
    if text.startswith("github.com/"):
        return "https://" + text
    if text.count("/") == 1 and not Path(text).exists():
        return f"https://github.com/{text}.git"
    return None


def install_from_git(url: str, home: Path | None = None) -> dict[str, Any]:
    clone = tempfile.mkdtemp(prefix="kraken-tentacle-")
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", url, clone],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"git clone failed: {url}")
    src = Path(clone)
    if not (src / "tentacle.yaml").exists():
        matches = list(src.glob("*/tentacle.yaml"))
        if matches:
            src = matches[0].parent
    return install_local(src, home=home)


def install_any(ref: str, home: Path | None = None) -> dict[str, Any]:
    git = _git_url(ref)
    if git:
        return install_from_git(git, home=home)
    return install_local(Path(ref), home=home)


def spec_by_name(root: Path, name: str, home: Path | None = None) -> dict[str, Any] | None:
    for spec in load_config(root).get("tentacles") or []:
        if spec.get("name") == name:
            return spec
    for spec in discover_installed(home):
        if spec.get("name") == name:
            return spec
    return None
