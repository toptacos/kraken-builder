import os
from pathlib import Path

from kraken.core.contract import invoke_binary
from kraken.core.scopes import active_catalog, set_scope, use_scope


ROOT = Path(__file__).resolve().parents[1]

CA = ROOT / "examples" / "tentacles" / "ca" / "handler.py"


def test_org_scope_key_stays_local(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = set_scope("work", key="kk_test_org", sites=["panel"])
    assert out["ok"] is True
    store = tmp_path / ".kraken" / "keys" / "scopes.json"
    assert store.exists()
    if os.name != "nt":
        assert oct(store.stat().st_mode)[-3:] == "600"
    cat = active_catalog()
    assert cat["active"] == "work"
    assert "kk_test_org" not in str(cat)
    switched = use_scope("global")
    assert switched["active"] == "global"


def test_ca_is_tentacle_plan(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    out = invoke_binary(CA, "plan", {"host": "panel.kraken.localhost"})
    assert out["ok"] is True
    assert "data/ca" in out["result"]["dir"].replace("\\", "/")
    assert Path(out["result"]["cert"]).exists()
    assert out["result"]["public"] is False


def test_kraken_home_pointed_at_the_kraken_dir_warns():
    """KRAKEN_HOME is the home directory; .kraken is appended to it. Setting it
    to `~/.kraken` silently nests everything one level deeper. This bit the
    contract sweep's own harness before it was guarded."""
    import subprocess
    import sys

    script = (
        "from kraken.core.paths import user_home, user_kraken;"
        "print(user_kraken())"
    )
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    env.pop("KRAKEN_HOME", None)

    nested = subprocess.run(
        [sys.executable, "-c", script],
        env={**env, "KRAKEN_HOME": "/tmp/x/.kraken"},
        capture_output=True,
        text=True,
    )
    assert "/tmp/x/.kraken/.kraken" in nested.stdout
    assert "KRAKEN_HOME" in nested.stderr
    assert "is the home directory" in nested.stderr

    correct = subprocess.run(
        [sys.executable, "-c", script],
        env={**env, "KRAKEN_HOME": "/tmp/x"},
        capture_output=True,
        text=True,
    )
    assert correct.stdout.strip().endswith("/tmp/x/.kraken")
    assert correct.stderr == ""


def test_home_kraken_is_not_also_a_project_scope(tmp_path, monkeypatch):
    """Running from inside the home directory used to put ~/.kraken in the
    chain twice: once as the user scope, and again as a "project" scope that
    outranks it. CI hit this for real -- its earlier steps create ~/.kraken,
    and every 'sandboxed' config test then read it as project config."""
    home = tmp_path / "home"
    work = home / "proj"
    (home / ".kraken").mkdir(parents=True)
    (work / ".kraken").mkdir(parents=True)
    monkeypatch.setenv("KRAKEN_HOME", str(home))
    monkeypatch.chdir(work)

    from kraken.core.config_chain import chain_files, scope_of
    from kraken.core.paths import config_chain

    dirs = [d for d in config_chain()]
    scopes = [scope_of(d) for d in dirs]
    assert scopes.count("user") == 1
    assert scopes.count("project") == 1, scopes
    # the project entry is the one in proj/, not a second copy of ~/.kraken
    projects = [d for d in dirs if scope_of(d) == "project"]
    assert projects[0] == work / ".kraken"
    assert [s for s, _, _ in chain_files()] == scopes
