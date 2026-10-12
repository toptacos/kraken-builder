from pathlib import Path

import pytest

VANILLA = (
    "geo",
    "filesort",
    "pi-net",
    "vault",
    "store",
    "hotreload",
    "notes",
    "tunnel",
)


def make_tentacle_repo(root: Path, names):
    for name in names:
        d = root / "examples" / "tentacles" / name
        d.mkdir(parents=True, exist_ok=True)
        (d / "tentacle.yaml").write_text(f"name: {name}\nversion: 1.0.0\n")


def test_source_root_with_repo(tmp_path):
    from kraken.core.vanilla import source_root

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, ["geo"])
    result = source_root(repo=repo)
    assert result == repo


def test_source_root_repo_without_tentacles(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    monkeypatch.setattr("kraken.core.vanilla.user_home", lambda: tmp_path)
    monkeypatch.setattr(
        "kraken.core.vanilla.__file__", str(tmp_path / "fake" / "vanilla.py")
    )
    monkeypatch.delenv("KRAKEN_ROOT", raising=False)
    monkeypatch.delenv("KRAKEN_SRC", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    result = source_root(repo=repo)
    assert result == repo


def test_source_root_kraken_root_env(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, ["geo"])
    monkeypatch.setenv("KRAKEN_ROOT", str(repo))
    result = source_root()
    assert result == repo


def test_source_root_kraken_src_env(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, ["geo"])
    monkeypatch.setenv("KRAKEN_SRC", str(repo))
    result = source_root()
    assert result == repo


def test_source_root_home_fallback(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    monkeypatch.setattr("kraken.core.vanilla.user_home", lambda: tmp_path)
    src = tmp_path / ".kraken" / "src"
    make_tentacle_repo(src, ["geo"])
    result = source_root()
    assert result == src


def test_source_root_file_fallback(tmp_path):
    from kraken.core.vanilla import source_root

    result = source_root()
    assert (result / "examples" / "tentacles").is_dir()


def test_source_root_nested_src(tmp_path):
    from kraken.core.vanilla import source_root

    repo = tmp_path / "repo"
    nested = repo / "src"
    make_tentacle_repo(nested, ["geo"])
    result = source_root(repo=repo)
    assert result == nested


def test_source_root_no_match_returns_repo(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    monkeypatch.setattr("kraken.core.vanilla.user_home", lambda: tmp_path)
    monkeypatch.setattr(
        "kraken.core.vanilla.__file__", str(tmp_path / "fake" / "vanilla.py")
    )
    monkeypatch.delenv("KRAKEN_ROOT", raising=False)
    monkeypatch.delenv("KRAKEN_SRC", raising=False)
    repo = tmp_path / "repo"
    repo.mkdir()
    result = source_root(repo=repo)
    assert result == repo


def test_source_root_no_match_no_repo(tmp_path, monkeypatch):
    from kraken.core.vanilla import source_root

    monkeypatch.setattr("kraken.core.vanilla.user_home", lambda: tmp_path)
    monkeypatch.setattr(
        "kraken.core.vanilla.__file__", str(tmp_path / "fake" / "vanilla.py")
    )
    result = source_root()
    assert result == Path.cwd()


def test_install_vanilla_all_present(tmp_path):
    from kraken.core.vanilla import install_vanilla

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, VANILLA)
    result = install_vanilla(repo, home=tmp_path)
    assert result["ok"] is True
    assert result["missing"] == []
    assert set(result["installed"]) == set(VANILLA)
    assert result["needs_docker"] is False


def test_install_vanilla_some_missing(tmp_path):
    from kraken.core.vanilla import install_vanilla

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, ["geo", "vault"])
    result = install_vanilla(repo, home=tmp_path)
    assert result["ok"] is True
    assert set(result["installed"]) == {"geo", "vault"}
    assert set(result["missing"]) == set(VANILLA) - {"geo", "vault"}


def test_install_vanilla_none_present(tmp_path):
    from kraken.core.vanilla import install_vanilla

    repo = tmp_path / "repo"
    (repo / "examples" / "tentacles").mkdir(parents=True)
    result = install_vanilla(repo, home=tmp_path)
    assert result["ok"] is True
    assert result["installed"] == []
    assert set(result["missing"]) == set(VANILLA)


def test_install_vanilla_creates_layout(tmp_path):
    from kraken.core.vanilla import install_vanilla

    repo = tmp_path / "repo"
    make_tentacle_repo(repo, ["geo"])
    install_vanilla(repo, home=tmp_path)
    assert (tmp_path / ".kraken" / "tentacles" / "geo" / "tentacle.yaml").exists()
