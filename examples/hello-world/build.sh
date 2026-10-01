#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
ok() { echo "built $1"; }

if command -v gcc >/dev/null; then
  gcc -O2 -o "$ROOT/c/hello" "$ROOT/c/handler.c" && ok c
fi
if command -v g++ >/dev/null; then
  g++ -O2 -o "$ROOT/cpp/hello" "$ROOT/cpp/handler.cpp" && ok cpp
fi
if command -v rustc >/dev/null; then
  rustc -O -o "$ROOT/rust/hello" "$ROOT/rust/handler.rs" && ok rust
fi
if command -v go >/dev/null; then
  (cd "$ROOT/go" && go build -o hello handler.go) && ok go
fi
if command -v javac >/dev/null; then
  javac "$ROOT/java/Hello.java" && ok java
fi
chmod +x "$ROOT"/*/hello 2>/dev/null || true
echo "scripts need no build: python bash js php ruby perl"
