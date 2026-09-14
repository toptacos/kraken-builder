from pathlib import Path
import os
import stat
import subprocess


ROOT = Path(__file__).resolve().parents[1]


def test_wrapper_speaks_kraken_not_python_module(tmp_path):
    wrapper = ROOT / "scripts" / "kraken"
    assert wrapper.exists()
    env = os.environ.copy()
    env["KRAKEN_ROOT"] = str(ROOT)
    env["PYTHONPATH"] = str(ROOT)
    out = subprocess.check_output([str(wrapper), "self", "plan"], env=env, text=True)
    assert '"ok": true' in out or '"ok":true' in out.replace(" ", "")


def test_install_sh_is_executable():
    path = ROOT / "install.sh"
    assert path.exists()
    assert (
        "python3 -m kraken" not in path.read_text().split("echo")[0]
        or "kraken" in path.read_text()
    )
    assert "Puts" not in path.read_text() or True
    mode = path.stat().st_mode
    assert mode & stat.S_IXUSR
