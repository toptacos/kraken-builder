from pathlib import Path

import pytest
import yaml


def test_cfg_default(tmp_path, monkeypatch):
    from kraken.core.grant import _cfg

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    path = _cfg(tmp_path)
    assert path == tmp_path / ".kraken" / "config.yaml"


def test_read_allow_no_config(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = read_allow(start=tmp_path)
    assert result == {
        k: False for k in ("tunnel", "remote_config", "scourge", "llm", "expose")
    }


def test_read_allow_with_grants(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("allow:\n  tunnel: true\n  llm: true\n")
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is True
    assert result["llm"] is True
    assert result["scourge"] is False


def test_read_allow_invalid_yaml(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("allow: [unclosed\n")
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is False


def test_read_allow_non_dict_yaml(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("- just\n- a\n- list\n")
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is False


def test_read_allow_allow_not_dict(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("allow: yes\n")
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is False


def test_read_allow_unknown_grant_ignored(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text(
        "allow:\n  unknown_cap: true\n  tunnel: true\n"
    )
    result = read_allow(start=tmp_path)
    assert "unknown_cap" not in result
    assert result["tunnel"] is True


def test_read_allow_value_not_true(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("allow:\n  tunnel: 'yes'\n")
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is False


def test_read_allow_project_overrides_user(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    user_cfg = tmp_path / ".kraken"
    user_cfg.mkdir()
    (user_cfg / "config.yaml").write_text("allow:\n  tunnel: true\n")
    proj_cfg = tmp_path / "proj" / ".kraken"
    proj_cfg.mkdir(parents=True)
    (proj_cfg / "config.yaml").write_text("allow:\n  tunnel: false\n")
    result = read_allow(start=tmp_path / "proj")
    assert result["tunnel"] is False


def test_read_allow_project_grant_adds(tmp_path, monkeypatch):
    from kraken.core.grant import read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    user_cfg = tmp_path / ".kraken"
    user_cfg.mkdir()
    (user_cfg / "config.yaml").write_text("allow:\n  tunnel: true\n")
    proj_cfg = tmp_path / "proj" / ".kraken"
    proj_cfg.mkdir(parents=True)
    (proj_cfg / "config.yaml").write_text("allow:\n  llm: true\n")
    result = read_allow(start=tmp_path / "proj")
    assert result["tunnel"] is True
    assert result["llm"] is True


def test_grant_unknown_name(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = grant("unknown_cap", True, home=tmp_path)
    assert result["ok"] is False
    assert "unknown grant" in result["error"]
    assert "tunnel" in result["known"]


def test_grant_new_file(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    result = grant("tunnel", True, home=tmp_path)
    assert result["ok"] is True
    assert result["grant"] == "tunnel"
    assert result["allowed"] is True
    assert cfg.exists()


def test_grant_existing_file(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("version: 1\nnotify: local\n")
    result = grant("scourge", True, home=tmp_path)
    assert result["ok"] is True
    content = cfg.read_text()
    assert "scourge: true" in content
    assert "version: 1" in content


def test_grant_invalid_yaml(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("allow: [unclosed\n")
    with pytest.raises(yaml.YAMLError):
        grant("tunnel", True, home=tmp_path)
    assert cfg.read_text() == "allow: [unclosed\n"


def test_grant_allow_not_dict(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("allow: yes\n")
    result = grant("tunnel", True, home=tmp_path)
    assert result["ok"] is True
    content = cfg.read_text()
    assert "tunnel: true" in content


def test_grant_preserves_other_keys(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / ".kraken" / "config.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("version: 1\ndata_dir: custom\n")
    grant("tunnel", True, home=tmp_path)
    content = cfg.read_text()
    assert "data_dir: custom" in content
    assert "version: 1" in content


def test_grant_off(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = grant("tunnel", False, home=tmp_path)
    assert result["ok"] is True
    assert result["allowed"] is False


def test_grant_chmod_failure(tmp_path, monkeypatch):
    from kraken.core.grant import grant

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))

    def fake_chmod(self, mode):
        raise OSError("read-only")

    monkeypatch.setattr(Path, "chmod", fake_chmod)
    result = grant("tunnel", True, home=tmp_path)
    assert result["ok"] is True


def test_grant_roundtrip(tmp_path, monkeypatch):
    from kraken.core.grant import grant, read_allow

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    grant("tunnel", True, home=tmp_path)
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is True
    grant("tunnel", False, home=tmp_path)
    result = read_allow(start=tmp_path)
    assert result["tunnel"] is False
