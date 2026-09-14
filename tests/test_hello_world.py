import shutil
from pathlib import Path

from kraken.core.contract import invoke_binary
from kraken.core.runner import run_named
from kraken.core.tentacle import install_local


ROOT = Path(__file__).resolve().parents[1]
HW = ROOT / "examples" / "tentacles" / "hello-world"

SCRIPTS = [
    ("hello-py", HW / "python"),
    ("hello-sh", HW / "bash"),
    ("hello-js", HW / "js"),
    ("hello-php", HW / "php"),
    ("hello-rb", HW / "ruby"),
    ("hello-pl", HW / "perl"),
    ("hello-go", HW / "go"),
]


def test_script_hellos(tmp_path, monkeypatch):
    monkeypatch.setenv("KRAKEN_HOME", str(tmp_path))
    need = {
        "hello-js": "node",
        "hello-php": "php",
        "hello-rb": "ruby",
        "hello-pl": "perl",
        "hello-go": "go",
    }
    ran = 0
    for name, src in SCRIPTS:
        exe = need.get(name)
        if exe and not shutil.which(exe):
            continue
        install_local(src, home=tmp_path)
        out = run_named(ROOT, name, "hello", {"name": "kraken"})
        assert out["ok"] is True
        assert "kraken" in str(out["result"]["hello"])
        ran += 1
    assert ran >= 3


def test_compiled_c_cpp_rust_java(tmp_path):
    import subprocess

    subprocess.run(["bash", str(HW / "build.sh")], check=False)
    cases = []
    for name in ("c", "cpp", "rust"):
        src = HW / name / "hello"
        if src.exists():
            dest = tmp_path / f"hello-{name}"
            dest.write_bytes(src.read_bytes())
            dest.chmod(0o755)
            cases.append(dest)
    if (HW / "java" / "run.sh").exists() and shutil.which("java"):
        cases.append(HW / "java" / "run.sh")
    assert cases
    for binary in cases:
        out = invoke_binary(binary, "hello", {"name": "kraken"})
        assert out.get("ok") is True
        assert "hello" in str(out.get("result") or out)
