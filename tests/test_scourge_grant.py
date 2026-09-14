from pathlib import Path

from kraken.core.cli import main
from kraken.core.contract import invoke_binary
from kraken.core.grant import grant
from kraken.core.license import assert_licensed, is_premium, set_key


H = Path(__file__).resolve().parents[1] / "examples" / "tentacles" / "scourge"


def test_spec_is_premium():
    import yaml

    spec = yaml.safe_load((H / "tentacle.yaml").read_text())
    assert is_premium(spec)


def test_license_blocks_without_key(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    import yaml

    spec = yaml.safe_load((H / "tentacle.yaml").read_text())
    try:
        assert_licensed("scourge", spec)
        raised = False
    except Exception:
        raised = True
    assert raised
    set_key("scourge", "kk_test")
    monkeypatch.setenv("KRAKEN_LICENSE_OFFLINE", "1")
    # offline flag may or may not exist; devices still need grant
    out = invoke_binary(H / "handler.py", "devices", {})
    assert out["ok"] is False


def test_grant_unlocks_devices(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    grant("scourge", True)
    out = invoke_binary(H / "handler.py", "devices", {})
    assert out["ok"] is True


def test_grant_cli(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["grant", "scourge"]) == 0
    assert "scourge" in capsys.readouterr().out
