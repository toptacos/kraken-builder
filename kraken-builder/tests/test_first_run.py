from pathlib import Path

from kraken.core.cli import main


def test_list_creates_user_layout(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["--root", str(Path(__file__).resolve().parents[1]), "list"]) == 0
    capsys.readouterr()
    assert (tmp_path / ".kraken" / "config.yaml").exists()
