# Tentacles (plugins)

Pair with in-process arms: `docs/PLUGINS.md`. Same `kraken run NAME ACTION`. Different process.

A tentacle is a folder with `tentacle.yaml` and a binary (or script) that speaks JSON on stdin/stdout.

## In-process vs binary

| Kind | Location | Used for |
|---|---|---|
| in-process | `arms/*/arm.yaml` | Core fixtures (`echo`, `pi-host`) |
| binary | `.kraken` config or `~/.kraken/tentacles/<name>/` | Real plugins |

`kraken run NAME ACTION` tries in-process, then config `tentacles:`, then installed tentacles.

## Install from a local folder

```bash
python3 bin/kraken tentacle add examples/tentacles/weather-pro
python3 bin/kraken tentacle list
python3 bin/kraken license set weather-pro YOUR_KEY
KRAKEN_LICENSE_OFFLINE=1 python3 bin/kraken run weather-pro forecast --payload '{"zip":"27284"}'
```

`tentacle add` copies the folder to `~/.kraken/tentacles/<name>/`.

## Install from git, pinned to a version

```bash
python3 bin/kraken tentacle add github.com/toptacos/kraken-tentacle-facts
python3 bin/kraken tentacle add github.com/toptacos/kraken-tentacle-facts@v0.1.0
```

`@tag` is a release the way `image:tag` is one: core clones that tag and
refuses when the manifest inside disagrees with it. Offline mirrors work
the same (`file:///srv/mirror@v1.2.3`).

## Manifest

See `examples/tentacles/weather-pro/tentacle.yaml` and `docs/CONTRACT.md`.

Set `license: premium` to require a key. Free tentacles never call the network.

Declare the versions your handler needs and core refuses before spawning it:

```yaml
requires:
  python: ">=3.11"    # or node, bash, php, ruby, perl, go, rustc, docker, git
  core: ">=0.4.0"
```

Undeclared means unprobed: a manifest that asks for nothing spawns nothing.


## Dev and share arms

`docker-env`, `hotreload`, `vault`, `store` — docs/TUTORIAL_TENTACLES.md and website/tutorial-tentacles.html.
