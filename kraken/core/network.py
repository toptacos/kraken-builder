"""Optional Docker network. Off unless configured. Config may come from a third party."""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from kraken.core.config import load_config

DEFAULT: dict[str, Any] = {
    "enabled": False,
    "name": "kraken_dev",
    "public": False,
    "isolated": False,
    "provider": "local",
    "config_url": "",
}


def _normalize_name(name: str) -> str:
    text = str(name or "dev").strip() or "dev"
    return text if text.startswith("kraken_") else f"kraken_{text}"


def _fetch(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = urllib.request.Request(url, headers={"User-Agent": "kraken-cli/0.1.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    text = raw.decode("utf-8", "replace")
    if url.endswith((".yaml", ".yml")) or text.lstrip().startswith(
        ("---", "enabled:", "name:")
    ):
        import yaml

        data = yaml.safe_load(text) or {}
    else:
        data = json.loads(text)
    return data if isinstance(data, dict) else {}


def resolve_docker(payload: dict[str, Any] | None = None, root=None) -> dict[str, Any]:
    """Merge config.yaml docker.*, env, payload, then optional URL. Fail closed on fetch error."""
    try:
        cfg = load_config(root).get("docker") or {}
    except Exception:
        cfg = {}
    out = dict(DEFAULT)
    for key in DEFAULT:
        if key in cfg:
            out[key] = cfg[key]
    env_net = os.environ.get("KRAKEN_DOCKER_NETWORK")
    env_url = os.environ.get("KRAKEN_DOCKER_CONFIG_URL")
    if env_net:
        out["enabled"] = True
        out["name"] = _normalize_name(env_net)
    if env_url:
        out["config_url"] = env_url
        out["provider"] = "url"
    p = payload or {}
    if p.get("network"):
        out["name"] = _normalize_name(str(p["network"]))
        out["enabled"] = True
    if "public" in p:
        out["public"] = bool(p["public"])
    if "isolated" in p:
        out["isolated"] = bool(p["isolated"])
    if p.get("config_url"):
        out["config_url"] = str(p["config_url"])
        out["provider"] = "url"
    if p.get("enabled") is False:
        out["enabled"] = False
    url = str(out.get("config_url") or "")
    if url and out.get("provider") == "url":
        try:
            remote = _fetch(url)
            for key in ("enabled", "name", "public", "isolated", "provider"):
                if key in remote:
                    out[key] = remote[key]
            if remote.get("name"):
                out["name"] = _normalize_name(str(remote["name"]))
            out["source"] = url
        except Exception as exc:
            out["fetch_error"] = str(exc)[:300]
            out["source"] = url
    out["name"] = _normalize_name(str(out.get("name") or "dev"))
    out["enabled"] = bool(out.get("enabled"))
    out["public"] = bool(out.get("public"))
    out["isolated"] = bool(out.get("isolated"))
    return out
