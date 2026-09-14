from pathlib import Path

from kraken.core.cli import main
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local
from kraken.core.workflow import load_workflow, run_workflow


ROOT = Path(__file__).resolve().parents[1]
DOCKER = ROOT / "examples" / "tentacles" / "docker-env"
HOT = ROOT / "examples" / "tentacles" / "hotreload"
VAULT = ROOT / "examples" / "tentacles" / "vault"
STORE = ROOT / "examples" / "tentacles" / "store"


def _install_all(home: Path) -> None:
    for src in (DOCKER, HOT, VAULT, STORE):
        install_local(src, home=home)


def test_docker_env_plan(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _install_all(tmp_path)
    out = run_named(
        ROOT,
        "docker-env",
        "plan",
        {"name": "dev", "services": [{"name": "redis", "image": "redis:7-alpine", "ports": ["6379:6379"]}]},
    )
    assert out["ok"] is True
    assert "redis" in out["result"]["yaml"]
    assert "127.0.0.1:6379:6379" in out["result"]["yaml"]
    assert "kraken.tentacle: docker-env" in out["result"]["yaml"]
    share = run_named(
        ROOT,
        "docker-env",
        "share",
        {"name": "dev", "services": [{"name": "redis", "image": "redis:7-alpine", "ports": ["6379:6379"]}]},
    )
    assert share["result"]["kind"] == "kraken.docker-share.v1"
    assert share["result"]["network"] == "kraken_dev"


def test_hotreload_tick(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _install_all(tmp_path)
    app = tmp_path / "app"
    app.mkdir()
    target = app / "main.py"
    target.write_text("print(1)\n")
    watch = run_named(
        ROOT,
        "hotreload",
        "watch",
        {"name": "demo", "root": str(app), "patterns": ["*.py"], "command": ["true"]},
    )
    assert watch["ok"] is True
    tick1 = run_named(ROOT, "hotreload", "tick", {"name": "demo"})
    assert tick1["result"]["ran"] is False
    target.write_text("print(2)\n")
    tick2 = run_named(ROOT, "hotreload", "tick", {"name": "demo"})
    assert tick2["result"]["ran"] is True
    assert "main.py" in tick2["result"]["changed"]


def test_vault_and_store_share(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _install_all(tmp_path)
    assert run_named(ROOT, "vault", "init", {})["ok"] is True
    put = run_named(ROOT, "vault", "put", {"name": "token", "value": "secret-one"})
    assert put["ok"] is True
    got = run_named(ROOT, "vault", "get", {"name": "token"})
    assert got["result"]["value"] == "secret-one"
    stash = run_named(
        ROOT,
        "store",
        "put",
        {"name": "token.enc", "path": put["result"]["path"], "backend": "s3", "bucket": "kraken-local"},
    )
    assert stash["ok"] is True
    assert stash["result"]["sha256"]
    pack = run_named(ROOT, "store", "export-pack", {})
    other = tmp_path / "other"
    other.mkdir()
    monkeypatch.setenv("KRAKEN_HOME", str(other))
    install_local(STORE, home=other)
    incoming = run_named(ROOT, "store", "import-pack", {"pack": pack["result"]["pack"]})
    assert incoming["ok"] is True
    listed = run_named(ROOT, "store", "list", {})
    assert "token.enc" in listed["result"]["objects"]


def test_secure_share_workflow(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    _install_all(tmp_path)
    spec = load_workflow(ROOT / "examples" / "workflows" / "secure-share.yaml")
    out = run_workflow(ROOT, spec)
    assert out["ok"] is True
    assert out["results"]["pack"]["ok"] is True


def test_cli_lists_new_tentacles(tmp_path: Path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["--root", str(ROOT), "tentacle", "add", str(DOCKER)]) == 0
    assert main(["--root", str(ROOT), "tentacle", "add", str(HOT)]) == 0
    capsys.readouterr()
    assert main(["--root", str(ROOT), "tentacle", "list"]) == 0
    text = capsys.readouterr().out
    assert "docker-env" in text and "hotreload" in text
