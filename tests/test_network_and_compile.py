from pathlib import Path

from kraken.core.network import resolve_docker
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local

ROOT = Path(__file__).resolve().parents[1]


def test_docker_network_off_by_default(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("KRAKEN_DOCKER_NETWORK", raising=False)
    monkeypatch.delenv("KRAKEN_DOCKER_CONFIG_URL", raising=False)
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    net = resolve_docker({})
    assert net["enabled"] is False
    assert net["name"] == "kraken_dev"
    assert net["public"] is False


def test_docker_network_from_env(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_DOCKER_NETWORK", "lab")
    net = resolve_docker({})
    assert net["enabled"] is True
    assert net["name"] == "kraken_lab"


def test_docker_network_from_url(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    cfg = tmp_path / "net.json"
    cfg.write_text('{"enabled": true, "name": "kraken_ci", "isolated": true}')
    monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", cfg.as_uri())
    net = resolve_docker({})
    assert net["enabled"] is True
    assert net["name"] == "kraken_ci"
    assert net["isolated"] is True
    assert net.get("source")


def test_docker_network_url_fail_closed(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    monkeypatch.setenv("KRAKEN_DOCKER_CONFIG_URL", "file:///no/such/kraken-net.json")
    net = resolve_docker({})
    assert "fetch_error" in net


def test_compile_c_plan_and_finish(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    for name in ("compile-c", "compile-stamp", "compile-tag", "runtime", "docker-env"):
        install_local(ROOT / "examples/tentacles" / name, home=tmp_path)
    plan = run_named(ROOT, "compile-c", "plan", {"inner": {"name": "matt"}})
    assert plan["ok"] is True
    assert plan["result"]["needs_docker"] is True
    assert plan["result"]["network"] == "kraken_dev"
    assert "runtime build" in " ".join(plan["result"]["next"])
    finish = run_named(
        ROOT,
        "compile-c",
        "finish",
        {
            "result": {"hello": "hello, matt", "arm": "hello-c"},
            "patch": {
                "toolchain": "c",
                "compiled": True,
                "image": "kraken-hello-c:local",
                "tag": "local",
            },
        },
    )
    assert finish["ok"] is True
    assert finish["result"]["finished"] is True
    assert finish["result"]["toolchain"] == "c"
    assert finish["result"]["tag"] == "local"


def test_compile_suckers_patch(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(ROOT / "examples/tentacles/compile-stamp", home=tmp_path)
    install_local(ROOT / "examples/tentacles/compile-tag", home=tmp_path)
    stamp = run_named(
        ROOT, "compile-stamp", "convert", {"result": {"hello": "hello, kraken"}}
    )
    tag = run_named(
        ROOT, "compile-tag", "convert", {"result": {"image": "kraken-hello-c:local"}}
    )
    assert stamp["result"]["patch"]["toolchain"] == "c"
    assert tag["result"]["patch"]["tag"] == "local"
