#!/bin/sh
set -eu
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if command -v node >/dev/null 2>&1; then
  exec node "$DIR/handler.js"
fi
printf '%s\n' '{"v":1,"ok":false,"error":{"code":"no_runtime","message":"node not installed"}}'
exit 0
