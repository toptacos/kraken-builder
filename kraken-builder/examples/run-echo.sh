#!/bin/sh
set -e
cd "$(dirname "$0")/.."
PYTHONPATH=. python3 -m kraken.core.cli --root . run echo echo --payload '{"hello":"kraken"}'
