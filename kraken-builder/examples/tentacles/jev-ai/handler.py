#!/usr/bin/env python3
"""Jev JSON editor + local secure AI models (Ollama/llama.cpp).

Actions:
  edit   - Edit JSON data using Jev-style path operations (get/set/delete/merge)
  learn  - Feed data to a local AI model for learning (Ollama/llama.cpp)
  infer  - Run inference on a local AI model with a prompt
  status - Check availability of Jev and local AI backends
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _ok(req: dict, result: dict, ok: bool = True) -> int:
    sys.stdout.write(
        json.dumps({"v": 1, "id": req.get("id"), "ok": ok, "result": result})
    )
    return 0


def _home() -> Path:
    raw = os.environ.get("KRAKEN_HOME")
    base = Path(raw) if raw else Path.home()
    d = base / ".kraken" / "data" / "jev-ai"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _check_ollama() -> dict[str, Any]:
    """Check if Ollama is available and list models."""
    exe = shutil.which("ollama")
    if not exe:
        return {"available": False, "reason": "ollama binary not found"}
    try:
        proc = subprocess.run(
            [exe, "list"], capture_output=True, timeout=10, check=False
        )
        if proc.returncode != 0:
            return {"available": False, "reason": "ollama list failed"}
        lines = proc.stdout.decode("utf-8", "replace").strip().split("\n")[1:]
        models = []
        for line in lines:
            parts = line.split()
            if parts:
                models.append({"name": parts[0], "size": parts[-1] if len(parts) > 1 else ""})
        return {"available": True, "models": models}
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        return {"available": False, "reason": str(exc)}


def _check_llamacpp() -> dict[str, Any]:
    """Check if llama.cpp server is available."""
    exe = shutil.which("llama-server")
    if not exe:
        return {"available": False, "reason": "llama-server binary not found"}
    return {"available": True, "binary": exe}


def _check_jev() -> dict[str, Any]:
    """Check if Jev (JSON editor) is available."""
    # Jev is a Python package; check if it's importable
    try:
        import importlib
        importlib.import_module("jev")
        return {"available": True, "type": "python-package"}
    except ImportError:
        pass
    # Check for jev binary
    exe = shutil.which("jev")
    if exe:
        return {"available": True, "type": "binary", "path": exe}
    return {"available": False, "reason": "jev not installed"}


def _jev_edit(data: Any, operations: list[dict]) -> Any:
    """Apply Jev-style path operations to JSON data.

    Operations:
      {"op": "set", "path": "a.b.c", "value": ...}
      {"op": "get", "path": "a.b.c"}
      {"op": "delete", "path": "a.b.c"}
      {"op": "merge", "path": "a.b", "value": {...}}
    """
    result = data
    for op in operations:
        path = op.get("path", "")
        action = op.get("op", "get")
        keys = path.split(".") if path else []

        if action == "get":
            node = result
            for k in keys:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    return None
            return node

        elif action == "set":
            node = result
            for k in keys[:-1]:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    node[k] = {}
                    node = node[k]
            if keys:
                node[keys[-1]] = op.get("value")
            else:
                result = op.get("value")

        elif action == "delete":
            node = result
            for k in keys[:-1]:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    break
            else:
                if keys and isinstance(node, dict) and keys[-1] in node:
                    del node[keys[-1]]

        elif action == "merge":
            node = result
            for k in keys:
                if isinstance(node, dict) and k in node:
                    node = node[k]
                else:
                    node[k] = {}
                    node = node[k]
            if isinstance(node, dict) and isinstance(op.get("value"), dict):
                node.update(op["value"])

    return result


def _ollama_infer(prompt: str, model: str = "llama3", temperature: float = 0.7) -> str:
    """Run inference via Ollama."""
    exe = shutil.which("ollama")
    if not exe:
        raise FileNotFoundError("ollama binary not found")
    proc = subprocess.run(
        [exe, "run", model, prompt],
        capture_output=True,
        timeout=120,
        check=False,
        input="",
        text=True,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"ollama run failed: {proc.stderr[:400]}")
    return proc.stdout.strip()


def _llamacpp_infer(prompt: str, model_path: str, temperature: float = 0.7) -> str:
    """Run inference via llama.cpp server (HTTP API)."""
    import urllib.request
    import urllib.error

    url = "http://127.0.0.1:8080/completion"
    payload = json.dumps({
        "prompt": prompt,
        "temperature": temperature,
        "model": model_path,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("content", "")
    except urllib.error.URLError as exc:
        raise RuntimeError(f"llama.cpp server not reachable: {exc}")


def main() -> int:
    req = json.loads(sys.stdin.read() or "{}")
    action = req.get("action") or "status"
    p = req.get("payload") or {}
    home = _home()

    if action == "status":
        return _ok(req, {
            "jev": _check_jev(),
            "ollama": _check_ollama(),
            "llamacpp": _check_llamacpp(),
            "data_dir": str(home),
        })

    if action == "edit":
        # Load or accept JSON data
        if "data" in p:
            data = p["data"]
        elif "file" in p:
            data = json.loads(Path(p["file"]).read_text())
        else:
            # Load from stored file
            store = home / "data.json"
            if store.exists():
                data = json.loads(store.read_text())
            else:
                data = {}

        operations = p.get("operations", [])
        if not operations:
            return _ok(req, {"error": "no operations provided"}, ok=False)

        result = _jev_edit(data, operations)

        # Save if requested
        if p.get("save"):
            store = home / "data.json"
            store.write_text(json.dumps(result, indent=2))
            return _ok(req, {"result": result, "saved": True, "path": str(store)})

        return _ok(req, {"result": result})

    if action == "learn":
        # Feed data to a local AI model for learning
        backend = p.get("backend", "ollama")
        model = p.get("model", "llama3")
        data = p.get("data", "")
        prompt = p.get("prompt", f"Analyze and learn from the following data: {json.dumps(data) if isinstance(data, (dict, list)) else data}")

        if backend == "ollama":
            try:
                output = _ollama_infer(prompt, model, p.get("temperature", 0.7))
                return _ok(req, {"backend": "ollama", "model": model, "output": output})
            except (FileNotFoundError, RuntimeError) as exc:
                return _ok(req, {"error": str(exc)}, ok=False)
        elif backend == "llamacpp":
            try:
                output = _llamacpp_infer(prompt, model, p.get("temperature", 0.7))
                return _ok(req, {"backend": "llamacpp", "model": model, "output": output})
            except (FileNotFoundError, RuntimeError) as exc:
                return _ok(req, {"error": str(exc)}, ok=False)
        else:
            return _ok(req, {"error": f"unknown backend: {backend}"}, ok=False)

    if action == "infer":
        # Run inference on a local AI model
        backend = p.get("backend", "ollama")
        model = p.get("model", "llama3")
        prompt = p.get("prompt", "")

        if not prompt:
            return _ok(req, {"error": "no prompt provided"}, ok=False)

        if backend == "ollama":
            try:
                output = _ollama_infer(prompt, model, p.get("temperature", 0.7))
                return _ok(req, {"backend": "ollama", "model": model, "output": output})
            except (FileNotFoundError, RuntimeError) as exc:
                return _ok(req, {"error": str(exc)}, ok=False)
        elif backend == "llamacpp":
            try:
                output = _llamacpp_infer(prompt, model, p.get("temperature", 0.7))
                return _ok(req, {"backend": "llamacpp", "model": model, "output": output})
            except (FileNotFoundError, RuntimeError) as exc:
                return _ok(req, {"error": str(exc)}, ok=False)
        else:
            return _ok(req, {"error": f"unknown backend: {backend}"}, ok=False)

    return _ok(req, {"error": f"unknown action {action}"}, ok=False)


if __name__ == "__main__":
    raise SystemExit(main())
