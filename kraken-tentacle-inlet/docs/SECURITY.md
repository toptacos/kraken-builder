# Security

- Bind is `127.0.0.1` only. `0.0.0.0` is forbidden.
- No `shell` action. Unknown actions include `shell`.
- Tunnel refused until at least one device is granted.
- Tunnel binary is optional; missing `cloudflared` returns `need_bin`. Kraken does not keep a daemon — print the command.
- `api.topta.co` is not used as a control plane. Local roster only.
- `finish` drops `token`.
- Jail: keys / licenses / catalog paths.
