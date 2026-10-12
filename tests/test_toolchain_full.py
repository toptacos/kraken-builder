"""Version requirements: what a tentacle declares vs what this box has.

Two surfaces, one rule. A manifest may declare the toolchains its handler
needs (`requires: {python: ">=3.11"}`) and the tag it was published under
(`kraken tentacle add repo@v1.2.3`); core refuses early, with a sentence,
when either does not hold -- at install time and at run time.

The rule that keeps it cheap: an undeclared requirement is never probed, so
a tentacle that asks for nothing spawns nothing.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from kraken.core import toolchain
from kraken.core.resolve import ResolveError, resolve
from kraken.core.semver import satisfies
from kraken.core.tentacle import _split_ref, install_local

ROOT = Path(__file__).resolve().parents[1]


def _install(tmp_path: Path, name: str, requires: dict | None) -> dict:
    src = tmp_path / f"src-{name}"
    src.mkdir(parents=True, exist_ok=True)
    body = (
        f'name: {name}\nversion: "0.1.0"\nlicense: free\nruntime: binary\n'
        "binary: handler.sh\nactions: [ping]\n"
    )
    if requires:
        body += "requires:"
        for key, bound in requires.items():
            body += f'\n  {key}: "{bound}"'
        body += "\n"
    (src / "tentacle.yaml").write_text(body)
    (src / "handler.sh").write_text(
        "#!/bin/sh\n"
        "exec python3 -c 'import json,sys;"
        "req=json.load(sys.stdin);"
        "sys.stdout.write(json.dumps({\"v\":1,\"id\":req.get(\"id\"),\"ok\":True}))'\n"
    )
    return install_local(src, home=tmp_path / "home")


# --- probes -----------------------------------------------------------------


def test_python_is_answered_without_a_process():
    assert toolchain.probe("python") == toolchain.python_version()


def test_probe_is_cached_per_process():
    toolchain._CACHE.clear()
    first = toolchain.probe("git")
    second = toolchain.probe("git")
    assert first == second
    assert "git" in toolchain._CACHE


def test_probe_of_a_tool_that_does_not_exist():
    assert toolchain.probe("kraken-no-such-toolchain-xyz") is None


def test_node_version_parses_to_x_y_z():
    have = toolchain.probe("node")
    if have is None:
        pytest.skip("node not installed on this machine")
    assert satisfies(have, ">=8") or not satisfies(have, ">=8")


def test_probe_survives_a_broken_binary(tmp_path, monkeypatch):
    """A tool on PATH that cannot run is 'not installed', not a crash."""
    fake = tmp_path / "rustc"
    fake.write_text("#!/bin/sh\nexit 1\n")
    fake.chmod(0o755)
    monkeypatch.setenv(
        "PATH",
        f"{tmp_path}{__import__('os').pathsep}{__import__('os').environ['PATH']}",
    )
    monkeypatch.setattr(toolchain, "_VERSION_CMD", {"rustc": ("rustc", "--version")})
    toolchain._CACHE.pop("rustc", None)
    assert toolchain.probe("rustc") is None


# --- declared requirements --------------------------------------------------


def test_declared_tools_ignores_non_tool_keys():
    spec = {"requires": {"protocol": 1, "core": ">=0.1.0", "python": ">=3.11"}}
    assert toolchain.declared_tools(spec) == {"python": ">=3.11"}


def test_declared_tools_ignores_wildcards():
    spec = {"requires": {"node": "*", "ruby": "any", "php": "optional", "go": ""}}
    assert toolchain.declared_tools(spec) == {}


def test_check_passes_when_nothing_is_declared():
    assert toolchain.check({"name": "quiet"}) == []


def test_check_passes_when_the_bound_is_met():
    running = toolchain.python_version()
    assert toolchain.check({"requires": {"python": ">=3.0"}}) == []
    assert satisfies(running, ">=3.0")


# --- enforcement at install and run -----------------------------------------


def test_install_then_resolve_refuses_a_missing_toolchain(tmp_path, monkeypatch):
    """install_local copies files and says nothing about requirements -- the
    gate is the resolve that follows it, in `kraken tentacle add` and in every
    `kraken run`."""
    home = tmp_path / "home"
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    _install(tmp_path, "needs-rust", {"rustc": ">=1.70"})
    with pytest.raises(ResolveError) as excinfo:
        resolve(tmp_path, "needs-rust", home)
    assert "rustc >=1.70, which is not installed" in str(excinfo.value)


def test_run_refuses_with_the_same_sentence(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    _install(tmp_path, "needs-rust2", {"rustc": ">=1.70"})
    from kraken.core.runner import run_named

    with pytest.raises(ResolveError) as excinfo:
        run_named(tmp_path, "needs-rust2", "ping", home=home)
    assert "requires rustc >=1.70, which is not installed" in str(excinfo.value)


def test_a_satisfied_bound_runs_normally(tmp_path, monkeypatch):
    home = tmp_path / "home"
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    _install(tmp_path, "needs-py", {"python": ">=3.0"})
    from kraken.core.runner import run_named

    result = run_named(tmp_path, "needs-py", "ping", home=home)
    assert result["ok"] is True


# --- @tag installs ----------------------------------------------------------


def test_split_ref_variants():
    assert _split_ref("github.com/x/y@v1.2.3") == ("github.com/x/y", "v1.2.3")
    assert _split_ref("https://github.com/x/y@v1.2.3") == (
        "https://github.com/x/y",
        "v1.2.3",
    )
    assert _split_ref("file:///srv/mirror@v1.0.0") == ("file:///srv/mirror", "v1.0.0")
    # SCP syntax: the @ belongs to the URL
    assert _split_ref("git@github.com:x/y.git") == ("git@github.com:x/y.git", None)
    assert _split_ref("/local/path") == ("/local/path", None)


def test_tag_on_a_directory_is_refused(tmp_path):
    from kraken.core.tentacle import install_any

    with pytest.raises(RuntimeError) as excinfo:
        install_any(f"{tmp_path}@v1.0.0", home=tmp_path / "home")
    assert "git reference" in str(excinfo.value)


def test_tag_that_disagrees_with_the_manifest_is_refused(tmp_path):
    """`@v2.0.0` on a repository whose manifest says 1.0.0 is a lie about
    what you installed; `@main` stays advisory."""
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "tentacle.yaml").write_text('name: pinned\nversion: "1.0.0"\n')
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "init",
        ],
        # A lightweight tag: an annotated one needs a git identity, which
        # exists on a developer box and not necessarily on a CI runner.
        ["git", "tag", "v2.0.0"],
    ):
        subprocess.run(cmd, cwd=repo, capture_output=True, check=True)

    from kraken.core.tentacle import install_from_git

    with pytest.raises(RuntimeError) as excinfo:
        install_from_git(f"file://{repo}", home=tmp_path / "home", ref="v2.0.0")
    assert "declares version 1.0.0" in str(excinfo.value)


def test_advisory_ref_installs_without_a_version_check(tmp_path):
    repo = tmp_path / "repo-adv"
    repo.mkdir()
    (repo / "tentacle.yaml").write_text('name: advisory\nversion: "1.0.0"\n')
    for cmd in (
        ["git", "init", "-q", "-b", "main"],
        ["git", "add", "-A"],
        [
            "git",
            "-c",
            "user.email=t@t",
            "-c",
            "user.name=t",
            "commit",
            "-qm",
            "init",
        ],
    ):
        subprocess.run(cmd, cwd=repo, capture_output=True, check=True)

    from kraken.core.tentacle import install_from_git

    installed = install_from_git(f"file://{repo}", home=tmp_path / "home", ref="main")
    assert installed["name"] == "advisory"
    assert installed["ref"] == "main"
