import json
from pathlib import Path

from kraken.core.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_cli_list(capsys):
    assert main(["--root", str(ROOT), "list"]) == 0
    out = capsys.readouterr().out
    assert "echo" in out
    assert "ping" in out


def test_cli_run_echo(capsys):
    assert main(["--root", str(ROOT), "run", "echo", "echo", "--payload", '{"ok":true}']) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["echo"]["ok"] is True


def test_cli_queue(capsys):
    assert main(["--root", str(ROOT), "queue", "echo", "ping"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["ok"] is True
