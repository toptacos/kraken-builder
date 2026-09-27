# Grants (default deny)

```
kraken grant scourge
kraken grant remote_config
kraken grant tunnel
kraken grant llm
kraken grant expose
kraken grant scourge --revoke
```

Writes `allow:` into `~/.kraken/config.yaml` (0600). Project `.kraken/config.yaml` can set the same keys; cwd wins on merge. Wiki: this page + `docs/SCOURGE.md`.
