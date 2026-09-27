from pathlib import Path

from kraken.core.runner import list_all, run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]


def test_pi_filesort_sites(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    for name in ("pi-net", "filesort", "sites"):
        install_local(ROOT / "examples" / "tentacles" / name, home=tmp_path)

    add = run_named(ROOT, "pi-net", "add", {"host": "127.0.0.1", "user": "pi"})
    assert add["ok"]
    disc = run_named(ROOT, "pi-net", "discover", {"hosts": ["127.0.0.1"]})
    assert disc["result"]["found"][0]["reachable"] is True

    sample = tmp_path / "tree"
    sample.mkdir()
    (sample / "a.txt").write_text("same")
    (sample / "b.txt").write_text("same")
    (sample / "c.py").write_text("other")
    scan = run_named(ROOT, "filesort", "scan", {"path": str(sample)})
    assert scan["result"]["indexed"] == 3
    dups = run_named(ROOT, "filesort", "dups", {})
    assert dups["result"]["count"] == 1

    demo = ROOT / "examples" / "sites-demo"
    plan = run_named(ROOT, "sites", "plan", {"project": str(demo)})
    assert "kraken_sites" in plan["result"]["yaml"]
    assert "127.0.0.1:8081" in plan["result"]["yaml"]


def test_list_includes_platform_flags(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(ROOT / "examples" / "tentacles" / "filesort", home=tmp_path)
    rows = {r["name"]: r for r in list_all(ROOT)}
    assert "platforms" in rows["echo"]
    assert rows["filesort"]["needs_docker"] is False
