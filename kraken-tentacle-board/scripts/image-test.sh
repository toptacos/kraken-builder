#!/bin/sh
set -eu
echo "image-test: host fallback (no daemon required)"
KRAKEN_OFFLINE=1 python3 tests/test_board.py -v
KRAKEN_OFFLINE=1 python3 tests/e2e_scenarios.py -v
KRAKEN_OFFLINE=1 python3 tests/test_suckers.py -v
