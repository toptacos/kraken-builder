# Docker

```bash
docker build -t kraken-board:dev .
docker run --rm -e KRAKEN_OFFLINE=1 kraken-board:dev
```

Alpine + Python 3.12 + git. No Go cross-compile step: this arm is the Python handler (same pattern as official `jev-ai`).
