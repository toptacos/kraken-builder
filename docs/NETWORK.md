# Kraken network security

There is no Kraken VPN, mesh, or mTLS fabric. Three things get called a “network”:

1. Docker network `kraken_<env>` from `docker-env`
2. Bind mounts + env that `runtime` calls “shared services”
3. Outbound HTTPS from core (`api.topta.co`, notify webhook)

## 1. Docker network `kraken_dev`

`docker-env` writes a compose file with:

- a user-defined bridge named `kraken_<env>`
- every listed service on that bridge
- **published ports** as given (`6379:6379` in the default redis example)

`runtime` then does `docker run --network kraken_dev`.

Implications:

- Containers on the same bridge can reach each other on container ports with **no auth** unless the service itself requires it.
- Published ports listen on the **host** (Compose default is `0.0.0.0`). That is LAN-visible, not “Kraken-only.”
- `share.json` prints `docker network connect kraken_dev <container>`. Anyone who can talk to that Docker socket can join.
- The network is not encrypted. Same-host bridge traffic is plain Ethernet inside the namespace.
- No network policy, no per-tentacle identity, no DNS allow-list.

Default redis example publishing `6379:6379` is a foot-gun on a shared machine.

## 2. Shared “services” are mounts, not a secure bus

`runtime` mounts:

| Mount | Mode | Risk |
|---|---|---|
| `work` → `/work` | read-write | Container can rewrite the project |
| `~/.kraken/data` → `/kraken/data` | **read-write** | Container can read/write store + vault files |
| SSH key → `/kraken/ssh/key` | read-only | Key still usable from inside the container |
| extra `mounts[]` | as given | Caller-controlled; can mount `$HOME` |

There is no:

- read-only data mount option in the handler today
- drop of Linux capabilities
- user namespace remapping
- seccomp/AppArmor profile
- image digest pin (`image: tag` only)

A Dockerfile you did not review, joined to `kraken_dev` with `/kraken/data` RW, can exfiltrate packs and vault ciphertext and talk to redis on the bridge.

`publish` only **names** an upload URI. It does not encrypt or check the destination. `store` S3 is a folder mirror unless you add real IAM later.

## 3. Outbound from core

| Call | When | Auth |
|---|---|---|
| `POST api.topta.co/api/kraken/licenses/*` | premium + remote verify / issue | license key in JSON body |
| `POST $KRAKEN_NOTIFY_WEBHOOK` | every `emit` | none |
| `git clone` on `tentacle add` | install | HTTPS or `git@` as the URL says |

Notify webhook is an unauthenticated POST of run metadata. Do not point it at a URL you do not trust. License traffic is HTTPS; the key still sits in `~/.kraken/keys/licenses.json` mode 0600.

Core does **not** open a listen port. `kraken serve-site` prints `python3 -m http.server` for the marketing folder. That is not the control plane.

## Trust boundary (honest)

```
you (unix user)
  └─ kraken CLI          no listen port
       ├─ tentacle binary    same user, no sandbox
       ├─ docker-env         Docker socket = root-equivalent
       └─ runtime            container + bridge + data RW
            ├─ other containers on kraken_dev
            └─ published host ports
```

Whoever can `kraken run` or use the Docker socket is inside the boundary. There is no second tenant.

## What to do before this is “a network product”

1. Default compose: **no host ports**. Publish only when `ports` is explicit and prefer `127.0.0.1:6379:6379`.
2. `runtime`: mount `/kraken/data` **read-only** unless `services.data.write: true`.
3. Pin images by digest; refuse `latest`.
4. `--network kraken_dev` only if that network exists and is labeled `kraken.tentacle=docker-env`.
5. Do not mount SSH keys unless `invoke` needs them; pass a one-shot agent socket later.
6. Treat store packs and vault bundles as bearer secrets on the wire.
7. Do not expose `kraken` over HTTP. Hooks and hotreload are local shell.

Until those land, “Kraken network” means **a named Docker bridge plus mounts**. Useful for a single operator. Not a multi-user fabric.

## Implemented defaults

- docker-env binds 127.0.0.1 unless public: true
- runtime data :ro, kraken_* network only, no-new-privileges, SSH opt-in
- vault openssl env:KRAKEN_V, dir 0700
