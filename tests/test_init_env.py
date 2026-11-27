import json
from pathlib import Path

from kraken.core.cli import main

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "examples" / "environments" / "compose"


def test_init_env_writes_workstation(tmp_path: Path, capsys):
    dest = tmp_path / "reef"
    assert main(["init", "--home", str(tmp_path / "home"), "--env", "--dir", str(dest)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["env"] is True
    assert (dest / "compose.yaml").exists()
    assert (dest / ".kraken" / "config.yaml").exists()
    assert (dest / "project.yaml").exists()
    config = (dest / ".kraken" / "config.yaml").read_text(encoding="utf-8")
    compose = (dest / "compose.yaml").read_text(encoding="utf-8")
    assert "public: false" in config
    assert "127.0.0.1:" in compose
    assert "--start" not in compose or "Pass --start only" in compose


def test_init_env_refuses_overwrite(tmp_path: Path, capsys):
    dest = tmp_path / "reef"
    dest.mkdir()
    (dest / "compose.yaml").write_text("services: {}\n")
    assert main(["init", "--home", str(tmp_path / "home"), "--env", "--dir", str(dest)]) == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["error"]["code"] == "exists"
    assert (dest / "compose.yaml").read_text(encoding="utf-8") == "services: {}\n"


def test_init_env_force(tmp_path: Path, capsys):
    dest = tmp_path / "reef"
    dest.mkdir()
    (dest / "compose.yaml").write_text("services: {}\n")
    rc = main(
        [
            "init",
            "--home",
            str(tmp_path / "home"),
            "--env",
            "--dir",
            str(dest),
            "--force",
        ]
    )
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert "127.0.0.1:" in (dest / "compose.yaml").read_text(encoding="utf-8")


def test_template_is_plan_only():
    compose = (TEMPLATE / "compose.yaml").read_text(encoding="utf-8")
    config = (TEMPLATE / ".kraken" / "config.yaml").read_text(encoding="utf-8")
    readme = (TEMPLATE / "README.md").read_text(encoding="utf-8")
    assert "127.0.0.1:" in compose
    assert "public: false" in config
    assert "docker compose up" in readme
    assert "kraken up --start" in readme
