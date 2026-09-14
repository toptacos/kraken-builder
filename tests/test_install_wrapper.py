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
    env["PYTHONPATH"] = str(ROOT)
    out = subprocess.check_output([str(wrapper), "self", "plan"], env=env, text=True)
    assert '"ok": true' in out or '"ok":true' in out.replace(" ", "")


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
    out = subprocess.check_output(
        [sys.executable, "-m", "kraken", "self", "plan"], env=env, text=True
    )
    assert '"ok"' in out
