import argparse
import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from kraken.core.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_main_no_args_exits(capsys):
    with pytest.raises(SystemExit):
        main([])


def test_main_unknown_command_exits(capsys):
    with pytest.raises(SystemExit):
        main(["frobnicate"])


def test_init_with_home(tmp_path, capsys):
    assert main(["init", "--home", str(tmp_path)]) == 0
    out = capsys.readouterr().out.strip()
    assert (Path(out) / "config.yaml").exists()
    assert (Path(out) / "tentacles").is_dir()


def test_init_with_kraken_home_env(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["init"]) == 0
    out = capsys.readouterr().out.strip()
    assert (Path(out) / "config.yaml").exists()


def test_init_without_home_uses_user_home(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["init"]) == 0
    out = capsys.readouterr().out.strip()
    assert Path(out) == tmp_path / ".kraken"


def test_list_command(capsys):
    assert main(["--root", str(ROOT), "list"]) == 0
    out = capsys.readouterr().out
    assert "echo" in out


def test_doctor_ok(capsys):
    assert main(["--root", str(ROOT), "doctor"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "checks" in data


def test_doctor_not_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.cli.inspect", return_value={"ok": False, "checks": []}):
        assert main(["--root", str(tmp_path), "doctor"]) == 2


def test_monitor_snapshot(capsys):
    assert main(["--root", str(ROOT), "monitor"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert "snapshot" in data


def test_monitor_with_url(capsys):
    assert main(["--root", str(ROOT), "monitor", "--url", "http://localhost:9999"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "ping" in data


def test_monitor_not_ok(tmp_path, capsys):
    with patch("kraken.core.cli.run_named", return_value={"ok": False}):
        assert main(["--root", str(tmp_path), "monitor"]) == 2


def test_workflow_run(tmp_path, capsys):
    wf = tmp_path / "wf.yaml"
    wf.write_text("steps:\n  - tentacle: echo\n    action: echo\n    payload: {}\n")
    assert main(["--root", str(ROOT), "workflow", "run", str(wf)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_workflow_workflow_error(tmp_path, capsys):
    wf = tmp_path / "wf.yaml"
    wf.write_text("not_a_list: true\n")
    assert main(["--root", str(ROOT), "workflow", "run", str(wf)]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_workflow_resolve_error(tmp_path, capsys):
    wf = tmp_path / "wf.yaml"
    wf.write_text("steps:\n  - tentacle: no-such-arm\n    action: ping\n")
    assert main(["--root", str(ROOT), "workflow", "run", str(wf)]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_workflow_license_error(tmp_path, capsys):
    from kraken.core.license import LicenseError

    wf = tmp_path / "wf.yaml"
    wf.write_text("steps:\n  - tentacle: echo\n    action: echo\n")
    with patch("kraken.core.cli.run_workflow", side_effect=LicenseError("no license")):
        assert main(["--root", str(ROOT), "workflow", "run", str(wf)]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_serve_site(capsys):
    assert main(["--root", str(ROOT), "serve-site"]) == 0
    out = capsys.readouterr().out
    assert "http.server" in out
    assert "8080" in out


def test_serve_site_custom_port(capsys):
    assert main(["--root", str(ROOT), "serve-site", "--port", "9999"]) == 0
    out = capsys.readouterr().out
    assert "9999" in out


def test_account_login(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "login", "dev@example.com"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["email"] == "dev@example.com"


def test_account_login_with_device(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "login", "dev@example.com", "--device", "pi"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_account_logout(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "logout"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["logged_in"] is False


def test_account_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "status"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "logged_in" in data


def test_account_pin(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "pin", "theme", "dark"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["pinboard"]["theme"] == "dark"


def test_account_sync_local_only(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.delenv("KRAKEN_SYNC_REMOTE", raising=False)
    assert main(["account", "sync"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["mode"] == "local-only"


def test_account_push(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "push", "--on", "--token", "tok123"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["push"]["opt_in"] is True


def test_account_push_default(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "push"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_account_group(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "group"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert "group_key" in data


def test_account_join(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "join", "kg_abc123def456"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_account_join_bad_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["account", "join", "bad-key"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_vanilla(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["vanilla", "--home", str(tmp_path)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert "installed" in data


def _demo_home(tmp_path):
    """A home with the vanilla tentacles installed, so `demo` does not depend
    on whatever the developer's ~/.kraken happens to contain."""
    from kraken.core.vanilla import install_vanilla

    home = tmp_path / "home"
    install_vanilla(ROOT, home)
    return home


def test_demo(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(_demo_home(tmp_path)))
    assert main(["--root", str(ROOT), "demo"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_demo_custom_ip(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(_demo_home(tmp_path)))
    assert main(["--root", str(ROOT), "demo", "--ip", "8.8.8.8"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_demo_resolve_error(tmp_path, capsys):
    from kraken.core.resolve import ResolveError

    with patch("kraken.core.cli.run_named", side_effect=ResolveError("arm not loaded")):
        assert main(["--root", str(tmp_path), "demo"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["hint"] == "kraken vanilla"


def test_demo_license_error(tmp_path, capsys):
    from kraken.core.license import LicenseError

    with patch("kraken.core.cli.run_named", side_effect=LicenseError("no license")):
        assert main(["--root", str(tmp_path), "demo"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_demo_key_error(tmp_path, capsys):
    with patch("kraken.core.cli.run_named", side_effect=KeyError("missing")):
        assert main(["--root", str(tmp_path), "demo"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_config_list(capsys):
    assert main(["--root", str(ROOT), "config", "list"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verb"] == "config"
    assert data["action"] == "list"


def test_config_get(capsys):
    assert main(["--root", str(ROOT), "config", "get", "data_dir"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["key"] == "data_dir"


def test_config_get_unknown_key(capsys):
    assert main(["--root", str(ROOT), "config", "get", "nonexistent"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error"]["code"] == "unknown_key"


def test_config_explain(capsys):
    assert main(["--root", str(ROOT), "config", "explain", "data_dir"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert "layers" in data


def test_config_explain_unknown_key(capsys):
    assert main(["--root", str(ROOT), "config", "explain", "nonexistent"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_config_path(capsys):
    assert main(["--root", str(ROOT), "config", "path"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert "chain" in data


def test_config_validate(capsys):
    assert main(["--root", str(ROOT), "config", "validate"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "valid" in data


def test_config_init_user(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.cli.first_run_init", lambda home=None: None)
    assert main(["config", "init", "--scope", "user"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["written"] is True


def test_config_init_project(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("kraken.core.cli.first_run_init", lambda home=None: None)
    assert main(["config", "init", "--scope", "project"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_config_init_system(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_SYSTEM_DIR", str(tmp_path / "system"))
    monkeypatch.setattr("kraken.core.cli.first_run_init", lambda home=None: None)
    assert main(["config", "init", "--scope", "system"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_config_init_already_exists(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("kraken.core.cli.first_run_init", lambda home=None: None)
    assert main(["config", "init", "--scope", "project"]) == 0
    capsys.readouterr()
    assert main(["config", "init", "--scope", "project"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["written"] is False


def test_config_no_action_defaults_to_list(capsys):
    assert main(["--root", str(ROOT), "config"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["action"] == "list"


def test_config_unknown_action(capsys):
    with pytest.raises(SystemExit):
        main(["--root", str(ROOT), "config", "bogus"])


def test_config_unmapped_action(capsys):
    ns = argparse.Namespace(cmd="config", config_action="bogus", root=ROOT)
    with patch("argparse.ArgumentParser.parse_args", return_value=ns):
        assert main(["config", "bogus"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error"]["code"] == "unknown_action"


def test_config_unmapped_action(capsys):
    ns = argparse.Namespace(
        cmd="config",
        config_action="bogus",
        root=Path.cwd(),
    )
    with patch("argparse.ArgumentParser.parse_args", return_value=ns):
        assert main(["config", "bogus"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error"]["code"] == "unknown_action"


def test_config_tty_output(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr(sys.stdout, "isatty", lambda: True)
    assert main(["config", "get", "data_dir"]) == 0
    out = capsys.readouterr().out
    assert "data_dir" in out


def test_up_plan_only(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up") as mock_up:
        mock_up.return_value = {"ok": True, "verb": "up", "daemon": False}
        assert main(["--root", str(tmp_path), "up"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_up_with_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    compose = tmp_path / "compose.yaml"
    compose.write_text("services:\n  web:\n    image: nginx\n")
    with patch("kraken.core.compose.up") as mock_up:
        mock_up.return_value = {"ok": True, "verb": "up"}
        assert main(["--root", str(tmp_path), "up", "--file", str(compose)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_up_with_arm(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up") as mock_up:
        mock_up.return_value = {"ok": True, "verb": "up"}
        assert main(["--root", str(tmp_path), "up", "--arm", "berth"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_up_with_start_flag(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up") as mock_up:
        mock_up.return_value = {"ok": True, "verb": "up", "daemon": True}
        assert main(["--root", str(tmp_path), "up", "--start"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_up_compose_error(tmp_path, monkeypatch, capsys):
    from kraken.core.compose import ComposeError

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up", side_effect=ComposeError("no plan")):
        assert main(["--root", str(tmp_path), "up"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error"]["code"] == "no_plan"


def test_up_result_not_ok(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up", return_value={"ok": False}):
        assert main(["--root", str(tmp_path), "up"]) == 2


def test_grant(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["grant", "expose"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["grant"] == "expose"


def test_grant_revoke(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["grant", "expose", "--revoke"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["allowed"] is False


def test_grant_unknown(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["grant", "bogus"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_self_plan(capsys):
    assert main(["--root", str(ROOT), "self", "plan"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "plan" in data


def test_self_plan_not_ok(tmp_path, capsys):
    with patch("kraken.core.cli.inspect", return_value={"ok": False}):
        assert main(["--root", str(tmp_path), "self", "plan"]) == 2


def test_tentacle_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["tentacle", "list"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)


def test_tentacle_add_local(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    src = tmp_path / "mytent"
    src.mkdir()
    (src / "tentacle.yaml").write_text("name: mytent\nversion: 1.0.0\n")
    (src / "handler.py").write_text("print('hi')\n")
    assert main(["tentacle", "add", str(src)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["name"] == "mytent"


def test_tentacle_add_resolve_error(tmp_path, monkeypatch, capsys):
    from kraken.core.resolve import ResolveError

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    src = tmp_path / "mytent"
    src.mkdir()
    (src / "tentacle.yaml").write_text("name: mytent\nversion: 1.0.0\n")
    (src / "handler.py").write_text("print('hi')\n")
    with patch("kraken.core.cli.resolve", side_effect=ResolveError("arm not loaded")):
        assert main(["tentacle", "add", str(src)]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_tentacle_plan(capsys):
    assert main(["--root", str(ROOT), "tentacle", "plan", "echo"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "root" in data


def test_tentacle_plan_resolve_error(tmp_path, capsys):
    from kraken.core.resolve import ResolveError

    with patch("kraken.core.cli.resolve", side_effect=ResolveError("arm not loaded")):
        assert main(["--root", str(tmp_path), "tentacle", "plan", "nope"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_license_status(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "status"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "keys" in data


def test_license_set(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "set", "weather-pro", "abc123"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["tentacle"] == "weather-pro"


def test_license_verify_no_key(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "verify", "weather-pro"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert data["error"] == "no local key"


def test_license_verify_success(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "set", "weather-pro", "abc123"]) == 0
    capsys.readouterr()
    with patch("kraken.core.cli.verify_remote", return_value={"ok": True}):
        assert main(["license", "verify", "weather-pro"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_license_verify_remote_error(tmp_path, monkeypatch, capsys):
    from kraken.core.license import LicenseError

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "set", "weather-pro", "abc123"]) == 0
    capsys.readouterr()
    with patch("kraken.core.cli.verify_remote", side_effect=LicenseError("rejected")):
        assert main(["license", "verify", "weather-pro"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_license_upgrade(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch(
        "kraken.core.cli.upgrade", return_value={"ok": True, "tentacle": "weather-pro"}
    ):
        assert main(["license", "upgrade", "weather-pro"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_license_upgrade_with_options(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.cli.upgrade", return_value={"ok": True}) as mock_up:
        assert (
            main(
                [
                    "license",
                    "upgrade",
                    "weather-pro",
                    "--plan",
                    "kraken-pro",
                    "--email",
                    "a@b.c",
                ]
            )
            == 0
        )
    mock_up.assert_called_once_with("weather-pro", plan="kraken-pro", email="a@b.c")


def test_license_upgrade_error(tmp_path, monkeypatch, capsys):
    from kraken.core.license import LicenseError

    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.cli.upgrade", side_effect=LicenseError("unknown plan")):
        assert main(["license", "upgrade", "weather-pro", "--plan", "bogus"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_run_echo(capsys):
    assert (
        main(["--root", str(ROOT), "run", "echo", "echo", "--payload", '{"ok":true}'])
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert data["echo"]["ok"] is True


def test_run_with_compose_flag(capsys):
    assert (
        main(
            [
                "--root",
                str(ROOT),
                "run",
                "echo",
                "echo",
                "--compose",
                "--payload",
                '{"ok":true}',
            ]
        )
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert "echo" in data


def test_run_invalid_json_payload(capsys):
    with pytest.raises(json.JSONDecodeError):
        main(["--root", str(ROOT), "run", "echo", "echo", "--payload", "not-json"])


def test_run_license_error(tmp_path, capsys):
    from kraken.core.license import LicenseError

    with patch("kraken.core.cli.run_named", side_effect=LicenseError("no license")):
        assert main(["--root", str(tmp_path), "run", "geo", "lookup"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_run_resolve_error(tmp_path, capsys):
    from kraken.core.resolve import ResolveError

    with patch("kraken.core.cli.run_named", side_effect=ResolveError("arm not loaded")):
        assert main(["--root", str(tmp_path), "run", "nope", "ping"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_run_key_error(tmp_path, capsys):
    with patch("kraken.core.cli.run_named", side_effect=KeyError("missing")):
        assert main(["--root", str(tmp_path), "run", "nope", "ping"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_queue_echo(capsys):
    assert main(["--root", str(ROOT), "queue", "echo", "ping"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data[0]["ok"] is True


def test_queue_with_trigger(capsys):
    assert (
        main(["--root", str(ROOT), "queue", "echo", "ping", "--trigger", "schedule"])
        == 0
    )
    data = json.loads(capsys.readouterr().out)
    assert data[0]["ok"] is True


def test_queue_license_error(tmp_path, capsys):
    from kraken.core.license import LicenseError

    with patch("kraken.core.cli.in_process_registry") as mock_reg:
        mock_reg.return_value.run.side_effect = LicenseError("no license")
        assert main(["--root", str(tmp_path), "queue", "geo", "lookup"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_queue_resolve_error(tmp_path, capsys):
    from kraken.core.resolve import ResolveError

    with patch("kraken.core.cli.in_process_registry") as mock_reg:
        mock_reg.return_value.run.side_effect = ResolveError("arm not loaded")
        assert main(["--root", str(tmp_path), "queue", "nope", "ping"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_queue_key_error(tmp_path, capsys):
    with patch("kraken.core.cli.in_process_registry") as mock_reg:
        mock_reg.return_value.run.side_effect = KeyError("missing")
        assert main(["--root", str(tmp_path), "queue", "nope", "ping"]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_instance_new(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome", "--label", "Test"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["name"] == "testhome"


def test_instance_new_no_label(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_instance_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome"]) == 0
    capsys.readouterr()
    assert main(["instance", "list"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert isinstance(data, list)
    assert len(data) >= 1


def test_instance_export(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome"]) == 0
    capsys.readouterr()
    out = tmp_path / "export.tgz"
    assert main(["instance", "export", "testhome", "--out", str(out)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["keys"] is False
    assert out.exists()


def test_instance_export_default_out(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    assert main(["instance", "new", "testhome"]) == 0
    capsys.readouterr()
    assert main(["instance", "export", "testhome"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert (tmp_path / "testhome.kraken.tgz").exists()


def test_instance_import(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome"]) == 0
    capsys.readouterr()
    out = tmp_path / "export.tgz"
    assert main(["instance", "export", "testhome", "--out", str(out)]) == 0
    capsys.readouterr()
    assert main(["instance", "import", str(out), "--name", "imported"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["name"] == "imported"


def test_instance_import_auto_name(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["instance", "new", "testhome"]) == 0
    capsys.readouterr()
    out = tmp_path / "export.tgz"
    assert main(["instance", "export", "testhome", "--out", str(out)]) == 0
    capsys.readouterr()
    assert main(["instance", "import", str(out)]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_root_flag_with_relative_path(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.chdir(ROOT)
    assert main(["--root", ".", "list"]) == 0
    out = capsys.readouterr().out
    assert "echo" in out


def test_run_with_kraken_home_env(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["run", "echo", "echo", "--payload", '{"ok":true}']) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["echo"]["ok"] is True


def test_monitor_url_empty_string(capsys):
    assert main(["--root", str(ROOT), "monitor", "--url", ""]) == 0
    data = json.loads(capsys.readouterr().out)
    assert "snapshot" in data
    assert "ping" not in data


def test_workflow_run_with_resolve_error_in_step(tmp_path, capsys):
    from kraken.core.resolve import ResolveError

    wf = tmp_path / "wf.yaml"
    wf.write_text("steps:\n  - tentacle: echo\n    action: echo\n")
    with patch(
        "kraken.core.cli.run_workflow", side_effect=ResolveError("arm not loaded")
    ):
        assert main(["--root", str(ROOT), "workflow", "run", str(wf)]) == 2
    data = json.loads(capsys.readouterr().err)
    assert data["ok"] is False


def test_config_list_with_problems(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("wibble: 1\n")
    assert main(["config", "list"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False
    assert len(data["problems"]) > 0


def test_config_validate_with_problems(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg_dir = tmp_path / ".kraken"
    cfg_dir.mkdir()
    (cfg_dir / "config.yaml").write_text("wibble: 1\n")
    assert main(["config", "validate"]) == 2
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is False


def test_up_no_file_no_arm(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.compose.up") as mock_up:
        mock_up.return_value = {"ok": True, "verb": "up"}
        assert main(["--root", str(tmp_path), "up"]) == 0
    _, kwargs = mock_up.call_args
    assert kwargs.get("start") is False


def test_tentacle_add_git_url(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    with patch("kraken.core.cli.install_any") as mock_install:
        mock_install.return_value = {"name": "gittent", "_root": "/tmp/gittent"}
        with patch("kraken.core.cli.resolve") as mock_resolve:
            mock_resolve.return_value = SimpleNamespace(
                as_dict=lambda: {"root": "gittent"}
            )
            assert main(["tentacle", "add", "github.com/org/repo"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert data["ok"] is True


def test_license_verify_with_api_base(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    assert main(["license", "set", "weather-pro", "abc123"]) == 0
    capsys.readouterr()
    with patch(
        "kraken.core.cli.verify_remote", return_value={"ok": True}
    ) as mock_verify:
        assert main(["license", "verify", "weather-pro"]) == 0
    mock_verify.assert_called_once()
    args = mock_verify.call_args[0]
    assert args[0] == "weather-pro"
    assert args[1] == "abc123"
