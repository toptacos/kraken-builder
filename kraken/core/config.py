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
    """Merged config across the chain. Signature-stable on purpose.

    Starts from the schema defaults rather than three hardcoded keys, so a
    partial file always resolves to a complete config. `data_dir` is a real
    setting now, so a caller asking for it gets the configured value.
    """
    from kraken.core import config_schema as cs

    merged: dict[str, Any] = cs.defaults()
    for directory in config_chain(start):
        # Unknown keys are merged through, not dropped: a config written by a
        # newer Kraken should not lose settings to an older one. They are
        # reported by `kraken config validate` instead of vanishing here.
        merged = _deep_merge(merged, load_yaml(directory / "config.yaml"))
    return merged
