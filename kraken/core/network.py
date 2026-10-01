"""Optional Docker network. Off unless configured.

The shared network is named ``kraken``. Arms that emit a compose plan (berth)
declare that same bare name, so core must normalize *to* ``kraken`` rather than
away from it. Arbitrary labels are still namespaced under ``kraken_`` so two
projects never collide on one host.

A remote ``config_url`` is an outbound pull. Policy is offline-first and
inbound-only, so ``KRAKEN_OFFLINE=1`` skips the fetch and reports why.
"""

from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from kraken import __version__
from kraken.core.config import load_config

#: The one shared network name across arms, sites, and docs.
SHARED_NETWORK = "kraken"

DEFAULT: dict[str, Any] = {
    "enabled": False,
    "name": SHARED_NETWORK,
    "public": False,
    "isolated": False,
    "provider": "local",
    "config_url": "",
}


def normalize_network_name(name: str) -> str:
    """Canonicalize a network name onto the shared namespace.

    ``kraken`` and ``kraken_*`` pass through untouched; anything else is
    namespaced as ``kraken_<label>`` so a project label cannot claim the
    shared network.
    """
    text = str(name or "").strip()
    if not text:
        return SHARED_NETWORK
    if text == SHARED_NETWORK or text.startswith(f"{SHARED_NETWORK}_"):
        return text
    return f"{SHARED_NETWORK}_{text}"


#: Backwards-compatible private alias.
_normalize_name = normalize_network_name


def _offline() -> bool:
    return os.environ.get("KRAKEN_OFFLINE") == "1"


def _fetch(url: str, timeout: float = 3.0) -> dict[str, Any]:
    req = urllib.request.Request(
        url, headers={"User-Agent": f"kraken-cli/{__version__}"}
    )
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
        out["name"] = normalize_network_name(env_net)
    if env_url:
        out["config_url"] = env_url
        out["provider"] = "url"
    p = payload or {}
    if p.get("network"):
        out["name"] = normalize_network_name(str(p["network"]))
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
        if _offline():
            out["fetch_skipped"] = "offline"
            out["source"] = url
        else:
            try:
                remote = _fetch(url)
                for key in ("enabled", "name", "public", "isolated", "provider"):
                    if key in remote:
                        out[key] = remote[key]
                if remote.get("name"):
                    out["name"] = normalize_network_name(str(remote["name"]))
                out["source"] = url
            except Exception as exc:
                out["fetch_error"] = str(exc)[:300]
                out["source"] = url
    out["name"] = normalize_network_name(str(out.get("name") or SHARED_NETWORK))
    out["enabled"] = bool(out.get("enabled"))
    out["public"] = bool(out.get("public"))
    out["isolated"] = bool(out.get("isolated"))
    return out
