"""Comprehensive tests for kraken.core.network — all functions and branches."""

from __future__ import annotations

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


def _clean_env(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(tmp_path / "no-such-system-dir"))
    for var in ("KRAKEN_DOCKER_NETWORK", "KRAKEN_DOCKER_CONFIG_URL", "KRAKEN_OFFLINE"):
        monkeypatch.delenv(var, raising=False)


def _write_config(tmp_path: Path, docker_yaml: str) -> None:
    kraken_dir = tmp_path / ".kraken"
    kraken_dir.mkdir(exist_ok=True)
    (kraken_dir / "config.yaml").write_text(f"docker:\n{docker_yaml}\n")


# --- normalize_network_name -------------------------------------------------


def test_normalize_network_name_empty_and_none():
    assert normalize_network_name("") == SHARED_NETWORK
    assert normalize_network_name(None) == SHARED_NETWORK
    assert normalize_network_name("   ") == SHARED_NETWORK
    assert normalize_network_name("\t\n") == SHARED_NETWORK


def test_normalize_network_name_shared_passthrough():
    assert normalize_network_name("kraken") == "kraken"
    assert normalize_network_name("kraken_lab") == "kraken_lab"
    assert normalize_network_name("kraken_a_b") == "kraken_a_b"


def test_normalize_network_name_namespaces_label():
    assert normalize_network_name("lab") == "kraken_lab"
    assert normalize_network_name("  lab  ") == "kraken_lab"
    assert normalize_network_name("Kraken") == "kraken_Kraken"


def test_normalize_network_name_coerces_non_string():
    assert normalize_network_name(123) == "kraken_123"
    assert normalize_network_name(0) == SHARED_NETWORK
    assert normalize_network_name(False) == SHARED_NETWORK


def test_normalize_name_alias():
    assert _normalize_name is normalize_network_name
    assert _normalize_name("lab") == "kraken_lab"


# --- _offline ----------------------------------------------------------------


def test_offline_enabled(monkeypatch):
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")
    assert _offline() is True


def test_offline_disabled(monkeypatch):
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    assert _offline() is False
    monkeypatch.setenv("KRAKEN_OFFLINE", "0")
    assert _offline() is False
    monkeypatch.setenv("KRAKEN_OFFLINE", "true")
    assert _offline() is False
    monkeypatch.setenv("KRAKEN_OFFLINE", "")
    assert _offline() is False


# --- _fetch ------------------------------------------------------------------


def test_fetch_json_file(tmp_path: Path):
    cfg = tmp_path / "net.json"
    cfg.write_text('{"enabled": true, "type": "kraken_ci", "isolated": true}')
    data = _fetch(cfg.as_uri())
    assert data == {"enabled": True, "type": "kraken_ci", "isolated": True}


def test_fetch_yaml_extensions(tmp_path: Path):
    for suffix in (".yaml", ".yml"):
        cfg = tmp_path / f"net{suffix}"
        cfg.write_text("enabled: true\nname: lab\n")
        assert _fetch(cfg.as_uri()) == {"enabled": True, "name": "lab"}


def test_fetch_yaml_content_markers(tmp_path: Path):
    for body in ("---\nenabled: true\n", "enabled: true\n", "name: lab\n"):
        cfg = tmp_path / "net.json"
        cfg.write_text(body)
        assert _fetch(cfg.as_uri()) == _fetch_yaml_expected(body)


def _fetch_yaml_expected(body: str) -> dict:
    if body.startswith("name:"):
        return {"name": "lab"}
    return {"enabled": True}


def test_fetch_non_dict_returns_empty(tmp_path: Path):
    cfg = tmp_path / "list.json"
    cfg.write_text("[1, 2, 3]")
    assert _fetch(cfg.as_uri()) == {}
    cfg = tmp_path / "scalar.json"
    cfg.write_text("42")
    assert _fetch(cfg.as_uri()) == {}
    cfg = tmp_path / "list.yaml"
    cfg.write_text("- a\n- b\n")
    assert _fetch(cfg.as_uri()) == {}


def test_fetch_empty_yaml_returns_empty(tmp_path: Path):
    cfg = tmp_path / "empty.yaml"
    cfg.write_text("")
    assert _fetch(cfg.as_uri()) == {}


def test_fetch_headers_and_default_timeout(monkeypatch):
    seen = {}

    class _Resp:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        seen["url"] = req.full_url
        seen["ua"] = req.headers.get("User-agent")
        seen["timeout"] = timeout
        return _Resp(b'{"enabled": true}')

    monkeypatch.setattr("kraken.core.network.urllib.request.urlopen", fake_urlopen)
    data = _fetch(NET_URL)
    assert data == {"enabled": True}
    assert seen["url"] == NET_URL
    assert seen["ua"] == f"kraken-cli/{__version__}"
    assert seen["timeout"] == 3.0


def test_fetch_custom_timeout_and_replace_decode(monkeypatch):
    seen = {}

    class _Resp:
        def __init__(self, payload: bytes):
            self._payload = payload

        def read(self) -> bytes:
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def fake_urlopen(req, timeout=None):
        seen["timeout"] = timeout
        return _Resp(b'{"name": "caf\xe9"}')

    monkeypatch.setattr("kraken.core.network.urllib.request.urlopen", fake_urlopen)
    data = _fetch(NET_URL, timeout=9.5)
    assert seen["timeout"] == 9.5
    assert data == {"name": "caf�"}


# --- resolve_docker ----------------------------------------------------------


def test_resolve_docker_defaults(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr("kraken.core.network.load_config", lambda root: {})
    net = resolve_docker({}, root=tmp_path)
    assert net == dict(DEFAULT)
    assert net["name"] == "kraken"
    assert net["enabled"] is False
    assert net["public"] is False
    assert net["isolated"] is False
    assert net["provider"] == "local"
    assert net["config_url"] == ""


def test_resolve_docker_payload_none(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr("kraken.core.network.load_config", lambda root: {})
    net = resolve_docker(root=tmp_path)
    assert net == dict(DEFAULT)


def test_resolve_docker_config_merge(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    _write_config(
        tmp_path,
        "  enabled: true\n  name: lab\n  public: true\n  isolated: true\n"
        '  provider: custom\n  config_url: ""\n  driver: bridge\n',
    )
    net = resolve_docker({}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"
    assert net["public"] is True
    assert net["isolated"] is True
    assert net["provider"] == "custom"
    assert "driver" not in net


def test_resolve_docker_config_docker_null(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "kraken.core.network.load_config", lambda root: {"docker": None}
    )
    net = resolve_docker({}, root=tmp_path)
    assert net == dict(DEFAULT)


def test_resolve_docker_config_load_raises(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)

    def boom(root):
        raise RuntimeError("no config")

    monkeypatch.setattr("kraken.core.network.load_config", boom)
    net = resolve_docker({}, root=tmp_path)
    assert net == dict(DEFAULT)


def test_resolve_docker_env_network(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "lab")
    net = resolve_docker({}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"


def test_resolve_docker_env_network_empty_ignored(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "")
    net = resolve_docker({}, root=tmp_path)
    assert net["enabled"] is False
    assert net["name"] == "kraken"


def test_resolve_docker_env_network_shared_passthrough(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "kraken")
    net = resolve_docker({}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken"


def test_resolve_docker_env_config_url_offline(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", NET_URL)
    monkeypatch.setenv("KRAKEN_OFFLINE", "1")

    def boom(url):
        raise AssertionError("fetch must be skipped offline")

    monkeypatch.setattr("kraken.core.network._fetch", boom)
    net = resolve_docker({}, root=tmp_path)
    assert net["provider"] == "url"
    assert net["config_url"] == NET_URL
    assert net["fetch_skipped"] == "offline"
    assert net["source"] == NET_URL
    assert "fetch_error" not in net


def test_resolve_docker_env_config_url_empty_ignored(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", "")
    net = resolve_docker({}, root=tmp_path)
    assert net["provider"] == "local"
    assert net["config_url"] == ""
    assert "source" not in net


def test_resolve_docker_payload_network(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    net = resolve_docker({"network": "lab"}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"
    net = resolve_docker({"network": "kraken"}, root=tmp_path)
    assert net["name"] == "kraken"


def test_resolve_docker_payload_network_empty_ignored(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    net = resolve_docker({"network": ""}, root=tmp_path)
    assert net["enabled"] is False
    assert net["name"] == "kraken"


def test_resolve_docker_payload_public_isolated(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    net = resolve_docker({"public": True, "isolated": True}, root=tmp_path)
    assert net["public"] is True
    assert net["isolated"] is True
    net = resolve_docker({"public": False, "isolated": False}, root=tmp_path)
    assert net["public"] is False
    assert net["isolated"] is False
    net = resolve_docker({"public": "yes", "isolated": 1}, root=tmp_path)
    assert net["public"] is True
    assert net["isolated"] is True


def test_resolve_docker_payload_config_url(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "kraken.core.network._fetch",
        lambda url: {"enabled": True, "name": "lab", "public": True},
    )
    net = resolve_docker({"config_url": NET_URL}, root=tmp_path)
    assert net["provider"] == "url"
    assert net["config_url"] == NET_URL
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"
    assert net["public"] is True
    assert net["source"] == NET_URL


def test_resolve_docker_payload_config_url_empty_ignored(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    net = resolve_docker({"config_url": ""}, root=tmp_path)
    assert net["provider"] == "local"
    assert "source" not in net


def test_resolve_docker_payload_enabled_false(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "lab")
    net = resolve_docker({"enabled": False}, root=tmp_path)
    assert net["enabled"] is False
    assert net["name"] == "kraken_lab"


def test_resolve_docker_payload_enabled_true(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    net = resolve_docker({"enabled": True}, root=tmp_path)
    assert net["enabled"] is False
    net = resolve_docker({"enabled": 0}, root=tmp_path)
    assert net["enabled"] is False


def test_resolve_docker_url_fetch_success(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "kraken.core.network._fetch",
        lambda url: {
            "enabled": True,
            "name": "lab",
            "public": True,
            "isolated": True,
            "provider": "remote",
        },
    )
    net = resolve_docker({"config_url": NET_URL}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"
    assert net["public"] is True
    assert net["isolated"] is True
    assert net["provider"] == "remote"
    assert net["source"] == NET_URL
    assert "fetch_error" not in net
    assert "fetch_skipped" not in net


def test_resolve_docker_url_fetch_partial_remote(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr("kraken.core.network._fetch", lambda url: {"public": True})
    net = resolve_docker({"config_url": NET_URL}, root=tmp_path)
    assert net["public"] is True
    assert net["enabled"] is False
    assert net["name"] == "kraken"
    assert net["isolated"] is False
    assert net["source"] == NET_URL


def test_resolve_docker_url_fetch_remote_blank_name(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setattr(
        "kraken.core.network._fetch", lambda url: {"name": "", "enabled": True}
    )
    net = resolve_docker({"config_url": NET_URL, "network": "keep"}, root=tmp_path)
    assert net["name"] == "kraken"
    assert net["enabled"] is True


def test_resolve_docker_url_fetch_error_truncated(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)

    def boom(url):
        raise OSError("x" * 500)

    monkeypatch.setattr("kraken.core.network._fetch", boom)
    net = resolve_docker({"config_url": NET_URL}, root=tmp_path)
    assert "fetch_error" in net
    assert len(net["fetch_error"]) == 300
    assert net["source"] == NET_URL
    assert "fetch_skipped" not in net


def test_resolve_docker_url_fetch_error_short(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)

    def boom(url):
        raise OSError("boom")

    monkeypatch.setattr("kraken.core.network._fetch", boom)
    net = resolve_docker({"config_url": NET_URL}, root=tmp_path)
    assert net["fetch_error"] == "boom"
    assert net["source"] == NET_URL


def test_resolve_docker_config_url_without_url_provider(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    _write_config(tmp_path, f'  config_url: "{NET_URL}"\n  provider: local\n')

    def boom(url):
        raise AssertionError("fetch must be skipped when provider is not url")

    monkeypatch.setattr("kraken.core.network._fetch", boom)
    net = resolve_docker({}, root=tmp_path)
    assert net["config_url"] == NET_URL
    assert net["provider"] == "local"
    assert "source" not in net
    assert "fetch_error" not in net
    assert "fetch_skipped" not in net


def test_resolve_docker_env_overrides_config(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    _write_config(tmp_path, "  enabled: true\n  name: lab\n")
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "prod")
    net = resolve_docker({}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_prod"


def test_resolve_docker_payload_overrides_env(monkeypatch, tmp_path: Path):
    _clean_env(monkeypatch, tmp_path)
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "lab")
    net = resolve_docker({"network": "prod"}, root=tmp_path)
    assert net["enabled"] is True
    assert net["name"] == "kraken_prod"
