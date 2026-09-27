#!/bin/sh
set -eu
DIR=$(CDPATH= cd -- "$(dirname "$0")" && pwd)
if command -v php >/dev/null 2>&1; then
  exec php "$DIR/handler.php"
fi
printf '%s\n' '{"v":1,"ok":false,"error":{"code":"no_runtime","message":"php not installed"}}'
exit 0
