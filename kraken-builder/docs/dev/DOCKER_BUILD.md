# Docker build

Slice 1 image:

```bash
docker build -t kraken .
docker run --rm kraken list
docker run --rm kraken run echo ping
```

Later (not implemented): multi-stage build that emits linux/amd64 and linux/arm64 binaries via PyInstaller or a tiny Go launcher that shells to Python. Signing keys stay out of git.
