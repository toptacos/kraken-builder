import json
import re
import shutil
from pathlib import Path
import os
import stat
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name == "nt", reason="POSIX wrapper")
def test_wrapper_speaks_kraken_not_python_module(tmp_path):
    wrapper = ROOT / "scripts" / "kraken"
    assert wrapper.exists()
    env = os.environ.copy()
    env["KRAKEN_ROOT"] = str(ROOT)
    env["KRAKEN_SRC"] = str(ROOT)
    env["PYTHONPATH"] = str(ROOT)
    out = subprocess.run(
        [str(wrapper), "self", "plan"], env=env, text=True, capture_output=True
    )
    # Deliberately not `ok: true`. `self plan` mirrors `kraken doctor`, which
    # reflects this machine's install state; a stale pip console script on
    # PATH is a real failure and should not be papered over here.
    assert_resolved(out)


def test_install_sh_is_executable():
    path = ROOT / "install.sh"
    assert path.exists()
    text = path.read_text()
    assert "python3 -m kraken" in text or "kraken" in text
    if os.name != "nt":
        assert path.stat().st_mode & stat.S_IXUSR


def test_module_entry_works():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    out = subprocess.run(
        [sys.executable, "-m", "kraken", "self", "plan"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert_resolved(out)


def _executable_lines(script):
    """Drop comments and heredoc bodies — a warning may *name* a command it
    never runs, and only what reaches the shell counts."""
    out, skipping = [], False
    for line in script.splitlines():
        if skipping:
            if line.strip() in ("MSG", "EOF"):
                skipping = False
            continue
        if re.search(r"<<\s*'?\"?(MSG|EOF)", line):
            skipping = True
            continue
        if line.lstrip().startswith("#"):
            continue
        out.append(line)
    return "\n".join(out)


def run_wrapper(env_extra, *args, home=None, wrapper=None, pythonpath=True):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT) if pythonpath else ""
    env.pop("KRAKEN_SRC", None)
    env.update(env_extra)
    if home:
        env["HOME"] = str(home)
    return subprocess.run(
        [str(wrapper or ROOT / "scripts" / "kraken"), *args],
        env=env,
        text=True,
        capture_output=True,
    )


def assert_resolved(out):
    """The launcher's job is to find the source and hand off. Whether this
    machine's install is healthy is `kraken doctor`'s business, not the
    launcher's — so exit 2 with valid JSON still means resolution worked."""
    assert out.returncode in (0, 2), out.stderr
    assert "cannot find the kraken source tree" not in out.stderr
    assert json.loads(out.stdout)["plan"]["checks"]


def test_launcher_resolves_pointer_file(tmp_path):
    """The pointer written by install.sh is what makes a moved checkout fixable
    with one env var instead of a reinstall."""
    home = tmp_path / "home"
    (home / ".kraken").mkdir(parents=True)
    (home / ".kraken" / "source").write_text(str(ROOT))
    assert_resolved(run_wrapper({}, "self", "plan", home=home))


def test_launcher_honours_kraken_src_over_a_stale_pointer(tmp_path):
    """A pointer written before a checkout moved must not win over an explicit
    KRAKEN_SRC — that is the one-line repair this whole change exists for."""
    home = tmp_path / "home"
    (home / ".kraken").mkdir(parents=True)
    (home / ".kraken" / "source").write_text(str(tmp_path / "moved-away"))
    assert_resolved(run_wrapper({"KRAKEN_SRC": str(ROOT)}, "self", "plan", home=home))


def test_launcher_never_bakes_in_an_absolute_path():
    """The regression that caused `ModuleNotFoundError: No module named
    'kraken'`: the wrapper used to contain the checkout path as a literal, so
    moving the checkout broke every invocation."""
    text = (ROOT / "scripts" / "kraken").read_text()
    assert str(ROOT) not in text
    assert "KRAKEN_SRC" in text


def test_launcher_prints_a_fix_when_source_is_gone(tmp_path):
    """A dead source must produce a named remedy, not a python traceback."""
    home = tmp_path / "home"
    (home / ".kraken").mkdir(parents=True)
    (home / ".kraken" / "source").write_text(str(tmp_path / "moved-away"))
    # Copy the launcher out of the repo so its own directory is not a candidate.
    bindir = tmp_path / "bin"
    bindir.mkdir()
    wrapper = bindir / "kraken"
    wrapper.write_text((ROOT / "scripts" / "kraken").read_text())
    wrapper.chmod(0o755)
    out = run_wrapper({}, "self", "plan", home=home, wrapper=wrapper, pythonpath=False)
    assert out.returncode == 1
    assert "ModuleNotFoundError" not in out.stderr
    assert "cannot find the kraken source tree" in out.stderr
    assert "install.sh" in out.stderr


def test_install_sh_points_the_pointer_and_does_not_pip_install():
    raw = (ROOT / "install.sh").read_text()
    body = _executable_lines(raw)
    assert "$HOME/.kraken/source" in raw
    assert "scripts/kraken" in raw
    # The warning text may *name* `pip install -e .`, but nothing may run it.
    # pyyaml is the single dependency the installer is allowed to install.
    pip_commands = re.findall(r"pip install [^\n'\"]*", body)
    assert pip_commands == ["pip install --user pyyaml >/dev/null"]
    # The old guard was `[ -f "$SRC/kraken/__main__.py" ]`, which passes for a
    # tree that has lost kraken/core.
    assert "kraken/core/cli.py" in body


def test_install_sh_works_when_piped_from_curl(tmp_path):
    """The README installs with `curl … | sh`, where `$0` is `sh` and there is
    no script directory next to it. Deriving the launcher from `$0` produced
    `install: /some/cwd/scripts/kraken: No such file or directory` for every
    user who followed the README — while the test suite, which ran install.sh
    from inside the repo, passed. Piping is the documented path, so pipe it."""
    home = tmp_path / "home"
    src = home / ".kraken" / "src"
    bindir = home / ".local" / "bin"
    src.mkdir(parents=True)
    for part in ("kraken", "examples", "arms", "scripts"):
        shutil.copytree(ROOT / part, src / part)

    env = os.environ.copy()
    env.update(HOME=str(home), KRAKEN_SRC=str(src), KRAKEN_BIN=str(bindir))
    proc = subprocess.run(
        ["sh"],
        stdin=(ROOT / "install.sh").open(),
        env=env,
        text=True,
        capture_output=True,
        cwd=str(tmp_path),  # deliberately NOT the repo, and not $SRC
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "No such file or directory" not in proc.stderr
    installed = bindir / "kraken"
    assert installed.exists()
    assert installed.read_text() == (ROOT / "scripts" / "kraken").read_text()
    # And the launcher it installed must find that same source tree.
    assert (home / ".kraken" / "source").read_text().strip() == str(src)
    out = subprocess.run(
        [str(installed), "self", "plan"],
        env={**env, "PATH": f"{bindir}:{env['PATH']}"},
        text=True,
        capture_output=True,
    )
    assert_resolved(out)


def test_install_sh_fails_loudly_on_an_incomplete_checkout(tmp_path):
    """A tree missing scripts/kraken must name the fix, not die on `install:`."""
    home = tmp_path / "home"
    src = home / ".kraken" / "src"
    bindir = home / ".local" / "bin"
    src.mkdir(parents=True)
    shutil.copytree(ROOT / "kraken", src / "kraken")
    env = os.environ.copy()
    env.update(HOME=str(home), KRAKEN_SRC=str(src), KRAKEN_BIN=str(bindir))
    proc = subprocess.run(
        ["sh"],
        stdin=(ROOT / "install.sh").open(),
        env=env,
        text=True,
        capture_output=True,
        cwd=str(tmp_path),
    )
    assert proc.returncode == 1
    assert "cannot find scripts/kraken" in proc.stdout + proc.stderr
    assert not (bindir / "kraken").exists()


def test_website_serves_the_same_installer():
    """`kraken.topta.co/install.sh` is a copy of this file. When they were two
    real files they drifted, and production kept serving the broken installer
    after the repo was fixed. website/install.sh is a symlink for that reason;
    this fails if anyone converts it back into a copy."""
    served = ROOT / "website" / "install.sh"
    assert served.is_symlink(), "website/install.sh must be a symlink to ../install.sh"
    assert served.resolve() == (ROOT / "install.sh").resolve()
    assert served.read_text() == (ROOT / "install.sh").read_text()


def test_install_wrapper_lives_in_one_place():
    """Every launcher on disk must be the same file, or `kraken` behaves
    differently depending on which one PATH finds."""
    launcher = ROOT / "scripts" / "kraken"
    installed = Path.home() / ".local" / "bin" / "kraken"
    if not installed.exists():
        pytest.skip("launcher not installed on this machine")
    assert installed.read_text() == launcher.read_text(), (
        "run: KRAKEN_SRC=$PWD sh ./install.sh"
    )


def test_version_has_exactly_one_source():
    """0.2.0 and 0.3.0 shipped in the changelog while every build still called
    itself 0.1.1, because the version was written out in five places. Core
    reads `kraken.__version__`; this asserts the packaging metadata agrees."""
    import tomllib

    import kraken
    from kraken.core.resolve import CORE_VERSION

    pkg = tomllib.loads((ROOT / "pyproject.toml").read_text())
    assert pkg["project"]["version"] == kraken.__version__
    assert CORE_VERSION == kraken.__version__

    # No hardcoded version may reappear in core or the examples.
    for path in list((ROOT / "kraken").rglob("*.py")) + list(
        (ROOT / "examples").rglob("*.py")
    ):
        for n, line in enumerate(path.read_text().splitlines(), 1):
            assert not re.search(r"kraken-cli/0\.", line), f"{path}:{n}"
            assert not re.search(r'__version__\s*=\s*"', line) or (
                path == ROOT / "kraken" / "__init__.py"
            ), f"{path}:{n} defines a second __version__"


def test_changelog_has_no_unreleased_section():
    """An Unreleased heading at tag time is how 0.2.0 and 0.3.0 shipped without
    a version bump. The release checklist is this assertion failing."""
    text = (ROOT / "CHANGELOG.md").read_text()
    top = text.split("## ", 2)[1].splitlines()[0]
    assert not top.lower().startswith("unreleased"), f"top section is {top!r}"


def test_doctor_does_not_call_a_symlinked_pointer_stale(tmp_path):
    """macOS `/tmp` is a symlink to `/private/tmp`, so a pointer written by
    install.sh reads back as a different string from the tree python imported.
    Comparing strings made every fresh install report itself stale."""
    from kraken.core.doctor import _same_dir

    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real)
    assert str(link) != str(real.resolve())
    assert _same_dir(link, real)
    assert not _same_dir(link, tmp_path / "elsewhere")
    assert not _same_dir("/nonexistent/xyz", real)


def test_install_pointer_survives_a_symlinked_home(tmp_path):
    """install.sh writes the pointer with whatever SRC the user passed. When
    that is a symlinked path, doctor must still call it current."""
    home = tmp_path / "home"
    (home / ".kraken").mkdir(parents=True)
    (home / ".kraken" / "source").write_text(str(ROOT))
    out = run_wrapper({}, "doctor", home=home, wrapper=None)
    report = json.loads(out.stdout)
    pointer = next(c for c in report["checks"] if c["name"] == "install.pointer")
    assert "stale" not in pointer["detail"]


def test_doctor_reports_which_source_is_running():
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    out = subprocess.run(
        [sys.executable, "-m", "kraken", "doctor"],
        env=env,
        text=True,
        capture_output=True,
    )
    report = json.loads(out.stdout)
    names = {c["name"] for c in report["checks"]}
    assert {
        "install.source",
        "install.revision",
        "install.pip_kraken_cli",
        "install.pointer",
        "install.on_path",
    } <= names
    source = next(c for c in report["checks"] if c["name"] == "install.source")
    assert source["ok"]
    assert source["detail"] == str(ROOT)


def test_doctor_flags_a_competing_pip_install(tmp_path):
    """The exact state that produced `ModuleNotFoundError: No module named
    'kraken'` — a healthy-looking dist-info shadowing a moved checkout."""
    fake = tmp_path / "site-packages"
    fake.mkdir()
    (fake / "kraken_cli-0.1.1.dist-info").mkdir()
    script = (
        "import json, sys;"
        f"sys.path.insert(0, {str(fake)!r});"
        "from kraken.core.doctor import install_checks;"
        "print(json.dumps(install_checks()))"
    )
    out = subprocess.check_output([sys.executable, "-c", script], text=True)
    check = next(c for c in json.loads(out) if c["name"] == "install.pip_kraken_cli")
    assert not check["ok"]
    assert "pip uninstall kraken-cli" in check["detail"]


def test_doctor_survives_a_broken_gitdir(tmp_path):
    """A submodule checkout whose parent moved has a .git *file* pointing at a
    gitdir that is gone. `doctor` must degrade, not raise — it is the command
    people run when things are already broken."""
    import shutil as _shutil

    work = tmp_path / "kraken-builder"
    _shutil.copytree(ROOT / "kraken", work / "kraken")
    (work / ".git").write_text("gitdir: ../../.git/modules/gone\n")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(work)
    out = subprocess.run(
        [sys.executable, "-m", "kraken", "doctor"],
        env=env,
        text=True,
        capture_output=True,
    )
    assert "Traceback" not in out.stderr
    revision = next(
        c for c in json.loads(out.stdout)["checks"] if c["name"] == "install.revision"
    )
    assert revision["ok"]
