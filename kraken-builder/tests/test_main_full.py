import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_kraken(*args, extra_env=None):
    env = {**os.environ, "PYTHONPATH": str(ROOT)}
    env.pop("KRAKEN_HOME", None)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        [sys.executable, "-m", "kraken", *args],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(ROOT),
    )


def test_main_no_args_exits_2():
    proc = run_kraken()
    assert proc.returncode == 2


def test_main_help_exits_0():
    proc = run_kraken("--help")
    assert proc.returncode == 0
    assert "usage" in proc.stdout.lower()


def test_main_unknown_command_exits_2():
    proc = run_kraken("not-a-command")
    assert proc.returncode == 2


def test_main_doctor(tmp_path):
    proc = run_kraken("doctor", extra_env={"KRAKEN_HOME": str(tmp_path)})
    assert proc.returncode in (0, 2)


def test_main_init(tmp_path):
    proc = run_kraken("init", extra_env={"KRAKEN_HOME": str(tmp_path)})
    assert proc.returncode == 0
    assert (tmp_path / ".kraken").is_dir()


def test_main_list(tmp_path):
    proc = run_kraken("list", extra_env={"KRAKEN_HOME": str(tmp_path)})
    assert proc.returncode == 0
