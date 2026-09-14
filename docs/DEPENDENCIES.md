# Tentacle dependency graph

Declare-only. Core does not download or invoke dependencies. It refuses to `run` if the graph is invalid.

## Manifest

```yaml
requires:
  protocol: 1
  core: ">=0.1.0"
  tentacles:
    geo: ">=0.1.0 <0.3.0"
    notify: optional
```

Ranges: exact, `*`, `>=` `>` `<=` `<`, `^1.2.0` (same major), `~1.2.0` (same minor), space-AND.

One installed version per name. In-process names win.

## Commands

```bash
python3 bin/kraken tentacle plan weather-pro
python3 bin/kraken tentacle add examples/tentacles/geo
python3 bin/kraken tentacle add examples/tentacles/weather-pro
```

`tentacle add` copies first, then resolves. Missing required deps → exit 2 (files stay installed).

## Errors

- missing required tentacle
- installed version outside range
- cycle
- protocol newer than core
- core version outside `requires.core`

## Cycle detection

`resolve()` DFS-colors the `requires.tentacles` graph. A node already on the current walk raises:

```text
ResolveError: dependency cycle: loop-a -> loop-b -> loop-a
```

One version per name, so this is not a SAT problem. Hook cycles are a different mechanism (`_IN_HOOK` in the runner) — see `docs/HOOKS.md`.
