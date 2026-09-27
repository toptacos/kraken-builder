# Named Kraken instances

One user, many boxes: laptop, Pi, jump host. Each instance is a `KRAKEN_HOME` with its own tentacles and config. Keys never leave the box.

```
kraken instance new laptop --label "Travel"
export KRAKEN_HOME=~/.kraken/instances/laptop
kraken tentacle add examples/tentacles/filesort
kraken instance export laptop --out laptop.kraken.tgz
# on the Pi:
kraken instance import laptop.kraken.tgz --name pi
export KRAKEN_HOME=~/.kraken/instances/pi
kraken license set weather-pro KEY   # keys are local, not in the tarball
```

Export skips `keys/`, `logs/`, `cache/`, `licenses.json`, and `.env`. Mode 0600 on imported yaml/json.

Security: treat the tarball as config, not secrets. Share tentacles and hook priority, not API keys.
