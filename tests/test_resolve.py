from pathlib import Path

import pytest

from kraken.core.resolve import ResolveError, resolve
from kraken.core.semver import satisfies
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def test_echo_plan_is_self():
    plan = resolve(ROOT, "echo")
    assert plan.order == ["echo"]


def test_missing_dep(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(ROOT / "examples" / "tentacles" / "weather-pro", home=tmp_path)
    with pytest.raises(ResolveError, match="missing tentacle 'geo'"):
        resolve(ROOT, "weather-pro")


def test_version_mismatch(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    dest = tmp_path / ".kraken" / "tentacles" / "geo"
    dest.mkdir(parents=True)
    (dest / "tentacle.yaml").write_text("name: geo\nversion: '0.9.0'\nbinary: handler.py\n")
    (dest / "handler.py").write_text("print('x')\n")
    install_local(ROOT / "examples" / "tentacles" / "weather-pro", home=tmp_path)
    with pytest.raises(ResolveError, match="requires geo"):
        resolve(ROOT, "weather-pro")


def test_cycle(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    a = tmp_path / ".kraken" / "tentacles" / "loop-a"
    b = tmp_path / ".kraken" / "tentacles" / "loop-b"
    a.mkdir(parents=True)
    b.mkdir(parents=True)
    (a / "tentacle.yaml").write_text(
        "name: loop-a\nversion: '1.0.0'\nrequires:\n  tentacles:\n    loop-b: '*'\n"
    )
    (b / "tentacle.yaml").write_text(
        "name: loop-b\nversion: '1.0.0'\nrequires:\n  tentacles:\n    loop-a: '*'\n"
    )
    with pytest.raises(ResolveError, match="cycle"):
        resolve(ROOT, "loop-a")


def test_happy_stack(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(ROOT / "examples" / "tentacles" / "geo", home=tmp_path)
    install_local(ROOT / "examples" / "tentacles" / "weather-pro", home=tmp_path)
    plan = resolve(ROOT, "weather-pro")
    assert plan.order == ["geo", "weather-pro"]


def test_semver_ranges():
    assert satisfies("0.1.2", ">=0.1.0 <0.3.0")
    assert not satisfies("0.3.0", ">=0.1.0 <0.3.0")
    assert satisfies("1.2.0", "^1.0.0")
    assert not satisfies("2.0.0", "^1.0.0")
    assert satisfies("0.1.5", "~0.1.0")
    assert not satisfies("0.2.0", "~0.1.0")
