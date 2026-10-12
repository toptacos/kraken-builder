from pathlib import Path

from kraken import __version__
from kraken.core.network import (
    DEFAULT,
    SHARED_NETWORK,
    _fetch,
    _normalize_name,
    _offline,
    normalize_network_name,
    resolve_docker,
)

NET_URL = "https://example.com/kraken-net.json"


def test_debug(tmp_path: Path):
    cfg = tmp_path / "net.json"
    cfg.write_text('{"enabled": true, "type": "kraken_ci", "isolated": true}')
    print("\nFETCH:", _fetch(cfg.as_uri()))
    assert _fetch(cfg.as_uri()) == {"enabled": True, "type": "kraken_ci", "isolated": True}
