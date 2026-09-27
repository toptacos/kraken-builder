import os
import shutil
import subprocess
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
    # Try to build, but skip if compilers not available
    import subprocess as sp
    import platform
    result = sp.run(["bash", str(HW / "build.sh")], check=False, capture_output=True, text=True)
    cases = []
    is_macos = platform.system() == "Darwin"
    is_linux = platform.system() == "Linux"
    for name in ("c", "cpp", "rust", "go"):
        # The build.sh should produce a binary named "hello" in each language directory
        binary = HW / name / "hello"
        # Check if it's a valid executable (not a source file)
        if binary.exists() and binary.is_file() and os.access(binary, os.X_OK):
            # Verify it's actually a binary (not a text file)
            try:
                with open(binary, 'rb') as f:
                    header = f.read(4)
                # Check for ELF magic (Linux) or Mach-O magic (macOS)
                is_elf = header.startswith(b'\x7fELF')
                is_macho = header.startswith(b'\xcf\xfa\xed\xfe') or header.startswith(b'\xfe\xed\xfa\xcf') or header.startswith(b'\xce\xfa\xed\xfe')
                # Skip Linux ELF binaries on macOS and vice versa
                if is_macos and is_elf:
                    continue  # Skip Linux binaries on macOS
                if is_linux and is_macho:
                    continue  # Skip macOS binaries on Linux
                if is_elf or is_macho:
                    dest = tmp_path / f"hello-{name}"
                    dest.write_bytes(binary.read_bytes())
                    dest.chmod(0o755)
                    cases.append((name, dest))
            except Exception:
                pass
    # Check if Java is available (need both javac and java that actually work)
    java_available = False
    if shutil.which("javac") and shutil.which("java"):
        try:
            result = sp.run(["java", "-version"], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                java_available = True
        except Exception:
            pass
    if (HW / "java" / "run.sh").exists() and java_available:
        cases.append(("java", HW / "java" / "run.sh"))
    if not cases:
        import pytest
        pytest.skip("No compiled binaries available (compilers not installed)")
    for name, binary in cases:
        # For shell scripts (java run.sh), invoke_binary may not work directly
        if str(binary).endswith("run.sh"):
            # Run the shell script directly
            proc = sp.run([str(binary), "hello", '{"name": "kraken"}'], capture_output=True, text=True)
            assert proc.returncode == 0
            assert "hello" in proc.stdout
        else:
            # Check if it's a valid binary before invoking
            try:
                with open(binary, 'rb') as f:
                    header = f.read(4)
                is_elf = header.startswith(b'\x7fELF')
                is_macho = header.startswith(b'\xcf\xfa\xed\xfe') or header.startswith(b'\xfe\xed\xfa\xcf') or header.startswith(b'\xce\xfa\xed\xfe')
                if not (is_elf or is_macho):
                    continue  # Skip non-binary files
                # Skip incompatible platform binaries
                if is_macos and is_elf:
                    continue
                if is_linux and is_macho:
                    continue
            except Exception:
                continue
            out = invoke_binary(binary, "hello", {"name": "kraken"})
            assert out.get("ok") is True
            assert "hello" in str(out.get("result") or out)