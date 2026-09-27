"""Merge YAML from the .kraken chain. Later files override earlier keys."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from kraken.core.paths import config_chain


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if key in out and isinstance(out[key], dict) and isinstance(value, dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a mapping")
    return data


def load_config(start: Path | None = None) -> dict[str, Any]:
    merged: dict[str, Any] = {"version": 1, "tentacles": [], "notify": "local"}
    for directory in config_chain(start):
        merged = _deep_merge(merged, load_yaml(directory / "config.yaml"))
    return merged
