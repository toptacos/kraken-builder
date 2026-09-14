"""Tiny version compare. No packaging dependency."""

from __future__ import annotations

import re


def parse_version(raw: str) -> tuple[int, int, int]:
    text = (raw or "0.0.0").strip()
    text = text.split("+", 1)[0].split("-", 1)[0]
    parts = re.findall(r"\d+", text)
    nums = [int(p) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return nums[0], nums[1], nums[2]


def cmp_version(a: str, b: str) -> int:
    left, right = parse_version(a), parse_version(b)
    return (left > right) - (left < right)


def _match_token(installed: str, token: str) -> bool:
    token = token.strip()
    if not token or token in {"*", "any"}:
        return True
    if token == "optional":
        return True
    if token.startswith("^"):
        base = token[1:].strip()
        major, minor, patch = parse_version(base)
        if cmp_version(installed, base) < 0:
            return False
        ceiling = f"{major + 1}.0.0"
        return cmp_version(installed, ceiling) < 0
    if token.startswith("~"):
        base = token[1:].strip()
        major, minor, patch = parse_version(base)
        if cmp_version(installed, base) < 0:
            return False
        ceiling = f"{major}.{minor + 1}.0"
        return cmp_version(installed, ceiling) < 0
    for op in (">=", "<=", ">", "<", "==", "="):
        if token.startswith(op):
            bound = token[len(op) :].strip()
            c = cmp_version(installed, bound)
            if op == ">=":
                return c >= 0
            if op == "<=":
                return c <= 0
            if op == ">":
                return c > 0
            if op == "<":
                return c < 0
            return c == 0
    return cmp_version(installed, token) == 0


def satisfies(installed: str, spec: str | None) -> bool:
    if spec is None or str(spec).strip() in {"", "*", "any", "optional"}:
        return True
    return all(_match_token(installed, part) for part in str(spec).split() if part)
