"""Arm manifest schema. Arms only need arm.yaml plus an entrypoint."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


REQUIRED_KEYS = ("name", "version", "entrypoint")


@dataclass
class ArmManifest:
    name: str
    version: str
    entrypoint: str
    description: str = ""
    triggers: list[str] = field(default_factory=list)
    actions: list[str] = field(default_factory=list)
    path: str = ""
    raw: dict[str, Any] = field(default_factory=dict)

    def invoke(self, action: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if action not in self.actions and self.actions:
            raise PermissionError(f"arm {self.name} does not expose action {action}")
        module_path, _, attr = self.entrypoint.partition(":")
        if not attr:
            attr = "handle"
        import importlib

        mod = importlib.import_module(module_path)
        handler = getattr(mod, attr)
        return handler(action=action, payload=payload or {}, manifest=self)
