# The `.kraken` directory

Created on first run of `kraken init`.

```
~/.kraken/
  config.yaml
  data/
  logs/
  tentacles/
    echo-bin/
      tentacle.yaml
      bin/
  cache/
  keys/
```

Project overlay:

```
~/src/race-ops/.kraken/
  config.yaml          # overrides notify, tentacle paths, env
  data/                # project-scoped state
```

Merge rule: deep-merge maps, replace lists and scalars. Order: system → user → parent projects → cwd.

`KRAKEN_HOME` relocates the user root (tests use this).
`KRAKEN_SYSTEM_DIR` relocates the system root.
