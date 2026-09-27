#!/bin/sh
set -eu
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if command -v python3 >/dev/null 2>&1; then
  exec python3 "$DIR/handler.py"
fi
printf '%s\n' '{"v":1,"ok":false,"error":{"code":"no_runtime","message":"python3 required"}}'
exit 0
