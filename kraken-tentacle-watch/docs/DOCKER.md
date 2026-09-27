# Minimum image and CI

Alpine + CPython + Kraken core + this tentacle. No Go toolchain in the runtime image. No Docker-in-Docker. Tests are default-deny / offline (`KRAKEN_OFFLINE=1`).

## What the image contains

| Layer | Package | Why |
|---|---|---|
| `alpine:3.20` | base | Smallest supported OS |
| `python3` `py3-yaml` | Kraken core runtime | `install.sh` needs these two |
| `git` | clone / `tentacle add` from git | Official installer |
| `bash` `ca-certificates` | scripts + TLS | `contrib/kraken-watch.sh`, HTTPS |
| `/opt/kraken-builder` | MIT core | `python3 -m kraken` |
| `/usr/local/bin/kraken` | wrapper | Same shape as `kraken.topta.co/install.sh` |
| `/opt/watch` | this tentacle + suckers | `handler.sh` → `dist/watch-linux-*` |
| `/opt/watch/examples/tentacles/watch-stamp` | sucker tentacle | `after_run` convert + `patch` |

Builder stage (`golang:1.22-alpine`) is discarded. Runtime has one static `watch` binary.

## Build and run

```bash
docker build -t kraken-watch:local .
docker images kraken-watch:local
docker run --rm --network=none -e KRAKEN_OFFLINE=1 -e KRAKEN_NOTIFY_STDOUT=1 kraken-watch:local
```

Default `CMD` is `scripts/image-test.sh` (verbose). `--network=none` proves the suite does not need the control plane.

## GitHub Action

`.github/workflows/ci.yml` has two jobs:

1. **host** — Ubuntu runner, `setup-go` + `setup-python`, `./build.sh`, `tests/test_watch.py -v`, then `scripts/ci-test.sh` which clones `kraken-builder`, writes a `kraken` wrapper, installs the tentacle + sucker, and runs the same image script.
2. **image** — `docker build`, print size, `docker run --network=none`, ping the compiled binary.

## Suckers wired in the image

`docker/config.yaml` is copied to `$KRAKEN_HOME/.kraken/config.yaml`:

```yaml
hooks:
  after_run:
    - tentacle: watch-stamp    # suckers/after-watch.yaml
      action: convert
      optional: true
      priority: 10
      if: ok
      when: ["watch"]
    - tentacle: echo-bin       # suckers/watch-log.yaml (vanilla arm)
      action: ping
      optional: true
      priority: 30
      when: ["watch"]
```

`watch` also declares `watch-stamp` + `save-text` on its own `tentacle.yaml`. `save-text` stays optional so a missing binary never fails CI.

`watch-stamp convert` returns `{result: {patch: {sucker, stamped_at, …}}}`. Because `watch` lists a `finish` action, core merges the patch after `after_run`.

## Host-only (no daemon)

```bash
bash scripts/ci-test.sh
```

Uses `$PWD/.ci-home` for `KRAKEN_HOME` / source clone so it does not touch your real `~/.kraken`.

The image `CMD` now runs contract + sucker + e2e scenarios + `ci` integration. `--network=none` is required in CI so a clone of `kraken-builder` must happen **at image build** (already in the Dockerfile). Do not rely on runtime `git clone`.
