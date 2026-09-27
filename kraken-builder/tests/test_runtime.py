from pathlib import Path

from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]
RT = ROOT / "examples" / "tentacles" / "runtime"
DF = ROOT / "examples" / "tentacles" / "hello-world" / "c" / "Dockerfile"


def test_runtime_plan_and_dry_invoke(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    install_local(RT, home=tmp_path)
    plan = run_named(
        ROOT,
        "runtime",
        "plan",
        {
            "dockerfile": str(DF),
            "image": "kraken-hello-c:local",
            "services": {"upload": {"uri": "local://store"}},
        },
    )
    assert plan["ok"] is True
    assert plan["result"]["argv"][0] == "docker"
    argv = plan["result"]["argv"]
    assert "/kraken/data:ro" in str(argv)
    assert "--security-opt" in argv
    assert plan["result"]["network"].startswith("kraken_")
    inv = run_named(
        ROOT,
        "runtime",
        "invoke",
        {"image": "kraken-hello-c:local", "inner": {"name": "kraken"}},
    )
    assert inv["ok"] is True
    assert inv["result"]["mode"] in {"dry-run", "docker"}
    pub = run_named(ROOT, "runtime", "publish", {"services": {"upload": {"uri": "s3://bucket/out"}}})
    assert pub["result"]["published"] == "s3://bucket/out"
