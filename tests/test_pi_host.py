from pathlib import Path

from kraken.core.loader import load_arms
from kraken.core.registry import Registry

ROOT = Path(__file__).resolve().parents[1]


def _registry() -> Registry:
    registry = Registry()
    registry.load_all(load_arms([ROOT / "arms"]))
    return registry


def test_two_tentacles_load():
    names = _registry().names()
    assert names == ["echo", "monitor", "pi-host"]


def test_pi_host_status():
    result = _registry().run("pi-host", "status")
    assert result["ok"] is True
    assert result["arm"] == "pi-host"
    assert "system" in result
