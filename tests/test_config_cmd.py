from __future__ import annotations

import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from kraken.core import config_chain as cc
from kraken.core import config_schema as cs
from kraken.core import config_cmd


@pytest.fixture
def sandbox(tmp_path, monkeypatch):
    home = tmp_path / "home"
    system = tmp_path / "system"
    work = tmp_path / "work"
    for p in (home, system, work):
        p.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(system))
    monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
    monkeypatch.delenv("KRAKEN_DOCKER_CONFIG_URL", raising=False)
    monkeypatch.delenv("KRAKEN_LICENSE_REMOTE", raising=False)
    monkeypatch.chdir(work)
    return SimpleNamespace(home=home, system=system, work=work)


def write_config(base: Path, body: str) -> Path:
    d = base / ".kraken"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "config.yaml"
    p.write_text(body, encoding="utf-8")
    return p


class TestSettingView:
    def test_basic_fields(self):
        origin = cc.Origin("default", "schema")
        view = config_cmd._setting_view("data_dir", "data", origin)
        assert view["key"] == "data_dir"
        assert view["type"] == "string"
        assert view["value"] == "data"
        assert view["default"] == "data"
        assert view["changed"] is False
        assert view["scope"] == "default"
        assert view["source"] == "schema"
        assert "env" not in view
        assert "detail" in view

    def test_changed_flag_true_when_not_default(self):
        origin = cc.Origin("user", "/some/path")
        view = config_cmd._setting_view("data_dir", "other", origin)
        assert view["changed"] is True
        assert view["scope"] == "user"
        assert view["source"] == "/some/path"

    def test_env_present_when_setting_has_env(self):
        origin = cc.Origin("default", "schema")
        view = config_cmd._setting_view("docker", cs.BY_KEY["docker"].default, origin)
        assert view["env"] == "KRAKEN_DOCKER_CONFIG_URL"

    def test_detail_present_when_setting_has_detail(self):
        origin = cc.Origin("default", "schema")
        view = config_cmd._setting_view("version", 1, origin)
        assert "detail" in view
        assert len(view["detail"]) > 0

    def test_scopes_list(self):
        origin = cc.Origin("default", "schema")
        view = config_cmd._setting_view("data_dir", "data", origin)
        assert view["scopes"] == ["system", "user", "project"]


class TestChainView:
    def test_returns_list_of_dicts(self, sandbox):
        chain = config_cmd._chain_view()
        assert isinstance(chain, list)
        assert len(chain) > 0
        for item in chain:
            assert "scope" in item
            assert "path" in item
            assert "exists" in item

    def test_with_start_path(self, sandbox):
        start = sandbox.work / "sub"
        start.mkdir()
        chain = config_cmd._chain_view(start)
        assert isinstance(chain, list)
        assert len(chain) > 0


class TestCmdList:
    def test_success_no_problems(self, sandbox):
        write_config(sandbox.home, "data_dir: mydata\n")
        result, code = config_cmd.cmd_list(SimpleNamespace())
        assert code == 0
        assert result["ok"] is True
        assert result["verb"] == "config"
        assert result["action"] == "list"
        assert result["valid"] is True
        assert result["problems"] == []
        assert len(result["settings"]) == len(cs.SETTINGS)
        assert "chain" in result
        assert "text" in result

    def test_with_problems(self, sandbox):
        write_config(sandbox.home, "wibble: 1\n")
        result, code = config_cmd.cmd_list(SimpleNamespace())
        assert code == 2
        assert result["ok"] is False
        assert result["valid"] is False
        assert len(result["problems"]) > 0
        assert "wibble" in result["text"]

    def test_text_contains_settings(self, sandbox):
        result, _ = config_cmd.cmd_list(SimpleNamespace())
        assert "data_dir" in result["text"]
        assert "version" in result["text"]

    def test_text_shows_problems_count(self, sandbox):
        write_config(sandbox.home, "wibble: 1\nbad: 2\n")
        result, _ = config_cmd.cmd_list(SimpleNamespace())
        assert "problem(s)" in result["text"]


class TestCmdGet:
    def test_success(self, sandbox):
        write_config(sandbox.home, "data_dir: custom\n")
        result, code = config_cmd.cmd_get(SimpleNamespace(key="data_dir"))
        assert code == 0
        assert result["ok"] is True
        assert result["key"] == "data_dir"
        assert result["value"] == "custom"
        assert "setting" in result
        assert "text" in result

    def test_unknown_key(self, sandbox):
        result, code = config_cmd.cmd_get(SimpleNamespace(key="nonexistent"))
        assert code == 2
        assert result["ok"] is False
        assert result["error"]["code"] == "unknown_key"
        assert "nonexistent" in result["error"]["message"]
        assert "known" in result
        assert "text" in result

    def test_default_value(self, sandbox):
        result, code = config_cmd.cmd_get(SimpleNamespace(key="data_dir"))
        assert code == 0
        assert result["value"] == "data"

    def test_text_format(self, sandbox):
        write_config(sandbox.home, "data_dir: mydata\n")
        result, _ = config_cmd.cmd_get(SimpleNamespace(key="data_dir"))
        assert "data_dir" in result["text"]
        assert "mydata" in result["text"]


class TestCmdExplain:
    def test_success(self, sandbox):
        write_config(sandbox.home, "data_dir: explained\n")
        result, code = config_cmd.cmd_explain(SimpleNamespace(key="data_dir"))
        assert code == 0
        assert result["ok"] is True
        assert result["key"] == "data_dir"
        assert result["effective"] == "explained"
        assert result["won_by"]["scope"] == "user"
        assert "layers" in result
        assert "text" in result

    def test_unknown_key(self, sandbox):
        result, code = config_cmd.cmd_explain(SimpleNamespace(key="nope"))
        assert code == 2
        assert result["ok"] is False
        assert result["error"]["code"] == "unknown_key"

    def test_layers_include_file_values(self, sandbox):
        write_config(sandbox.home, "data_dir: from-user\n")
        write_config(sandbox.work, "data_dir: from-project\n")
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="data_dir"))
        scopes = [l["scope"] for l in result["layers"]]
        assert "user" in scopes
        assert "project" in scopes

    def test_env_note_telemetry(self, sandbox, monkeypatch):
        monkeypatch.setenv("KRAKEN_OFFLINE", "1")
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="telemetry"))
        assert result["ok"] is True
        env_layers = [l for l in result["layers"] if l["scope"] == "env"]
        assert len(env_layers) == 1
        assert env_layers[0]["source"] == "KRAKEN_OFFLINE"
        assert "overrides the file" in env_layers[0]["note"]

    def test_env_note_license(self, sandbox, monkeypatch):
        monkeypatch.setenv("KRAKEN_LICENSE_REMOTE", "0")
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="license"))
        env_layers = [l for l in result["layers"] if l["scope"] == "env"]
        assert len(env_layers) == 1
        assert env_layers[0]["source"] == "KRAKEN_LICENSE_REMOTE"

    def test_env_note_docker(self, sandbox, monkeypatch):
        monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", "https://example.com/c.json")
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="docker"))
        env_layers = [l for l in result["layers"] if l["scope"] == "env"]
        assert len(env_layers) == 1
        assert env_layers[0]["source"] == "KRAKEN_DOCKER_CONFIG_URL"

    def test_no_env_note_when_env_unset(self, sandbox):
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="telemetry"))
        env_layers = [l for l in result["layers"] if l["scope"] == "env"]
        assert len(env_layers) == 0

    def test_yaml_error_in_layer(self, sandbox):
        write_config(sandbox.home, "- not\n- a\n- mapping\n")
        with pytest.raises(ValueError, match="must be a mapping"):
            config_cmd.cmd_explain(SimpleNamespace(key="data_dir"))

    def test_text_contains_default(self, sandbox):
        result, _ = config_cmd.cmd_explain(SimpleNamespace(key="data_dir"))
        assert "default" in result["text"]


class TestOsOfflineNote:
    def test_telemetry_offline(self, monkeypatch):
        monkeypatch.setenv("KRAKEN_OFFLINE", "1")
        assert config_cmd.os_offline_note(cs.BY_KEY["telemetry"], "telemetry") is True

    def test_telemetry_no_offline(self, monkeypatch):
        monkeypatch.delenv("KRAKEN_OFFLINE", raising=False)
        assert config_cmd.os_offline_note(cs.BY_KEY["telemetry"], "telemetry") is False

    def test_license_remote_off(self, monkeypatch):
        monkeypatch.setenv("KRAKEN_LICENSE_REMOTE", "0")
        assert config_cmd.os_offline_note(cs.BY_KEY["license"], "license") is True

    def test_license_no_remote_off(self, monkeypatch):
        monkeypatch.delenv("KRAKEN_LICENSE_REMOTE", raising=False)
        assert config_cmd.os_offline_note(cs.BY_KEY["license"], "license") is False

    def test_docker_config_url_set(self, monkeypatch):
        monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", "https://x.com/c")
        assert config_cmd.os_offline_note(cs.BY_KEY["docker"], "docker") is True

    def test_docker_no_config_url(self, monkeypatch):
        monkeypatch.delenv("KRAKEN_DOCKER_CONFIG_URL", raising=False)
        assert config_cmd.os_offline_note(cs.BY_KEY["docker"], "docker") is False

    def test_other_key_returns_false(self, monkeypatch):
        monkeypatch.setenv("KRAKEN_OFFLINE", "1")
        monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", "https://x.com/c")
        monkeypatch.setenv("KRAKEN_LICENSE_REMOTE", "0")
        assert config_cmd.os_offline_note(cs.BY_KEY["data_dir"], "data_dir") is False


class TestCmdPath:
    def test_success(self, sandbox):
        result, code = config_cmd.cmd_path(SimpleNamespace())
        assert code == 0
        assert result["ok"] is True
        assert result["action"] == "path"
        assert "chain" in result
        assert "text" in result

    def test_chain_contains_scopes(self, sandbox):
        result, _ = config_cmd.cmd_path(SimpleNamespace())
        scopes = [c["scope"] for c in result["chain"]]
        assert "system" in scopes

    def test_text_format(self, sandbox):
        result, _ = config_cmd.cmd_path(SimpleNamespace())
        assert "system" in result["text"]


class TestCmdValidate:
    def test_success_no_problems(self, sandbox):
        write_config(sandbox.home, "data_dir: ok\n")
        result, code = config_cmd.cmd_validate(SimpleNamespace())
        assert code == 0
        assert result["ok"] is True
        assert result["valid"] is True
        assert result["problems"] == []
        assert "text" in result

    def test_with_problems(self, sandbox):
        write_config(sandbox.home, "wibble: 1\n")
        result, code = config_cmd.cmd_validate(SimpleNamespace())
        assert code == 2
        assert result["ok"] is False
        assert result["valid"] is False
        assert len(result["problems"]) > 0
        assert "wibble" in result["text"]

    def test_text_ok_message(self, sandbox):
        result, _ = config_cmd.cmd_validate(SimpleNamespace())
        assert "ok" in result["text"]
        assert str(len(cs.SETTINGS)) in result["text"]

    def test_chain_in_result(self, sandbox):
        result, _ = config_cmd.cmd_validate(SimpleNamespace())
        assert "chain" in result


class TestCmdInit:
    def test_project_scope(self, sandbox):
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert code == 0
        assert result["ok"] is True
        assert result["written"] is True
        assert result["scope"] == "project"
        target = sandbox.work / ".kraken" / "config.yaml"
        assert target.exists()
        assert result["error"] is None

    def test_user_scope(self, sandbox):
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="user"))
        assert code == 0
        assert result["ok"] is True
        assert result["written"] is True
        target = sandbox.home / ".kraken" / "config.yaml"
        assert target.exists()

    def test_system_scope(self, sandbox):
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="system"))
        assert code == 0
        assert result["ok"] is True
        assert result["written"] is True
        target = sandbox.system / "config.yaml"
        assert target.exists()

    def test_file_exists_error(self, sandbox):
        target = sandbox.work / ".kraken"
        target.mkdir(parents=True)
        (target / "config.yaml").write_text("existing: true\n")
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert code == 2
        assert result["ok"] is False
        assert result["written"] is False
        assert result["error"]["code"] == "exists"
        assert "already exists" in result["error"]["message"]

    def test_oserror(self, sandbox, monkeypatch):
        def raise_oserror(*a, **kw):
            raise OSError("disk full")

        monkeypatch.setattr(cc, "write_example", raise_oserror)
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert code == 2
        assert result["ok"] is False
        assert result["written"] is False
        assert "disk full" in result["error"]["message"]

    def test_written_but_problems(self, sandbox, monkeypatch):
        def bad_write(path, scope):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("wibble: 1\n", encoding="utf-8")
            return path

        monkeypatch.setattr(cc, "write_example", bad_write)
        result, code = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert code == 2
        assert result["ok"] is False
        assert result["written"] is True
        assert len(result["problems"]) > 0
        assert result["error"] is None

    def test_text_success(self, sandbox):
        result, _ = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert "wrote" in result["text"]

    def test_text_file_exists(self, sandbox):
        target = sandbox.work / ".kraken"
        target.mkdir(parents=True)
        (target / "config.yaml").write_text("existing: true\n")
        result, _ = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert "did not write" in result["text"]

    def test_text_written_but_problems(self, sandbox, monkeypatch):
        def bad_write(path, scope):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("wibble: 1\n", encoding="utf-8")
            return path

        monkeypatch.setattr(cc, "write_example", bad_write)
        result, _ = config_cmd.cmd_init(SimpleNamespace(scope="project"))
        assert "does not validate" in result["text"]
