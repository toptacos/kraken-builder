#!/usr/bin/env bash
set -euo pipefail
DIR="$(cd "$(dirname "$0")" && pwd)"
if [ ! -f "$DIR/Hello.class" ]; then
  javac "$DIR/Hello.java"
fi
exec java -cp "$DIR" Hello
