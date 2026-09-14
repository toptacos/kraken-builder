# Plugin architecture — both kinds

Kraken has two plugin types. They share a name and an action list. They do not share a process.

## 1. In-process arm

- Manifest: `arms/<name>/arm.yaml`
- Required keys: `name`, `version`, `entrypoint`
- Entrypoint: `module.path:function` imported by `ArmManifest.invoke`
- Signature: `handle(action, payload, manifest) -> dict`
- Discovery: `load_arms([root / "arms"])`
- Reload: process restart (slice 1 does not hot-reload core)
- Use for: fixtures shipped with the runner (`echo`, `monitor`, `pi-host`)

```yaml
name: echo
version: "0.1.0"
entrypoint: arms.echo.handler:handle
actions: [ping, echo]
```

## 2. External tentacle

- Manifest: `tentacle.yaml` + a binary or script
- Contract: JSON on stdin / JSON on stdout (`docs/CONTRACT.md`)
- Discovery: `~/.kraken/tentacles/*/tentacle.yaml` and config `tentacles:`
- Install: `kraken tentacle add <dir|git>`
- Reload: not required; scanned on each `run`
- Use for: everything else (`geo`, `docker-env`, `hotreload`, `vault`, `store`, `weather-pro`)

```yaml
name: docker-env
version: "0.1.0"
runtime: binary
binary: handler.py
actions: [plan, up, status, share, down]
```

## Resolve order

`kraken run NAME ACTION`

1. In-process registry (`arms/`)
2. Project / user config `tentacles:`
3. `~/.kraken/tentacles/<name>/`

First hit wins. `kraken list` prints `kind` as `in-process` or `binary`.

## Shared layers (both kinds)

Same pipeline after the name is resolved:

```
resolve (deps, semver, cycles)
 → license (premium only)
 → hook before_run
 → invoke
 → hook after_run | on_error
 → notify
```

`--compose` runs declared tentacle deps first and injects `_deps`.
Workflows and the queue call `run_named`, so they work for both kinds.

## What stays out of a plugin

Core owns config merge, licenses, hooks, notify, and the CLI.
A tentacle must not import `kraken.core`. An arm may, because it lives in the same tree — keep it thin anyway.

## When to pick which

| You are… | Pick |
|---|---|
| Shipping a fixture with the binary | arm |
| Publishing a tool in its own repo | tentacle |
| Need Docker / files / S3 / another language | tentacle |
| Need to patch core tests quickly | arm |

The four tutorial tools are tentacles on purpose: they must move between machines without rebuilding core.

To ship one for other people: `docs/PUBLISHING.md`. Security bar: `docs/SECURITY.md`.
