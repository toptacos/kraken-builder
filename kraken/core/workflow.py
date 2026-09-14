"""Declarative workflows: sequential steps and parallel groups.

Each step is a tentacle invoke. Later payloads may reference prior results
with $step_id or $step_id.result.field.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import yaml

from kraken.core.notify import emit
from kraken.core.runner import run_named


class WorkflowError(ValueError):
    pass


def load_workflow(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text()) or {}
    if not isinstance(data, dict) or "steps" not in data:
        raise WorkflowError(f"{path} needs a steps list")
    return data


def _dig(obj: Any, path: str) -> Any:
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            raise WorkflowError(f"no value at ${path}")
    return cur


def interpolate(value: Any, results: dict[str, Any]) -> Any:
    if isinstance(value, str) and value.startswith("$"):
        return _dig(results, value[1:])
    if isinstance(value, dict):
        return {k: interpolate(v, results) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate(v, results) for v in value]
    return value


def _run_step(root: Path, step: dict[str, Any], results: dict[str, Any]) -> dict[str, Any]:
    if "parallel" in step:
        kids = list(step["parallel"] or [])
        out: dict[str, Any] = {}
        with ThreadPoolExecutor(max_workers=max(1, len(kids))) as pool:
            futs = {
                pool.submit(_run_step, root, child, results): child.get("id") or str(i)
                for i, child in enumerate(kids)
            }
            for fut in as_completed(futs):
                key = futs[fut]
                out[key] = fut.result()
        return out
    name = step.get("tentacle") or step.get("arm")
    action = step.get("action") or "ping"
    if not name:
        raise WorkflowError(f"step {step.get('id')} missing tentacle")
    payload = interpolate(step.get("payload") or {}, results)
    return run_named(root, str(name), str(action), payload, compose=bool(step.get("compose")))


def run_workflow(root: Path, spec: dict[str, Any]) -> dict[str, Any]:
    results: dict[str, Any] = {}
    for i, step in enumerate(spec.get("steps") or []):
        sid = str(step.get("id") or f"step{i}")
        results[sid] = _run_step(root, step, results)
    emit("workflow", {"name": spec.get("name"), "steps": list(results)})
    return {
        "ok": True,
        "name": spec.get("name"),
        "goal": spec.get("goal"),
        "results": results,
    }
