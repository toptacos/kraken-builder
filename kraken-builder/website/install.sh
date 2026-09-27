#!/bin/sh
# Kraken installer — copies nothing privileged. Prints the local commands.
set -eu
echo "Kraken is a local CLI. Clone then:"
echo "  export PYTHONPATH=\$PWD"
echo "  python3 -m kraken init"
echo "  python3 -m kraken vanilla"
echo "Docs: https://kraken.topta.co/docs.html"
