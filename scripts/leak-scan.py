#!/usr/bin/env python3
"""Fail if test logs look like they printed a live secret."""
from __future__ import annotations

import re
import sys
from pathlib import Path

NEEDLES = [
    re.compile(r"sk-[A-Za-z0-9]{8,}"),
    re.compile(r"-----BEGIN .*PRIVATE KEY-----"),
]

def main() -> int:
    roots = [Path(p) for p in (sys.argv[1:] or ["/home/workdir/artifacts"])]
    hits = []
    for root in roots:
        for p in root.rglob("*"):
            if p.suffix not in {".txt", ".jsonl", ".log", ".json"}:
                continue
            if "node_modules" in p.parts:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for rx in NEEDLES:
                if rx.search(text):
                    hits.append(f"{p}: {rx.pattern}")
    if hits:
        print("LEAK")
        print("\n".join(hits[:20]))
        return 1
    print("clean")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
