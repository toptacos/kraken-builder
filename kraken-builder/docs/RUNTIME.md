# Custom compilers and shared services

Core does not ship gcc, rustc, or a language pack. A tentacle that needs a toolchain brings a **Dockerfile** and a **services.yaml**. `runtime` turns a JSON request into `docker run`, with mounts for shared Kraken services.

```
request JSON
    → runtime plan | build | invoke | publish
    → container on network kraken_dev
    → stdout JSON
    → store / s3 / ssh / upload URI
```

## What you add

```
my-arm/
  tentacle.yaml
  handler.c          # or any language
  Dockerfile         # your compiler
  services.yaml      # shared paths only
```

```yaml
# services.yaml
store: { backend: local, path: ~/.kraken/data/store }
s3:    { uri: "" }
ssh:   { key: "" }
upload: { uri: local://store }
network: kraken_dev
dockerfile: Dockerfile
image: kraken-hello-c:local
```

```bash
kraken tentacle add examples/tentacles/runtime
kraken run runtime plan --payload '{"dockerfile":"examples/tentacles/hello-world/c/Dockerfile","image":"kraken-hello-c:local"}'
kraken run runtime build --payload '{"dockerfile":"examples/tentacles/hello-world/c/Dockerfile","image":"kraken-hello-c:local"}'
kraken run runtime invoke --payload '{"image":"kraken-hello-c:local","inner":{"name":"kraken"}}'
kraken run runtime publish --payload '{"services":{"upload":{"uri":"s3://bucket/out"}}}'
```

No Docker: `build` and `invoke` return `mode: dry-run` and the argv. That is enough for CI.

## Shared services (lean)

| Name | Meaning | Mount / env |
|---|---|---|
| data | `~/.kraken/data` | `/kraken/data` |
| store | content-addressed results | `KRAKEN_STORE` |
| vault | encrypted secrets | path in services.yaml |
| s3 | remote prefix | `s3://…` when creds exist |
| ssh | deploy key | `/kraken/ssh/key:ro` |
| upload | where to put the result | `KRAKEN_UPLOAD` |
| network | docker network from `docker-env share` | `--network kraken_dev` |

Advanced packages (GPU builders, remote builders, cache volumes) are **more tentacles**, not core flags. They read the same services.yaml.

## Room to grow without fattening core

- Extra mounts: `payload.mounts: [{src, dest}]`
- Extra env: set in the image, not in core
- Result hand-off: `runtime publish` then `store put` / `store export-pack`
- Other compilers: copy `hello-world/c/Dockerfile` and change the `RUN` line
