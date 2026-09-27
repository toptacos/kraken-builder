# User namespaces and Kraken

Kraken does not enable user namespaces. That is a **Docker daemon / host** choice.

## Modes

- Rootless Docker: `dockerd` and containers run as you. Container UID 0 maps to your host UID.
- `userns-remap` in `/etc/docker/daemon.json`: daemon stays root; container UID 0 maps to `dockremap` + `/etc/subuid`.

Need `newuidmap`, `newgidmap`, and ≥65536 IDs in `/etc/subuid` and `/etc/subgid`.

## Why tentacles do not pass `--userns`

- `--userns=host` *disables* remapping for that container.
- Bind mounts (`work`, `~/.kraken/data`) break unless host paths are owned by the remapped UID.
- Compose + remap historically fails on builds and volume chown.

Prefer: run rootless Docker as the same user as `kraken`. Keep Kraken flags: `127.0.0.1` publish, `kraken_*` networks, data `:ro`, `no-new-privileges`.

## Check

```
grep "^$USER:" /etc/subuid /etc/subgid
docker info 2>/dev/null | grep -iE 'rootless|userns'
```
