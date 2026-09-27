"""Discover arms from directories that contain arm.yaml. Restart or rebuild to pick up changes."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import yaml

from kraken.core.schema import REQUIRED_KEYS, ArmManifest


def default_arm_roots(repo_root: Path | None = None) -> list[Path]:
    root = repo_root or Path.cwd()
    return [root / "arms"]


def parse_manifest(path: Path) -> ArmManifest:
    data = yaml.safe_load(path.read_text()) or {}
    missing = [k for k in REQUIRED_KEYS if k not in data]
    if missing:
        raise ValueError(f"{path}: missing keys {missing}")
    return ArmManifest(
        name=str(data["name"]),
        version=str(data["version"]),
        entrypoint=str(data["entrypoint"]),
        description=str(data.get("description", "")),
        triggers=list(data.get("triggers", [])),
        actions=list(data.get("actions", [])),
        path=str(path.parent),
        raw=data,
    )


def load_arms(roots: Iterable[Path] | None = None) -> list[ArmManifest]:
    found: list[ArmManifest] = []
    for root in roots or default_arm_roots():
        if not root.exists():
            continue
        for manifest_path in sorted(root.glob("*/arm.yaml")):
            found.append(parse_manifest(manifest_path))
    return found
