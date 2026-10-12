import subprocess
from pathlib import Path

import pytest

import kraken
from kraken.core.doctor import _git, _same_dir, inspect, install_checks, next_actions

ROOT = Path(__file__).resolve().parents[1]


def test_git_success(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 0, stdout="abc1234\n", stderr="")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    assert _git(Path("/tmp"), "rev-parse") == "abc1234"


def test_git_nonzero_return(monkeypatch):
    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 1, stdout="", stderr="error")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    assert _git(Path("/tmp"), "rev-parse") == ""


def test_git_oserror(monkeypatch):
    def fake_run(*args, **kwargs):
        raise OSError("no git")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    assert _git(Path("/tmp"), "rev-parse") == ""


def test_git_subprocess_error(monkeypatch):
    def fake_run(*args, **kwargs):
        raise subprocess.SubprocessError("boom")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    assert _git(Path("/tmp"), "rev-parse") == ""


def test_same_dir_identical(tmp_path):
    assert _same_dir(str(tmp_path), str(tmp_path)) is True


def test_same_dir_different(tmp_path):
    assert _same_dir(str(tmp_path), str(tmp_path / "other")) is False


def test_same_dir_oserror(monkeypatch):
    def fake_resolve(self):
        raise OSError("boom")

    monkeypatch.setattr(Path, "resolve", fake_resolve)
    assert _same_dir("/a", "/b") is False


def test_install_checks_basic(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "source_pointer")
    (tmp_path / "source_pointer").write_text("")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)
    checks = install_checks()
    names = [c["name"] for c in checks]
    assert "install.source" in names
    assert "install.revision" in names
    assert "install.pip_kraken_cli" in names
    assert "install.pointer" in names
    assert "install.on_path" in names
    pointer_check = next(c for c in checks if c["name"] == "install.pointer")
    assert "absent" in pointer_check["detail"]
    on_path_check = next(c for c in checks if c["name"] == "install.on_path")
    assert on_path_check["ok"] is False


def test_install_checks_pointer_matching(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    pkg = Path(kraken.__file__).resolve().parent
    root = pkg.parent
    pointer = tmp_path / "source_pointer"
    pointer.write_text(str(root))
    monkeypatch.setattr("kraken.core.doctor.POINTER", pointer)
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)
    checks = install_checks()
    pointer_check = next(c for c in checks if c["name"] == "install.pointer")
    assert pointer_check["ok"] is True
    assert "→" in pointer_check["detail"]


def test_install_checks_pointer_stale(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    pointer = tmp_path / "source_pointer"
    pointer.write_text("/nonexistent/path")
    monkeypatch.setattr("kraken.core.doctor.POINTER", pointer)
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)
    checks = install_checks()
    pointer_check = next(c for c in checks if c["name"] == "install.pointer")
    assert "stale" in pointer_check["detail"]


def test_install_checks_pointer_read_error(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "nonexistent_pointer")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)
    checks = install_checks()
    pointer_check = next(c for c in checks if c["name"] == "install.pointer")
    assert "absent" in pointer_check["detail"]


def test_install_checks_stale_dist_info(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    stale_dir = tmp_path / "kraken_cli-1.0.0.dist-info"
    stale_dir.mkdir()
    monkeypatch.setattr("kraken.core.doctor.sys.path", [str(tmp_path)])
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)
    checks = install_checks()
    pip_check = next(c for c in checks if c["name"] == "install.pip_kraken_cli")
    assert pip_check["ok"] is False
    assert "kraken_cli" in pip_check["detail"]


def test_install_checks_on_path_found(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr(
        "kraken.core.doctor.shutil.which", lambda name: f"/usr/local/bin/{name}"
    )
    checks = install_checks()
    on_path_check = next(c for c in checks if c["name"] == "install.on_path")
    assert on_path_check["ok"] is True
    assert "kraken" in on_path_check["detail"]


def test_install_checks_on_path_partial(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr(
        "kraken.core.doctor.shutil.which",
        lambda name: "/usr/bin/kraken" if name == "kraken" else None,
    )
    checks = install_checks()
    on_path_check = next(c for c in checks if c["name"] == "install.on_path")
    assert "not found: k" in on_path_check["detail"]


def test_install_checks_git_commit_clean(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)

    def fake_run(*args, **kwargs):
        if "rev-parse" in args[0]:
            return subprocess.CompletedProcess(args, 0, stdout="abc1234\n", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="", stderr="")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    checks = install_checks()
    rev_check = next(c for c in checks if c["name"] == "install.revision")
    assert "abc1234" in rev_check["detail"]
    assert "dirty" not in rev_check["detail"]


def test_install_checks_git_commit_dirty(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)

    def fake_run(*args, **kwargs):
        if "rev-parse" in args[0]:
            return subprocess.CompletedProcess(args, 0, stdout="abc1234\n", stderr="")
        return subprocess.CompletedProcess(args, 0, stdout="M file.py\n", stderr="")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    checks = install_checks()
    rev_check = next(c for c in checks if c["name"] == "install.revision")
    assert "dirty" in rev_check["detail"]


def test_install_checks_not_git_checkout(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setattr("kraken.core.doctor.POINTER", tmp_path / "p")
    (tmp_path / "p").write_text("")
    monkeypatch.setattr("kraken.core.doctor.shutil.which", lambda name: None)

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args, 128, stdout="", stderr="not a repo")

    monkeypatch.setattr("kraken.core.doctor.subprocess.run", fake_run)
    checks = install_checks()
    rev_check = next(c for c in checks if c["name"] == "install.revision")
    assert "not a git checkout" in rev_check["detail"]


def test_next_actions_with_install_failures(tmp_path):
    checks = [{"name": "install.pointer", "ok": False, "detail": "stale"}]
    steps = next_actions(tmp_path, installed=["geo", "filesort"], checks=checks)
    assert any("repair" in s for s in steps)


def test_next_actions_without_install_failures(tmp_path):
    checks = [{"name": "install.pointer", "ok": True, "detail": "fine"}]
    steps = next_actions(tmp_path, installed=["geo", "filesort"], checks=checks)
    assert not any("repair" in s for s in steps)


def test_next_actions_missing_geo(tmp_path):
    steps = next_actions(tmp_path, installed=["filesort"], checks=[])
    assert any("geo" in s for s in steps)


def test_next_actions_missing_filesort(tmp_path):
    steps = next_actions(tmp_path, installed=["geo"], checks=[])
    assert any("filesort" in s for s in steps)


def test_next_actions_all_present(tmp_path):
    steps = next_actions(tmp_path, installed=["geo", "filesort"], checks=[])
    assert not any("tentacle add" in s for s in steps)
    assert any("grant expose" in s for s in steps)
    assert any("docs:" in s for s in steps)


def test_next_actions_discovers_installed(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    steps = next_actions(tmp_path, installed=None, checks=[])
    assert isinstance(steps, list)
    assert len(steps) > 0


def test_inspect_full(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    report = inspect(ROOT)
    assert "checks" in report
    assert "ok" in report
    assert "home" in report
    assert "next" in report
    names = [c["name"] for c in report["checks"]]
    assert "protocol" in names
    assert "core" in names
    assert "licenses.keys" in names
    assert "catalog" in names
    assert any(n.startswith("layout.") for n in names)


def test_inspect_with_unresolvable_tentacle(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    from kraken.core.tentacle import install_local

    bad = tmp_path / "bad-tentacle"
    bad.mkdir()
    (bad / "tentacle.yaml").write_text(
        "name: bad-tentacle\nversion: 1.0.0\nrequires:\n  tentacles:\n    nonexistent: '*'\n"
    )
    install_local(bad, home=tmp_path)
    report = inspect(ROOT)
    plan_checks = [c for c in report["checks"] if c["name"] == "plan.bad-tentacle"]
    assert len(plan_checks) == 1
    assert plan_checks[0]["ok"] is False


def test_editable_install_pointing_here_is_not_a_shadow(tmp_path, monkeypatch):
    """`pip install -e .` is the documented dev setup and what CI does; the
    dist-info it leaves must not read as a competing install. This check
    failed on every CI run for that reason before 2026-10-11."""
    import json

    from kraken.core import doctor as doctor_mod

    dist = tmp_path / "site" / "kraken_cli-0.3.1.dist-info"
    dist.mkdir(parents=True)
    # as_uri() writes file:///C:/... on Windows; hand-building file:// +
    # str(path) drops the third slash and url2pathname reads the result as
    # the current directory.
    (dist / "direct_url.json").write_text(
        json.dumps({"url": tmp_path.as_uri()})
    )
    root = tmp_path
    assert doctor_mod._same_dir(tmp_path, root) is True
    assert doctor_mod._direct_url_dir(dist) == tmp_path


def test_foreign_pip_install_still_fails(tmp_path):
    import json

    from kraken.core import doctor as doctor_mod

    dist = tmp_path / "site" / "kraken_cli-0.3.1.dist-info"
    dist.mkdir(parents=True)
    (dist / "direct_url.json").write_text(
        json.dumps({"url": "file:///some/other/checkout"})
    )
    target = doctor_mod._direct_url_dir(dist)
    assert target is not None
    assert doctor_mod._same_dir(target, tmp_path) is False
