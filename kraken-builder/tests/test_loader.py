from pathlib import Path

from kraken.core.loader import load_arms, parse_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_echo_arm_is_discovered():
    arms = load_arms([ROOT / "arms"])
    names = [a.name for a in arms]
    assert "echo" in names


def test_manifest_requires_name(tmp_path: Path):
    bad = tmp_path / "arm.yaml"
    bad.write_text("version: '1'\nentrypoint: x:y\n")
    try:
        parse_manifest(bad)
        assert False, "expected ValueError"
    except ValueError as exc:
        assert "name" in str(exc)


from kraken.core.runner import list_all
from kraken.core.tentacle import install_local


def test_list_all_shows_both_kinds(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(ROOT / "examples" / "tentacles" / "geo", home=tmp_path)
    rows = {r["name"]: r["kind"] for r in list_all(ROOT)}
    assert rows.get("echo") == "in-process"
    assert rows.get("geo") == "binary"
