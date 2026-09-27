#!/bin/sh
# Dispatch: compiled watch binary if present, else go run, else python fixture.
# stdin JSON → stdout JSON. Core never imports this.
set -eu
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
OS=$(uname -s | tr 'A-Z' 'a-z')
ARCH=$(uname -m)
case "$ARCH" in
  x86_64|amd64) ARCH=amd64 ;;
  aarch64|arm64) ARCH=arm64 ;;
esac
BIN=""
case "$OS" in
  linux)  BIN="$DIR/dist/watch-linux-$ARCH" ;;
  darwin) BIN="$DIR/dist/watch-darwin-$ARCH" ;;
  msys*|mingw*|cygwin*) BIN="$DIR/dist/watch-windows-$ARCH.exe" ;;
esac
if [ -n "$BIN" ] && [ -f "$BIN" ]; then
  staged="${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}/kraken-watch-${OS}-${ARCH}"
  if [ ! -f "$staged" ] || [ "$BIN" -nt "$staged" ]; then
    cp "$BIN" "$staged"
    chmod +x "$staged" 2>/dev/null || true
  fi
  if [ -x "$staged" ]; then
    exec "$staged"
  fi
  if [ -x "$BIN" ]; then
    exec "$BIN"
  fi
fi
if command -v go >/dev/null 2>&1 && [ -f "$DIR/go.mod" ]; then
  cd "$DIR"
  exec go run ./cmd/watch
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/handler.py"
fi
printf '%s\n' '{"v":1,"ok":false,"error":{"code":"no_runtime","message":"build dist/ with ./build.sh or install go/python3"}}'
exit 0
