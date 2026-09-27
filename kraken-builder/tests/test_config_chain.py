from pathlib import Path

from kraken.core.config import load_config
from kraken.core.paths import ensure_user_layout, walk_kraken_dirs


def test_ensure_user_layout(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    root = ensure_user_layout(tmp_path)
    assert (root / "config.yaml").exists()
    assert (root / "data").is_dir()
    assert (root / "tentacles").is_dir()


def test_project_overrides_user(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path / "home"))
    user = ensure_user_layout(tmp_path / "home")
    (user / "config.yaml").write_text("version: 1\nnotify: user\nregion: home\n")

    project = tmp_path / "proj" / "app"
    project.mkdir(parents=True)
    local = project / ".kraken"
    local.mkdir()
    (local / "config.yaml").write_text("notify: project\n")

    cfg = load_config(project)
    assert cfg["notify"] == "project"
    assert cfg["region"] == "home"
    assert walk_kraken_dirs(project)[-1] == local
