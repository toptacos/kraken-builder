# Tutorial — four tentacles with Nyx

Voice: `website/media/voice/tutorial-dev.mp3` and `tutorial-secure.mp3`.
Page: `website/tutorial-tentacles.html`.

## 1. docker-env

Compose from a service list. If Docker is missing, `up` still writes the YAML and returns `mode: dry-run`.

```bash
kraken tentacle add examples/tentacles/docker-env
kraken run docker-env plan --payload '{"name":"dev","services":[{"name":"redis","image":"redis:7-alpine","ports":["6379:6379"]}]}'
kraken run docker-env up --payload '{"name":"dev","services":[{"name":"redis","image":"redis:7-alpine","ports":["6379:6379"]}]}'
kraken run docker-env share --payload '{"name":"dev","services":[{"name":"redis","image":"redis:7-alpine","ports":["6379:6379"]}]}'
```

`share` writes `share.json`: network name, published ports, join command. Another machine on the same Docker network can attach.

## 2. hotreload

```bash
kraken tentacle add examples/tentacles/hotreload
kraken run hotreload watch --payload '{"name":"demo","root":"./app","patterns":["*.py"],"command":["pytest","-q"]}'
kraken run hotreload tick --payload '{"name":"demo"}'
```

`tick` hashes the tree. On change it runs the command. Call tick from a loop or a git hook. No daemon required.

Dev loop workflow: `examples/workflows/dev-loop.yaml`.

## 3. vault

```bash
kraken tentacle add examples/tentacles/vault
kraken run vault init --payload '{}'
kraken run vault put --payload '{"name":"deploy-token","value":"..."}'
kraken run vault get --payload '{"name":"deploy-token"}'
kraken run vault export-bundle --payload '{}'
```

AES-256-CBC via openssl + PBKDF2. If openssl is missing, an HMAC-wrapped fallback is used so tests still run. Passphrase: payload `passphrase` or `KRAKEN_VAULT_PASS`.

## 4. store

Content-addressed blobs (`sha256`). Backends: `local`, `s3` (directory mirror under `.kraken/data/store/s3/<bucket>` until real AWS creds exist), `export-pack` / `import-pack` for another Kraken home.

```bash
kraken tentacle add examples/tentacles/store
kraken run store put --payload '{"name":"token.enc","path":"/path/to/file","backend":"s3","bucket":"kraken-local"}'
kraken run store export-pack --payload '{}'
# on the other box
kraken run store import-pack --payload '{"pack":"/path/kraken.pack.json"}'
```

Duplicate puts of the same bytes skip the write.

## Workflow that ties vault + store

`examples/workflows/secure-share.yaml`

```bash
kraken workflow run examples/workflows/secure-share.yaml
```

Encrypts `deploy-token`, stashes the ciphertext by hash, writes a pack the next install can import.
