# CLI

```text
kraken init [--home DIR]
kraken vanilla
kraken demo [--ip 1.1.1.1]
kraken doctor
kraken self plan
kraken list
kraken run NAME ACTION [--payload JSON]
kraken queue NAME ACTION
kraken tentacle add PATH
kraken tentacle list
kraken grant NAME [--revoke]
kraken license set NAME KEY
kraken license status
kraken license verify NAME
kraken serve-site
```

`bin/kraken` is the console entry. If the shebang cannot exec, use `python3 bin/kraken`.

Environment:

| Variable | Meaning |
|---|---|
| `KRAKEN_HOME` | Relocate user `.kraken` |
| `KRAKEN_API_BASE` | License API (default https://api.topta.co) |
| `KRAKEN_LICENSE_OFFLINE=1` | Trust stored key, no HTTP |
| `KRAKEN_LICENSE_REMOTE=1` | Verify on every premium run |
