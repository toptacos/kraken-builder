# Optional Docker network

Core does not start Docker. `kraken demo` does not need a network.

The named bridge `kraken_<env>` exists only when you ask for it:

1. Payload: `kraken run docker-env plan --payload '{"name":"dev"}'`
2. Env: `KRAKEN_DOCKER_NETWORK=lab` → `kraken_lab`
3. Config: `~/.kraken/config.yaml`

```yaml
docker:
  enabled: true
  name: kraken_dev
  public: false
  isolated: false
```

4. Third party: `KRAKEN_DOCKER_CONFIG_URL=https://example.com/kraken-net.json`

```json
{"enabled": true, "name": "kraken_ci", "isolated": true, "public": false}
```

YAML at a `.yml` URL is accepted. Fetch errors are recorded as `fetch_error`; the CLI does not invent a public bind.

## Defaults

- Off (`enabled: false`)
- Name `kraken_dev` when enabled
- Publish `127.0.0.1` unless `public: true`
- `isolated: true` sets Compose `internal: true`
- `runtime` refuses `--network` names that do not start with `kraken_`
- No Docker: `plan` / `build` / `invoke` return `mode: dry-run` and the argv

## Trust

Whoever can talk to the Docker socket is inside the boundary. This is not a multi-tenant fabric. See `docs/NETWORK.md`.
