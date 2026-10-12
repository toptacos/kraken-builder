import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from kraken.core.tentacle import (
    _fire_after_install_hook,
    _git_url,
    _run_tentacle_tests,
    discover_installed,
    install_any,
    install_from_git,
    install_local,
    installed_dir,
    parse_tentacle_yaml,
    spec_by_name,
)


NT_SKIP = pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX-only: the scaffold handler is a sh script",
)


def _write_tentacle_yaml(path: Path, name: str, **kwargs) -> Path:
    data = {"name": name, **kwargs}
    path.mkdir(parents=True, exist_ok=True)
    manifest = path / "tentacle.yaml"
    manifest.write_text(yaml.safe_dump(data))
    return manifest


def test_parse_tentacle_yaml_success(tmp_path):
    manifest = tmp_path / "tentacle.yaml"
    manifest.write_text(yaml.safe_dump({"name": "test", "version": "1.0"}))
    result = parse_tentacle_yaml(manifest)
    assert result == {"name": "test", "version": "1.0"}


def test_parse_tentacle_yaml_empty_file_raises(tmp_path):
    manifest = tmp_path / "tentacle.yaml"
    manifest.write_text("")
    with pytest.raises(ValueError, match="missing name"):
        parse_tentacle_yaml(manifest)


def test_parse_tentacle_yaml_missing_name_raises(tmp_path):
    manifest = tmp_path / "tentacle.yaml"
    manifest.write_text(yaml.safe_dump({"version": "1.0"}))
    with pytest.raises(ValueError, match="missing name"):
        parse_tentacle_yaml(manifest)


def test_parse_tentacle_yaml_whitespace_only_raises(tmp_path):
    manifest = tmp_path / "tentacle.yaml"
    manifest.write_text("   \n  \n")
    with pytest.raises(ValueError, match="missing name"):
        parse_tentacle_yaml(manifest)


def test_run_tentacle_tests_no_tests_dir(tmp_path):
    result = _run_tentacle_tests(tmp_path)
    assert result == {"ok": True, "skipped": True, "reason": "no tests/ directory"}


def test_run_tentacle_tests_passing_tests(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    result = _run_tentacle_tests(tmp_path)
    assert result["ok"] is True
    assert result["returncode"] == 0


def test_run_tentacle_tests_failing_tests(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text("def test_fail():\n    assert False\n")
    result = _run_tentacle_tests(tmp_path)
    assert result["ok"] is False
    assert result["returncode"] != 0


def test_run_tentacle_tests_timeout(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_slow.py").write_text(
        "import time\ndef test_slow():\n    time.sleep(300)\n"
    )
    with patch(
        "subprocess.run",
        side_effect=subprocess.TimeoutExpired(cmd="pytest", timeout=120),
    ):
        result = _run_tentacle_tests(tmp_path)
    assert result == {"ok": False, "error": "test timeout (120s)"}


def test_run_tentacle_tests_exception(tmp_path):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    with patch("subprocess.run", side_effect=OSError("no such file")):
        result = _run_tentacle_tests(tmp_path)
    assert result["ok"] is False
    assert "no such file" in result["error"]


def test_installed_dir_default(monkeypatch, tmp_path):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    result = installed_dir()
    assert result == tmp_path / ".kraken" / "tentacles"


def test_installed_dir_with_home(tmp_path):
    result = installed_dir(tmp_path)
    assert result == tmp_path / ".kraken" / "tentacles"


def test_discover_installed_no_dir(tmp_path):
    result = discover_installed(tmp_path)
    assert result == []


def test_discover_installed_no_kraken_dir(tmp_path):
    result = discover_installed(tmp_path)
    assert result == []


def test_discover_installed_empty_dir(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    tentacles_dir.mkdir(parents=True)
    result = discover_installed(tmp_path)
    assert result == []


def test_discover_installed_with_tentacle_no_binary(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle", version="1.0")
    result = discover_installed(tmp_path)
    assert len(result) == 1
    assert result[0]["name"] == "my-tentacle"
    assert result[0]["_root"] == str(src)
    assert "binary" not in result[0]


def test_discover_installed_with_handler_py(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle")
    (src / "handler.py").write_text("# handler")
    result = discover_installed(tmp_path)
    assert result[0]["binary"] == str(src / "handler.py")


def test_discover_installed_with_echo_bin_py(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle")
    (src / "echo-bin.py").write_text("# echo")
    result = discover_installed(tmp_path)
    assert result[0]["binary"] == str(src / "echo-bin.py")


def test_discover_installed_with_tentacle_py(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle")
    (src / "tentacle.py").write_text("# tentacle")
    result = discover_installed(tmp_path)
    assert result[0]["binary"] == str(src / "tentacle.py")


def test_discover_installed_binary_absolute_path(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle", binary="/usr/local/bin/myapp")
    result = discover_installed(tmp_path)
    assert result[0]["binary"].replace("\\", "/") == "/usr/local/bin/myapp"


def test_discover_installed_binary_relative_path(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle", binary="bin/myapp")
    result = discover_installed(tmp_path)
    assert result[0]["binary"] == str((src / "bin/myapp").resolve())


def test_discover_installed_multiple_tentacles_sorted(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    _write_tentacle_yaml(tentacles_dir / "zeta", "zeta")
    _write_tentacle_yaml(tentacles_dir / "alpha", "alpha")
    _write_tentacle_yaml(tentacles_dir / "beta", "beta")
    result = discover_installed(tmp_path)
    assert [r["name"] for r in result] == ["alpha", "beta", "zeta"]


def test_discover_installed_skips_non_yaml_files(tmp_path):
    tentacles_dir = tmp_path / ".kraken" / "tentacles"
    src = tentacles_dir / "my-tentacle"
    _write_tentacle_yaml(src, "my-tentacle")
    (src / "README.md").write_text("# readme")
    result = discover_installed(tmp_path)
    assert len(result) == 1


def test_fire_after_install_hook_no_name(capsys):
    _fire_after_install_hook({})
    captured = capsys.readouterr()
    assert captured.err == ""


def test_fire_after_install_hook_root_not_exists(capsys):
    _fire_after_install_hook({"name": "test", "_root": "/nonexistent/path"})
    captured = capsys.readouterr()
    assert captured.err == ""


def test_fire_after_install_hook_tests_skipped(tmp_path, capsys):
    _fire_after_install_hook({"name": "test", "_root": str(tmp_path)})
    captured = capsys.readouterr()
    assert "Tests skipped" in captured.err


def test_fire_after_install_hook_tests_passed(tmp_path, capsys):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_ok.py").write_text("def test_ok():\n    assert True\n")
    _fire_after_install_hook({"name": "test", "_root": str(tmp_path)})
    captured = capsys.readouterr()
    assert "Tests passed" in captured.err


def test_fire_after_install_hook_tests_failed(tmp_path, capsys):
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_fail.py").write_text("def test_fail():\n    assert False\n")
    _fire_after_install_hook({"name": "test", "_root": str(tmp_path)})
    captured = capsys.readouterr()
    assert "Tests failed" in captured.err


def test_fire_after_install_hook_hook_exception(tmp_path, capsys, monkeypatch):
    def raise_exc(*args, **kwargs):
        raise RuntimeError("hook boom")

    monkeypatch.setattr("kraken.core.hooks.fire_hooks", raise_exc)
    _fire_after_install_hook({"name": "test", "_root": str(tmp_path)})
    captured = capsys.readouterr()
    assert "Warning: after_install hook error: hook boom" in captured.err


def test_install_local_success(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle", version="2.0")
    (src / "handler.py").write_text("# handler")
    home = tmp_path / "home"
    result = install_local(src, home=home)
    assert result["name"] == "my-tentacle"
    assert result["version"] == "2.0"
    assert result["_root"] == str(home / ".kraken" / "tentacles" / "my-tentacle")
    assert (home / ".kraken" / "tentacles" / "my-tentacle" / "handler.py").exists()
    assert (home / ".kraken" / "tentacles" / "my-tentacle" / "tentacle.yaml").exists()


def test_install_local_from_manifest_path(tmp_path):
    src = tmp_path / "src"
    manifest = _write_tentacle_yaml(src, "my-tentacle")
    home = tmp_path / "home"
    result = install_local(manifest, home=home)
    assert result["name"] == "my-tentacle"


def test_install_local_no_tentacle_yaml_raises(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "README.md").write_text("# readme")
    with pytest.raises(FileNotFoundError):
        install_local(src)


def test_install_local_non_tentacle_yaml_name_raises(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "other.yaml").write_text("name: test")
    with pytest.raises(FileNotFoundError, match="no tentacle.yaml"):
        install_local(src / "other.yaml")


def test_discover_installed_missing_tentacles_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.tentacle.installed_dir",
        lambda home: tmp_path / "nonexistent" / "tentacles",
    )
    result = discover_installed(tmp_path)
    assert result == []


def test_install_local_resolves_relative_binary(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle", binary="bin/run.sh")
    home = tmp_path / "home"
    result = install_local(src, home=home)
    expected = (home / ".kraken" / "tentacles" / "my-tentacle" / "bin/run.sh").resolve()
    assert result["binary"] == str(expected)


def test_install_local_keeps_absolute_binary(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle", binary="/opt/bin/run.sh")
    home = tmp_path / "home"
    result = install_local(src, home=home)
    assert result["binary"].replace("\\", "/") == "/opt/bin/run.sh"


def test_install_local_records_lockfile(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle", version="3.0")
    home = tmp_path / "home"
    install_local(src, home=home)
    lock_file = home / ".kraken" / "tentacles.lock"
    assert lock_file.exists()
    import json

    data = json.loads(lock_file.read_text())
    assert data["tentacles"]["my-tentacle"]["version"] == "3.0"


def test_install_local_copies_directories(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle")
    subdir = src / "subdir"
    subdir.mkdir()
    (subdir / "module.py").write_text("# module")
    home = tmp_path / "home"
    install_local(src, home=home)
    assert (
        home / ".kraken" / "tentacles" / "my-tentacle" / "subdir" / "module.py"
    ).exists()


def test_install_local_replaces_existing_directory(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "my-tentacle")
    subdir = src / "subdir"
    subdir.mkdir()
    (subdir / "old_module.py").write_text("# old")
    home = tmp_path / "home"
    install_local(src, home=home)
    (
        home / ".kraken" / "tentacles" / "my-tentacle" / "subdir" / "old_module.py"
    ).write_text("# modified")
    (subdir / "old_module.py").unlink()
    (subdir / "new_module.py").write_text("# new")
    install_local(src, home=home)
    dest_subdir = home / ".kraken" / "tentacles" / "my-tentacle" / "subdir"
    assert not (dest_subdir / "old_module.py").exists()
    assert (dest_subdir / "new_module.py").exists()


def test_git_url_https():
    assert _git_url("https://github.com/user/repo") == "https://github.com/user/repo"


def test_git_url_git_at():
    assert _git_url("git@github.com:user/repo.git") == "git@github.com:user/repo.git"


def test_git_url_github_com_prefix():
    assert _git_url("github.com/user/repo") == "https://github.com/user/repo"


def test_git_url_owner_repo_format():
    assert _git_url("user/repo") == "https://github.com/user/repo.git"


def test_git_url_owner_repo_with_git_suffix():
    assert _git_url("user/repo.git") == "https://github.com/user/repo.git.git"


def test_git_url_local_path_returns_none(tmp_path):
    assert _git_url(str(tmp_path)) is None


def test_git_url_random_string_returns_none():
    assert _git_url("not-a-url") is None


def test_git_url_deep_path_returns_none():
    assert _git_url("a/b/c") is None


def test_git_url_empty_string_returns_none():
    assert _git_url("") is None


def test_git_url_whitespace_stripped():
    assert (
        _git_url("  https://github.com/user/repo  ") == "https://github.com/user/repo"
    )


def test_install_from_git_success(tmp_path):
    home = tmp_path / "home"

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[5])
        clone_dir.mkdir(parents=True, exist_ok=True)
        _write_tentacle_yaml(clone_dir, "git-tentacle", version="1.0")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        result = install_from_git("https://github.com/user/repo", home=home)
    assert result["name"] == "git-tentacle"
    assert (home / ".kraken" / "tentacles" / "git-tentacle" / "tentacle.yaml").exists()


def test_install_from_git_clone_failure_raises(tmp_path):
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="clone failed")

    with patch("subprocess.run", side_effect=mock_run):
        with pytest.raises(RuntimeError, match="clone failed"):
            install_from_git("https://github.com/user/repo")


def test_install_from_git_clone_failure_empty_stderr(tmp_path):
    def mock_run(cmd, **kwargs):
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        with pytest.raises(RuntimeError, match="git clone failed"):
            install_from_git("https://github.com/user/repo")


def test_install_from_git_nested_tentacle_yaml(tmp_path):
    home = tmp_path / "home"

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[5])
        nested = clone_dir / "packages"
        _write_tentacle_yaml(nested, "nested-tentacle")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        result = install_from_git("https://github.com/user/repo", home=home)
    assert result["name"] == "nested-tentacle"


def test_install_any_with_git_url(tmp_path):
    home = tmp_path / "home"

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[5])
        clone_dir.mkdir(parents=True, exist_ok=True)
        _write_tentacle_yaml(clone_dir, "git-tentacle")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        result = install_any("https://github.com/user/repo", home=home)
    assert result["name"] == "git-tentacle"


def test_install_any_with_local_path(tmp_path):
    src = tmp_path / "src"
    _write_tentacle_yaml(src, "local-tentacle")
    home = tmp_path / "home"
    result = install_any(str(src), home=home)
    assert result["name"] == "local-tentacle"


def test_install_any_with_owner_repo(tmp_path):
    home = tmp_path / "home"

    def mock_run(cmd, **kwargs):
        clone_dir = Path(cmd[5])
        clone_dir.mkdir(parents=True, exist_ok=True)
        _write_tentacle_yaml(clone_dir, "owner-repo-tentacle")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    with patch("subprocess.run", side_effect=mock_run):
        result = install_any("user/repo", home=home)
    assert result["name"] == "owner-repo-tentacle"


def test_spec_by_name_found_in_config(tmp_path, monkeypatch):
    config = {"tentacles": [{"name": "cfg-tentacle", "version": "1.0"}]}
    monkeypatch.setattr("kraken.core.tentacle.load_config", lambda root: config)
    monkeypatch.setattr("kraken.core.tentacle.discover_installed", lambda home: [])
    result = spec_by_name(tmp_path, "cfg-tentacle")
    assert result == {"name": "cfg-tentacle", "version": "1.0"}


def test_spec_by_name_found_in_installed(tmp_path, monkeypatch):
    monkeypatch.setattr("kraken.core.tentacle.load_config", lambda root: {})
    installed = [{"name": "inst-tentacle", "version": "2.0"}]
    monkeypatch.setattr(
        "kraken.core.tentacle.discover_installed", lambda home: installed
    )
    result = spec_by_name(tmp_path, "inst-tentacle")
    assert result == {"name": "inst-tentacle", "version": "2.0"}


def test_spec_by_name_not_found(tmp_path, monkeypatch):
    monkeypatch.setattr("kraken.core.tentacle.load_config", lambda root: {})
    monkeypatch.setattr("kraken.core.tentacle.discover_installed", lambda home: [])
    result = spec_by_name(tmp_path, "nonexistent")
    assert result is None


def test_spec_by_name_config_takes_priority(tmp_path, monkeypatch):
    config = {"tentacles": [{"name": "dup", "version": "cfg"}]}
    monkeypatch.setattr("kraken.core.tentacle.load_config", lambda root: config)
    installed = [{"name": "dup", "version": "inst"}]
    monkeypatch.setattr(
        "kraken.core.tentacle.discover_installed", lambda home: installed
    )
    result = spec_by_name(tmp_path, "dup")
    assert result["version"] == "cfg"


def test_spec_by_name_empty_tentacles_list(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "kraken.core.tentacle.load_config", lambda root: {"tentacles": []}
    )
    monkeypatch.setattr("kraken.core.tentacle.discover_installed", lambda home: [])
    result = spec_by_name(tmp_path, "anything")
    assert result is None


def test_spec_by_name_no_tentacles_key(tmp_path, monkeypatch):
    monkeypatch.setattr("kraken.core.tentacle.load_config", lambda root: {"version": 1})
    monkeypatch.setattr("kraken.core.tentacle.discover_installed", lambda home: [])
    result = spec_by_name(tmp_path, "anything")
    assert result is None


def test_git_url_file_url_is_a_git_ref():
    # The offline story: an air-gapped box installs from a LAN mirror.
    assert _git_url("file:///srv/tentacles/geo") == "file:///srv/tentacles/geo"
    assert _git_url("ssh://git@example.com/t.git") == "ssh://git@example.com/t.git"
    assert _git_url("git://example.com/t.git") == "git://example.com/t.git"
    assert _git_url("http://example.com/t.git") == "http://example.com/t.git"


def test_git_url_local_tentacle_dir_is_not_a_git_ref(tmp_path):
    src = _write_tentacle_yaml(tmp_path / "geo", "geo")
    assert _git_url(str(src.parent)) is None


def test_install_any_from_local_git_mirror(tmp_path):
    repo = tmp_path / "mirror"
    _write_tentacle_yaml(repo, "mirrored", version="9.9.9")
    (repo / "handler.py").write_text(
        "import json,sys\n"
        "req=json.load(sys.stdin)\n"
        "sys.stdout.write(json.dumps({'v':1,'id':req['id'],'ok':True,"
        "'result':{'action':req['action']}}))\n"
    )
    proc = subprocess.run(
        ["git", "init", "-q"], cwd=repo, capture_output=True, check=True
    )
    assert proc.returncode == 0
    for args in (["git", "add", "-A"], ["git", "-c", "user.email=t@t",
                 "-c", "user.name=t", "commit", "-qm", "init"]):
        subprocess.run(args, cwd=repo, capture_output=True, check=True)

    installed = install_any(f"file://{repo}", home=tmp_path / "home")
    assert installed["name"] == "mirrored"
    assert (installed_dir(tmp_path / "home") / "mirrored" / "handler.py").exists()


@NT_SKIP
def test_template_handler_answers_the_envelope(tmp_path):
    """The scaffold every new tentacle starts from must honor the contract.

    A `python3 - <<'PY'` heredoc reads the script from stdin, which starves
    the request: the handler answered with id null and a canned action. The
    template now uses `python3 -c` so stdin stays the envelope.
    """
    template = Path(__file__).resolve().parents[1] / "examples/tentacles/_template"
    home = tmp_path / "home"
    install_local(template, home=home)
    spec = spec_by_name(tmp_path, "hello", home)
    binary = Path(spec["binary"])
    from kraken.core.contract import invoke_binary

    resp = invoke_binary(binary, "ping", {"n": 7}, req_id="tpl-1")
    assert resp["id"] == "tpl-1"
    assert resp["ok"] is True
    assert resp["result"]["action"] == "ping"
