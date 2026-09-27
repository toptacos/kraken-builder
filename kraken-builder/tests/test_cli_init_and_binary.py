import json
from pathlib import Path

from kraken.core.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_init_creates_layout(tmp_path: Path, capsys):
    assert main(["init", "--home", str(tmp_path)]) == 0
    created = Path(capsys.readouterr().out.strip())
    assert (created / "config.yaml").exists()
    assert (created / "tentacles").is_dir()


def test_list_includes_binary_tentacle(capsys):
    assert main(["--root", str(ROOT), "list"]) == 0
    out = capsys.readouterr().out
    assert "echo" in out
    assert "pi-host" in out
    assert "echo-bin" in out


def test_run_external_binary(capsys):
    assert main(["--root", str(ROOT), "run", "echo-bin", "ping"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["result"]["arm"] == "echo-bin"
