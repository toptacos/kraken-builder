# Security review (device CLI + tentacles)

Honest pass against the code that exists, not a marketing list.

## What is actually isolated

- Core does not import tentacle source. A bad plugin cannot monkey-patch `license.py` unless you install it as an **in-process arm**.
- Free tentacles never call `api.topta.co`.
- Hook invokes use `_invoke_one` and `_IN_HOOK`, so a hook cannot hook itself into a loop.
- Store packs check `sha256` on import.
- Vault ciphertext is not the passphrase.

## What is not isolated

| Issue | Where | Risk | What to do |
|---|---|---|---|
| `tentacle add` from git runs whatever binary the repo names | `tentacle.py` | Supply chain. Same as `curl \| sh`. | Only add URLs you trust. Later: signed manifests + checksum in catalog. |
| `hotreload` runs `command` from the payload | `hotreload/handler.py` | Local RCE by whoever can `kraken run` | Treat tick as your own shell. Do not expose the CLI to untrusted HTTP. |
| `docker-env up` shells out to `docker compose` | `docker-env/handler.py` | Starts containers you listed | Review the service list. Dry-run when Docker is missing is safe. |
| OpenSSL `-pass pass:` on the argv | `vault/handler.py` | Passphrase visible in `ps` | Prefer `KRAKEN_VAULT_PASS` + env, or a file descriptor. Do not log it. |
| XOR+HMAC fallback if openssl missing | `vault/handler.py` | Not production crypto | Require openssl in real use. Tests only. |
| `licenses.json` is plaintext | `~/.kraken/keys/` | Disk theft = keys | File mode 0600; later: OS keychain. |
| `KRAKEN_LICENSE_OFFLINE=1` | `license.py` | Skips remote revoke | Fine for air-gap. Do not ship that on in a SaaS wrapper. |
| S3 backend is a folder mirror | `store/handler.py` | Not AWS IAM | Real S3 needs signed requests + bucket policy. Mirror is for tests and LAN. |
| `after_install` hooks are not fired | `hooks.py` vs `tentacle.py` | Dead event | Do not rely on it for audit until wired. |
| No sandbox | invoke | A tentacle has your user account | That is the product. Do not run untrusted arms. |

## Rules for authors

1. Never print secrets, passphrases, or raw license keys in `result`.
2. Never fetch and eval remote code inside a handler.
3. If you shell out, take an allow-list of binaries (`docker`, `openssl`), not a free-form string from the network.
4. Premium arms still must work offline after `license set` + `KRAKEN_LICENSE_OFFLINE=1` for air-gapped users — but revoke only works when remote verify is on.
5. Packs and bundles are bearer files. Treat `kraken.pack.json` like a tarball of secrets.

## Rules for operators

- `chmod 700 ~/.kraken` and `chmod 600 ~/.kraken/keys/licenses.json`.
- Do not run `kraken` as root.
- Pin git refs when you add (`git clone --depth 1` today tracks default branch — pin a tag in the catalog row).
- Hooks in project `.kraken/config.yaml` run other binaries. Review them like cron.

## What we will not do

- Put a license dongle in core so a school image has to call home.
- Pretend the XOR fallback is AES.
- List an unsigned mystery binary on kraken.topta.co without a source URL.
